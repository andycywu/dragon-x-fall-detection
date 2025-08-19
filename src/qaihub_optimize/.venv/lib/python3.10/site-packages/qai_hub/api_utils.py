from __future__ import annotations

import configparser
import datetime
import io
import json
import logging
import mimetypes
import os
import posixpath
import re
import shutil
import tempfile
import threading
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)
from urllib.parse import urljoin
from zipfile import ZipFile

import requests
import s3transfer.utils as s3utils
from requests_toolbelt import MultipartEncoder
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from typing_extensions import assert_never

from . import api_status_codes
from . import public_api_pb2 as api_pb
from .public_rest_api import APIException, ClientConfig, InputSpecs, _InputSpec
from .util.session import (
    create_external_session,
    create_session,
    retry_call_with_backoff,
    retry_with_backoff,
)

QAIHUB_CLIENT_ENV = "QAIHUB_CLIENT_INI"

InputSpecsList = List[Tuple[str, _InputSpec]]

_API_VERSION = "v1"

# Used for error message feedback
_CASUAL_CLASSNAMES = {
    api_pb.ProfileJob: "job",
    api_pb.Model: "model",
    api_pb.User: "user",
}
_DOCS_URL = "https://app.aihub.qualcomm.com/docs"
_SIGNUP_URL = "https://aihub.qualcomm.com/"
_DEFAULT_CONFIG_PATH = "~/.qai_hub/client.ini"


def get_config_path(expanduser=True):
    path = os.environ.get(QAIHUB_CLIENT_ENV, _DEFAULT_CONFIG_PATH)
    if expanduser:
        path = os.path.expanduser(path)
    return path


def response_as_protobuf(
    response: requests.Response, protobuf_class: Any, obj_id: Optional[str] = None
) -> Any:
    if (
        api_status_codes.is_success(response.status_code)
        and response.headers.get("Content-Type") == "application/x-protobuf"
    ):
        pb = protobuf_class()
        pb.ParseFromString(response.content)
        return pb
    elif (
        response.status_code == api_status_codes.HTTP_404_NOT_FOUND
        and obj_id is not None
    ):
        prefix = ""
        class_name = _CASUAL_CLASSNAMES.get(protobuf_class)
        if class_name is not None:
            prefix = class_name.capitalize() + " "

        raise APIException(
            f"{prefix}ID '{obj_id}' could not be found. It may not exist or you may not have permission to view it.",
            status_code=response.status_code,
            url=response.url,
        )
    elif response.status_code in [
        api_status_codes.HTTP_400_BAD_REQUEST,
        api_status_codes.HTTP_403_FORBIDDEN,
        api_status_codes.HTTP_409_CONFLICT,
        api_status_codes.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        api_status_codes.HTTP_426_UPGRADE_REQUIRED,
        api_status_codes.HTTP_429_TOO_MANY_REQUESTS,
    ]:
        raise APIException(
            response.text,
            status_code=response.status_code,
            url=response.url,
        )
    else:
        raise APIException(status_code=response.status_code, url=response.url)


def offset_limit_url_params(offset: int, limit: Optional[int]) -> dict[str, Any]:
    url_params = {}
    if offset > 0:
        url_params["offset"] = offset
    if limit is not None:
        url_params["limit"] = limit
    return url_params


def load_default_api_config(verbose=False) -> ClientConfig:
    """
    Load a default ClientConfig from default locations.

    Parameters
    ----------
    verbose : bool
        Print where config file is loaded from.

    Returns
    -------
    config : ClientConfig
        API authentication configuration.
    """
    # Load from default config path
    config = configparser.ConfigParser()
    # Client config should be in ~/.qai_hub/client.ini
    tilde_config_path = get_config_path(expanduser=False)
    config_path = os.path.expanduser(tilde_config_path)
    if verbose:
        print(f"Loading Client config from {tilde_config_path} ...")
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"{tilde_config_path} not found. "
            f"Please request access at {_SIGNUP_URL}. "
            f"If you have access, please refer to {_DOCS_URL} for instructions on configuring the API key."
        )
    config.read([config_path])
    try:
        client_config = config["api"]

        api_config = ClientConfig(
            api_url=client_config["api_url"],
            web_url=client_config["web_url"],
            api_token=client_config["api_token"],
            verbose=(
                str2bool(client_config["verbose"])
                if "verbose" in client_config
                else True
            ),
        )
    except KeyError:
        raise APIException(
            status_code=api_status_codes.API_CONFIGURATION_MISSING_FIELDS
        )
    return api_config


def auth_header(
    config: ClientConfig, content_type: str = "application/x-protobuf"
) -> dict:
    header = {
        "Authorization": f"token {config.api_token}",
        "Content-Type": content_type,
    }
    return header


