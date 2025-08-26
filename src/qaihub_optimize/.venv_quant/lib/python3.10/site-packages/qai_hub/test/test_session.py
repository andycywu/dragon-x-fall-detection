from unittest.mock import Mock, PropertyMock

import pytest

import qai_hub.util.session
from qai_hub.util.session import retry_with_backoff


class MyRetriableException(Exception):
    pass


@pytest.fixture
def patch_wait_time(monkeypatch):
    monkeypatch.setattr(qai_hub.util.session, "MAX_WAIT", 0.1)


@pytest.fixture
def ok_status(patch_wait_time):
    return PropertyMock(return_value=200)


@pytest.fixture
def retriable_status(patch_wait_time):
    return PropertyMock(return_value=500)


@pytest.fixture
def fatal_status(patch_wait_time):
    return PropertyMock(return_value=400)


def make_response(status_mock):
    response = Mock(name="response")
    type(response).status_code = status_mock
    return response


def test_retriable_exception(ok_status):
    expected_ok_response = make_response(ok_status)
    test_func = Mock(
        side_effect=[
            MyRetriableException(),
            MyRetriableException(),
            MyRetriableException(),
            expected_ok_response,
            # should never get here
            make_response(ok_status),
        ]
    )

    decorated_func = retry_with_backoff([MyRetriableException])(test_func)
    response = decorated_func()

    assert test_func.call_count == 4
    ok_status.assert_called_once()
    assert response == expected_ok_response


def test_max_exception_retries(ok_status):
    test_func = Mock(
        side_effect=[
            MyRetriableException(),
            MyRetriableException(),
            MyRetriableException(),
            MyRetriableException(),
            MyRetriableException(),
            MyRetriableException(),
            # should never get here
            make_response(ok_status),
        ]
    )

    # decorated_func = retry_with_backoff(MyRetriableException)(test_func)
    decorated_func = retry_with_backoff([MyRetriableException])(test_func)
    with pytest.raises(MyRetriableException):
        decorated_func()

    assert test_func.call_count == 6
    ok_status.assert_not_called()


def test_fatal_status(fatal_status, ok_status, retriable_status):
    expected_fatal_response = make_response(fatal_status)
    test_func = Mock(
        side_effect=[
            make_response(retriable_status),
            expected_fatal_response,
            # should never get here
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(ok_status),
        ]
    )

    decorated_func = retry_with_backoff()(test_func)
    response = decorated_func()

    assert test_func.call_count == 2
    assert retriable_status.call_count == 1
    fatal_status.assert_called_once()
    ok_status.assert_not_called()
    assert response == expected_fatal_response


def test_retriable_status(ok_status, retriable_status):
    expected_ok_response = make_response(ok_status)
    test_func = Mock(
        side_effect=[
            make_response(retriable_status),
            make_response(retriable_status),
            expected_ok_response,
            # should never get here
            make_response(retriable_status),
            make_response(ok_status),
        ]
    )

    decorated_func = retry_with_backoff()(test_func)
    response = decorated_func()

    assert test_func.call_count == 3
    assert retriable_status.call_count == 2
    ok_status.assert_called_once()
    assert response == expected_ok_response


def test_max_status_retries(retriable_status):
    expected_retriable_response = make_response(retriable_status)
    test_func = Mock(
        side_effect=[
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(retriable_status),
            expected_retriable_response,
            # should never get here
            make_response(retriable_status),
            make_response(retriable_status),
        ]
    )

    decorated_func = retry_with_backoff()(test_func)
    response = decorated_func()

    assert test_func.call_count == 6
    # it doesn't really matter if it checks the status after the last try
    assert retriable_status.call_count >= 5 and retriable_status.call_count <= 6
    assert response == expected_retriable_response


def test_max_mixed_retries(ok_status, retriable_status):
    test_func = Mock(
        side_effect=[
            make_response(retriable_status),
            make_response(retriable_status),
            MyRetriableException(),
            MyRetriableException(),
            MyRetriableException(),
            make_response(retriable_status),
            MyRetriableException(),
            make_response(retriable_status),
            MyRetriableException(),
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(retriable_status),
            make_response(retriable_status),
            MyRetriableException(),
            # should never get here
            make_response(retriable_status),
            make_response(retriable_status),
            MyRetriableException(),
            make_response(ok_status),
        ]
    )

    decorated_func = retry_with_backoff([MyRetriableException])(test_func)
    with pytest.raises(MyRetriableException):
        decorated_func()

    # sadly the retry count is not shared between the exception and status retries;
    # in fact, the status retry count gets reset every time an exception is raised
    assert test_func.call_count == 15
    assert retriable_status.call_count == 9
    ok_status.assert_not_called()
