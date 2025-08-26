from __future__ import annotations

from contextlib import contextmanager
import functools
import io
import logging
from collections.abc import Callable, Iterator
import sys
import textwrap
from typing import List, Protocol, TypeVar, Union

import backoff
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import qai_hub

# Will sleep {backoff factor} * (2 ** ({number of previous retries})) seconds
BACKOFF_FACTOR = 0.75
# Try 6 times total, for a max total delay of about 20s
MAX_RETRIES = 5
# The maximum length of any single wait (this is here mainly for testing)
MAX_WAIT = 10

# How long to wait before timing out a connection attempt.
# Due to a bug in urllib3/requests (https://github.com/psf/requests/issues/5263),
# the "connect timeout" actually spans the whole process of connecting
# to the socket and sending the HTTP request (or the first chunk of
# the request, when using chunked encoding).
REQUEST_TIMEOUT_SECONDS = 3.05

# Due to the aforementioned bug in urllib3, we want to chunk the
# request if it is large, otherwise it will time out prematurely
MAX_UNCHUNKED_REQUEST_SIZE = BYTES_PER_MIB = 1024.0 * 1024.0

# How long to wait for response data before timing out a connected
# socket. (It's the number of seconds that the client will wait
# between bytes sent from the server. In 99.9% of cases, this is
# the time before the server sends the first byte).
# By default, requests waits forever.
# https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
EXTERNAL_RESPONSE_TIMEOUT_SECONDS = 4

# Our webserver is configured to time out connections after 26 seconds,
# so we specify a slightly higher max timeout.
AIHUB_RESPONSE_TIMEOUT_SECONDS = 28

RETRIABLE_STATUSES = [
    429,  # Too many requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
]


# Matches the response objects from both "requests" and "httpx"
class GenericHTTPResponse(Protocol):
    @property
    def status_code(self) -> int: ...


def is_retriable_status(response: GenericHTTPResponse):
    return response.status_code in RETRIABLE_STATUSES


HTTPResponseLike = TypeVar("HTTPResponseLike", bound=GenericHTTPResponse)


def retry_with_backoff(
    additional_exceptions_to_retry: List[type[Exception]] = [],
) -> Callable[[Callable[..., HTTPResponseLike]], Callable[..., HTTPResponseLike]]:
    """
    Decorator for retrying functions that need to set up state as well as make an HTTP call.
    Assumes the function will return a response object with a `status_code` attribute,
    and may raise connect and timeout exceptions from the `requests` library or the additional
    exception types provided.

    The user of this decorator is responsible for making sure the call is safe to retry.
    """

    def wrapper(
        func: Callable[..., HTTPResponseLike],
    ) -> Callable[..., HTTPResponseLike]:
        @backoff.on_exception(
            wait_gen=backoff.expo,
            exception=(
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ContentDecodingError,
            )
            + tuple(additional_exceptions_to_retry),
            max_tries=1 + MAX_RETRIES,
            factor=BACKOFF_FACTOR,
            max_value=MAX_WAIT,
        )
        @backoff.on_predicate(
            wait_gen=backoff.expo,
            max_tries=1 + MAX_RETRIES,
            predicate=is_retriable_status,
            factor=BACKOFF_FACTOR,
            max_value=MAX_WAIT,
        )
        @functools.wraps(func)
        def inner(*args, **kwargs) -> HTTPResponseLike:
            return func(*args, **kwargs)

        return inner

    return wrapper


def retry_call_with_backoff(func: Callable[[], HTTPResponseLike]) -> HTTPResponseLike:
    """
    Retry a single call to a no-arg function, as in @retry_with_backoff.
    """

    @retry_with_backoff()
    def call() -> HTTPResponseLike:
        return func()

    return call()


class LogRetry(Retry):
    """
    Adding extra logs before making a retry request
    """

    def increment(self, *args, **kwargs):
        retry_object = super().increment(*args, **kwargs)

        # TODO: sanitize this URL instead of truncating it (#13103)
        url_log = f" for {kwargs['url'][:300]}" if kwargs.get("url") else ""
        error_log = f"; error was {kwargs['error']}" if kwargs.get("error") else ""

        # Total is the number of retries remaining. Starts at MAX_RETRIES and counts down to zero.
        if isinstance(self.total, int) and self.total < MAX_RETRIES:
            logger = logging.getLogger("LogRetry")
            logger.info(
                f"Retry attempt number {MAX_RETRIES - self.total}{url_log}{error_log}"
            )

        return retry_object