def api_url(config: ClientConfig, *rel_paths) -> str:
    return urljoin(config.api_url, posixpath.join("api", _API_VERSION, *rel_paths, ""))


def get_token(api_url, email, password):
    url = urljoin(
        api_url, posixpath.join("api", _API_VERSION, "users", "auth", "login", "")
    )
    data = {"email": email, "password": password}
    header = {"Content-Type": "application/json"}
    response = retry_call_with_backoff(
        lambda: create_session().post(url, headers=header, data=json.dumps(data))
    )
    if api_status_codes.is_success(response.status_code):
        return json.loads(response.content)["key"]
    elif response.status_code == 400:
        raise ValueError("Failed to log in: Wrong Username / Password")
    else:
        raise APIException(status_code=response.status_code, url=url)


def str2bool(s: str) -> bool:
    if s.lower() in ("yes", "true", "t", "1"):
        return True
    if s.lower() in ("no", "false", "f", "0"):
        return False
    raise ValueError(f"Unrecognized boolean string value {s}")


_STR_TO_TETRA_TYPE: Dict[str, api_pb.TensorDtype.ValueType] = {
    "float16": api_pb.TensorDtype.TENSOR_DTYPE_FLOAT16,
    "float32": api_pb.TensorDtype.TENSOR_DTYPE_FLOAT32,
    "int32": api_pb.TensorDtype.TENSOR_DTYPE_INT32,
    "int8": api_pb.TensorDtype.TENSOR_DTYPE_INT8,
    "uint8": api_pb.TensorDtype.TENSOR_DTYPE_UINT8,
    "int16": api_pb.TensorDtype.TENSOR_DTYPE_INT16,
    "uint16": api_pb.TensorDtype.TENSOR_DTYPE_UINT16,
    "int64": api_pb.TensorDtype.TENSOR_DTYPE_INT64,
    "bool": api_pb.TensorDtype.TENSOR_DTYPE_BOOL,
}
_TETRA_TYPE_TO_STR: Dict[api_pb.TensorDtype.ValueType, str] = {
    v: k for k, v in _STR_TO_TETRA_TYPE.items()
}


def _get_type_str_from_value(type: api_pb.TensorDtype.ValueType) -> str:
    dtype = _TETRA_TYPE_TO_STR.get(type, None)
    if dtype is None:
        raise ValueError("Unknown tensor dtype")
    return dtype


def get_type_value_from_str(dtype: str) -> api_pb.TensorDtype.ValueType:
    type = _STR_TO_TETRA_TYPE.get(dtype, None)
    if type is None:
        raise ValueError(
            f"Unsupported tensor dtype={dtype}. Supported dtypes: {list(_STR_TO_TETRA_TYPE.keys())}"
        )
    return type


def _create_named_tensor(
    name: str, shape: Tuple[int, ...], type: str
) -> api_pb.NamedTensorType:
    tensor_type_list = []
    for i in shape:
        tensor_type_list.append(i)
    tensor_type_pb = api_pb.TensorType(
        shape=tensor_type_list, dtype=get_type_value_from_str(type)
    )
    return api_pb.NamedTensorType(name=name, tensor_type=tensor_type_pb)


def input_shapes_to_tensor_type_list_pb(
    input_shapes: InputSpecs | None,
) -> api_pb.NamedTensorTypeList:
    tensor_type_pb_list = []

    if input_shapes is not None:
        for name, spec in input_shapes.items():
            shape: Tuple[int, ...]
            if isinstance(spec[0], tuple):
                shape = spec[0]
                dtype = spec[1]
            else:
                shape = spec  # type: ignore
                dtype = "float32"

            assert isinstance(dtype, str)
            assert isinstance(shape, tuple)
            named_tensor_type_pb = _create_named_tensor(name, shape, dtype)
            tensor_type_pb_list.append(named_tensor_type_pb)

    return api_pb.NamedTensorTypeList(types=tensor_type_pb_list)


def tensor_type_list_pb_to_list_shapes(
    tensor_type_list_pb: api_pb.NamedTensorTypeList,
) -> InputSpecsList:
    shapes_list = []

    for t in tensor_type_list_pb.types:
        type = _get_type_str_from_value(t.tensor_type.dtype)
        shape = tuple([int(d) for d in t.tensor_type.shape])
        shapes_list.append((t.name, (shape, type)))

    return shapes_list


def input_shapes_dict_to_list(input_shapes: InputSpecs) -> InputSpecsList:
    return tensor_type_list_pb_to_list_shapes(
        input_shapes_to_tensor_type_list_pb(input_shapes)
    )


