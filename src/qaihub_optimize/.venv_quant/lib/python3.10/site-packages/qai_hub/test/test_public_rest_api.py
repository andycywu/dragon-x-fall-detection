from unittest.mock import MagicMock

import pytest

import qai_hub.public_rest_api as api
from qai_hub import api_utils


def test_rate_limit_get():
    mock_session = MagicMock()
    api.create_session = MagicMock()
    api.create_session.return_value = mock_session
    rval = MagicMock()
    rval.status_code = 429
    mock_session.get = MagicMock(return_value=rval)

    with pytest.raises(api.APIException) as e:
        api.get_model(api_utils.load_default_api_config(), "2")

    assert e.value.status_code == 429  # too many requests