class SessionWithRetryAndTimeout(requests.Session):
    def __init__(self, *args, response_timeout_seconds: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_timeout_seconds = response_timeout_seconds

    def request(
        self, method, url, params=None, data=None, *args, **kwargs
    ) -> requests.Response:
        with self._stream_if_oversized(data) as data_stream:
            default_kwargs = {
                "timeout": (REQUEST_TIMEOUT_SECONDS, self.response_timeout_seconds),
                "data": data_stream if data_stream else data,
            }
            return super().request(
                method, url, params, *args, **{**default_kwargs, **kwargs}
            )

    @contextmanager
    def _stream_if_oversized(self, data) -> Iterator[io.IOBase | None]:
        # workaround for https://github.com/psf/requests/issues/5263; it's also best practice
        # not to load large files into memory if all you're doing is streaming them
        data_stream: io.IOBase | None = None
        try:
            if (
                isinstance(data, (str, bytes))
                and sys.getsizeof(data) > MAX_UNCHUNKED_REQUEST_SIZE
            ):
                logging.warning(
                    textwrap.dedent(f"""
                            UploadFromMemoryWarning:
                            A {(sys.getsizeof(data) / BYTES_PER_MIB):.2f} MiB data buffer is being PUT or POSTed from memory.
                            If the data originated in a file, you should stream it from disk rather than buffering in memory:
                                with open(file_path, "rb") as file_stream:
                            If the data originated in memory, suppress this warning by wrapping it in an IO stream:
                                with io.BytesIO(data_bytes) as data_stream:  # or StringIO, for string data
                        """)
                )
                if isinstance(data, bytes):
                    data_stream = io.BytesIO(data)
                else:
                    data_stream = io.StringIO(data)
            yield data_stream
        finally:
            if data_stream:
                data_stream.close()


def create_session(
    internal_retries: bool = True,
    response_timeout_seconds: int = AIHUB_RESPONSE_TIMEOUT_SECONDS,
) -> SessionWithRetryAndTimeout:
    """
    Get a requests.Session object pre-configured to time out all requests, and
    (if `internal_retries` is True, which is the default) do safe retries.

    "Safe to retry" includes failure to connect with any HTTP method, or a retriable
    HTTP status or read timeout from an idempotent HTTP method (GET, PUT, DELETE, HEAD, OPTIONS).

    Only read errors in the initial connection and header exchange will be retried. Any read errors
    encountered while consuming the response body are not retried, even with a non-streaming request.
    This is an open issue in `requests`: https://github.com/psf/requests/issues/6512
    """
    session = SessionWithRetryAndTimeout(
        response_timeout_seconds=response_timeout_seconds
    )
    session.headers.update({"User-Agent": f"qai_hub/{qai_hub.__version__}"})
    if internal_retries:
        retries: Union[Retry, int] = LogRetry(
            total=MAX_RETRIES,
            # Enable exponential back-off
            backoff_factor=BACKOFF_FACTOR,
            # Retry for these statuses
            status_forcelist=RETRIABLE_STATUSES,
            # Retry on connection errors
            connect=MAX_RETRIES,
            # Retry on read errors
            read=MAX_RETRIES,
            # Don't retry on redirect (default)
            redirect=None,
            # Don't retry on other errors (urllib3 ignores safety of HTTP methods for "other" errors)
            other=0,
        )
    else:
        retries = 0

    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    return session


def create_external_session(
    internal_retries: bool = True,
) -> SessionWithRetryAndTimeout:
    """
    Get a requests.Session object pre-configured for interacting with services with strict SLAs.
    The same as create_session() but with a shorter response timeout.
    """
    return create_session(
        internal_retries=internal_retries,
        response_timeout_seconds=EXTERNAL_RESPONSE_TIMEOUT_SECONDS,
    )