_get_unique_path_lock = threading.Lock()


def get_unique_path(dst_path: str) -> Tuple[str, str]:
    name, ext = os.path.splitext(dst_path)
    if ext == ".zip":
        name, sub_ext = os.path.splitext(name)
        ext = sub_ext + ext

    _get_unique_path_lock.acquire()
    if os.path.exists(dst_path):
        now = str(datetime.datetime.now().time()).replace(":", ".")
        dst_path = f"{name}_{now}{ext}"

    # Write empty file (to be overwritten later), for thread safety.
    open(dst_path, "a").close()

    _get_unique_path_lock.release()

    name = os.path.basename(dst_path)

    return dst_path, name


def extract_error_text(response: requests.Response):
    # https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html
    # kids, you should never use a regex to parse XML. but this response
    # is very constrained and XML parsers are full of vulnerabilities
    code_match = re.search(r"<Code>(\w{,100})</Code>", response.text)
    code = code_match[1] if code_match else ""
    message_match = re.search(r"<Message>([^<]{,1000})</Message>", response.text)
    message = message_match[1] if message_match else ""
    if code or message:
        return f"{code}: {message}"
    else:
        return response.reason


def _verify_download_path(
    filename: str,
    dst_path: str,
    should_extract_file: bool,
) -> tuple[str, str]:
    dst_path = os.path.expanduser(dst_path)  # Expand ~ to user home in path.

    # If no filename is provided, use the filename given to us by the parent
    if os.path.isdir(dst_path):
        dst_path = os.path.join(dst_path, filename)

        # Append numerical suffix to the filename if the dst file already exists.
        dst_path, filename = get_unique_path(dst_path)

        # Remove .zip extension from destination path
        if should_extract_file:
            dst_path = os.path.splitext(dst_path)[0]
    elif should_extract_file:
        raise ValueError(
            "Model cannot be extracted to a file. Please provide a directory path."
        )
    else:
        # If the given path is not a directory, assume it's a filepath
        # If the filename doesn't have the right file extension, append it

        # This properly handles cases like foo.tar.gz and correctly returns .tar.gz
        file_extension = "".join(Path(filename).suffixes)

        if not dst_path.endswith(file_extension):
            dst_path += file_extension

    # Verify dst parent dir exists. The same error thrown by open() called
    # below would include the model name, which is confusing.
    parent_dir, filename = os.path.split(dst_path)
    if parent_dir and not os.path.exists(parent_dir):
        raise ValueError(f"Download directory '{parent_dir}' does not exist.")

    return filename, dst_path


def get_progress_bar(description, file_size, block_size, verbose):
    return tqdm(
        disable=not verbose,  # 'disable' will completely bypass the progress bar
        total=file_size,
        unit="B",
        unit_scale=True,
        unit_divisor=block_size,
        colour="blue",
        desc=description,
    )


@retry_with_backoff()
def _download_to_verified_path(
    url: str,
    filename: str,
    dst_path: str,
    verbose: bool,
    should_extract_file: bool,
):
    # Suppress get()'s built-in internal retries so we can restart the
    # progress bar on errors.
    response = create_external_session(internal_retries=False).get(url, stream=True)
    if api_status_codes.is_success(response.status_code):
        file_size = int(response.headers.get("content-length", 0))
        block_size = 1024

        with get_progress_bar(filename, file_size, block_size, verbose) as progress_bar:
            # Download to a temporary directory first, so if the download
            # fails or is cancelled midway, the user isn't left with a
            # useless partial artifact on disk.
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_dst_path = os.path.join(tmpdir, os.path.basename(dst_path))
                with open(tmp_dst_path, "wb") as fd:
                    for data in response.iter_content(block_size):
                        written_data = fd.write(data)
                        progress_bar.update(written_data)

                if should_extract_file:
                    with ZipFile(tmp_dst_path, "r") as zippedModel:
                        zippedModel.extractall(dst_path)
                    os.remove(tmp_dst_path)
                else:
                    # Cannot use os.rename, whose doc string states: "On
                    # Windows, if dst exists a FileExistsError is always
                    # raised." `dst_path` is always created by
                    # `_get_unique_path`
                    # `os.replace` gives "The system cannot move the file to a
                    # different disk drive"
                    shutil.move(tmp_dst_path, dst_path)

    return response


def download_file(
    url: str,
    filename: str,
    dst_path: str,
    verbose: bool,
    extract_if_zipped: bool = False,
) -> str:
    # Unzip file only if extract_if_zipped is set and uploaded file is zipped.
    should_extract_file = extract_if_zipped and filename.endswith(".zip")

    filename, dst_path = _verify_download_path(filename, dst_path, should_extract_file)

    response = _download_to_verified_path(
        url, filename, dst_path, verbose, should_extract_file
    )
    if not api_status_codes.is_success(response.status_code):
        raise APIException(
            f"Failed to download. {extract_error_text(response)}",
            status_code=response.status_code,
            url=response.url,
        )

    return dst_path


def guess_file_http_content_type(path: str | Path) -> str:
    file_type = None

    if isinstance(path, str) and path.endswith(".log"):
        # `.log` is not supported by mimetypes on linux.
        file_type = "text/plain"
    elif isinstance(path, str) and path.endswith("schematic.bin"):
        # `schematic.bin` is a text file with a wacky name.
        file_type = "text/plain"
    else:
        file_type, _ = mimetypes.guess_type(path, strict=True)

    return file_type or "application/octet-stream"


@retry_with_backoff()
def _try_upload_asset(
    upload_url: str,
    asset_file: io.IOBase,
    asset_offset: int,
    asset_size: int,
    full_file_size: int,
    file_field_name: str,
    fields: Dict[str, Any] = {},
    verbose: bool = True,
    progress_bar_description: Optional[str] = None,
    upload_method: Union[Literal["post"], Literal["put"]] = "post",
    content_type: str = "application/octet-stream",
) -> requests.Response:
    # NOTE: If changing this code, use manual_test_flaky_upload_download as a stress test

    progress_bar = get_progress_bar(
        description=progress_bar_description,
        file_size=asset_size,
        block_size=1024,
        verbose=verbose,
    )

    # Suppress built-in retries so we can restart the progress bar and multipart encoder on errors.
    session = create_external_session(internal_retries=False)

    # Rewind the file to the right spot (in case of retry)
    asset_file.seek(asset_offset)

    try:
        if upload_method == "post":
            # MultipartEncoder only works for multi-part POST requests with a form body.
            # (It does not work for PUT requests - it inserts a plaintext content-type and boundary
            # at the start of the uploaded data.)

            fields[file_field_name] = (
                "model",
                asset_file,
                content_type,
            )
            mpe = MultipartEncoder(fields=fields)
            asset_file_wrapped = CallbackIOWrapper(progress_bar.update, mpe, "read")
            headers = {"content-type": mpe.content_type}
            response = session.post(
                upload_url,
                allow_redirects=False,
                data=asset_file_wrapped,  # type: ignore
                headers=headers,
            )
        elif upload_method == "put":
            # This is used for multipart uploads to S3, which doesn't support POST requests.

            # a file-like object that acts as if this chunk is the whole file
            asset_chunk = s3utils.ReadFileChunk(
                asset_file,  # type: ignore
                asset_size,
                full_file_size,
                callbacks=[
                    lambda bytes_transferred: progress_bar.update(bytes_transferred)
                ],
            )
            response = session.put(upload_url, allow_redirects=False, data=asset_chunk)
        else:
            assert_never(upload_method)
    except Exception:
        # keep the progress bar from incorrectly showing a completed upload
        progress_bar.disable = True
        print("\n")
        raise

    progress_bar.close()
    return response


def upload_asset(
    upload_url: str,
    asset_file: io.IOBase,
    asset_size: int,
    full_file_size: int,
    file_field_name: str,
    fields: Dict[str, Any] = {},
    verbose: bool = True,
    progress_bar_description: Optional[str] = None,
    upload_method: str = "post",
    content_type: str = "application/octet-stream",
    logger: logging.Logger = logging.getLogger("api_utils"),
) -> str | None:
    """
    Helper upload function for models, datasets, etc.
    """

    # TODO: log and sanitize this URL instead of truncating it (#13103)
    logger.info(f"Uploading asset to {upload_url[:300]}")

    asset_offset = asset_file.tell()
    response = _try_upload_asset(
        upload_url=upload_url,
        upload_method=upload_method,
        asset_file=asset_file,
        asset_offset=asset_offset,
        asset_size=asset_size,
        full_file_size=full_file_size,
        file_field_name=file_field_name,
        fields=fields,
        verbose=verbose,
        progress_bar_description=progress_bar_description,
        content_type=content_type,
    )

    if not api_status_codes.is_success(response.status_code):
        raise APIException(
            message=f"Failed to upload the file. {extract_error_text(response)}",
            status_code=response.status_code,
            url=response.url,
        )

    logger.info(
        f"Successfully uploaded asset with response status: {response.status_code}"
    )

    if response.headers:
        # Multipart uploads to S3 return an ETag header that's used for stitching the parts together.
        return response.headers.get("ETag", None)

    return None
