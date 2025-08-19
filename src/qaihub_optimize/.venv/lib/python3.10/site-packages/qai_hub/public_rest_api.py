from __future__ import annotations

import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)

import numpy as np
from typing_extensions import assert_never

from . import api_status_codes, api_utils
from . import public_api_pb2 as api_pb
from .util.session import (
    create_session,
    retry_call_with_backoff,
)

UNKNOWN_ERROR = "Unknown error."
DEFAULT_HUB_WEB_URL = "https://app.aihub.qualcomm.com"
_InputSpec = Tuple[Tuple[int, ...], str]
InputSpecs = Mapping[str, Union[Tuple[int, ...], _InputSpec]]
DatasetEntries = Mapping[str, List[np.ndarray]]


@dataclass
class ClientConfig:
    """
    Configuration information, such as your API token, for use with
    :py:class:`.Client`.

    Parameters
    ----------
    api_url
        URL of the API backend endpoint.
    web_url
        URL of the web interface.
    api_token
        API token. Available through the web interface under the "Account" page.
    verbose
        Verbosity of terminal output (eg. whether to print status bars for uploads & downloads)
    """

    api_url: str
    web_url: str
    api_token: str
    verbose: bool


class APIException(Exception):
    """
    Exception for the python REST API.

    Parameters
    ----------
    message : str
        Message of the failure. If None, sets it automatically based on
        `status_code`.
    status_code : int
        API status code (a superset of HTTP status codes).
    url: Optional[str]
        The URL for the API call that threw this exception.
        This is optional because we sometimes throw this exception without making an API call,
        or from call sites where the API URL is unavailable.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
    ):
        if not message:
            if status_code is not None:
                # Some common error codes have custom messages
                if status_code == api_status_codes.HTTP_401_UNAUTHORIZED:
                    message = "API authentication failure; please check your API token."
                elif status_code == api_status_codes.HTTP_429_TOO_MANY_REQUESTS:
                    message = "Too Many Requests: please slow down and try again soon."
                elif status_code == api_status_codes.API_CONFIGURATION_MISSING_FIELDS:
                    config_path = api_utils.get_config_path(expanduser=False)
                    message = f"Required fields are missing from your {config_path}."
                elif status_code == api_status_codes.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
                    message = "The uploaded asset is too large. Please contact us for workarounds."
                elif status_code == api_status_codes.HTTP_426_UPGRADE_REQUIRED:
                    message = "This version of the Hub client is no longer supported. Please upgrade by running 'pip install --upgrade qai-hub'."
                else:
                    message = f"API request returned status code {status_code}."
            else:
                message = UNKNOWN_ERROR

        super().__init__(message)
        self.status_code = status_code
        self.url = url


def get_auth_user(config: ClientConfig) -> api_pb.User:
    """
    Get authenticated user information.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.

    Returns
    -------
    user_pb : User
        Get authenticated user information.
    """
    url = api_utils.api_url(config, "users", "auth", "user")
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header)
    return api_utils.response_as_protobuf(response, api_pb.User)


def get_device_list(
    config: ClientConfig,
    name: str = "",
    os: str = "",
    attributes: List[str] = [],
    select: bool = False,
) -> api_pb.DeviceList:
    """
    Get list of active devices.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    name : str
        Only devices with this exact name will be returned.
    os : str
        Only devices with an OS version that is compatible with this os are returned
    attributes : List[str]
        Only devices that have all requested properties are returned.
    select: bool
        whether to return a list or a single device

    Returns
    -------
    device_list_pb : DeviceList
       Device list as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "devices")
    url_params: Dict[str, Union[bool, str, Iterable[str]]] = {
        "name": name,
        "os": os,
        "select": select,
        "attributes": attributes,
    }
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header, params=url_params)
    return api_utils.response_as_protobuf(response, api_pb.DeviceList)


def create_compile_job(
    config: ClientConfig, compile_job_pb: api_pb.CompileJob
) -> api_pb.CreateUpdateResponse:
    """
    Create new compile job.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_pb : CompileJob
        Protobuf object with new compile job.

    Returns
    -------
    response_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse. If successful, ``id`` will be nonzero.
        If failure, ``id`` will be zero and ``status`` will contain an error.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs")
    header = api_utils.auth_header(config)
    job_pb = api_pb.Job(compile_job=compile_job_pb)
    response = retry_call_with_backoff(
        lambda: create_session().post(
            url,
            data=job_pb.SerializeToString(),
            headers=header,
        )
    )
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create compile job: " + response_pb.status)
    return response_pb


def create_link_job(
    config: ClientConfig, link_job_pb: api_pb.LinkJob
) -> api_pb.CreateUpdateResponse:
    """
    Create new link job.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_pb : LinkJob
        Protobuf object with new link job.

    Returns
    -------
    response_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse. If successful, ``id`` will be nonzero.
        If failure, ``id`` will be zero and ``status`` will contain an error.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs")
    header = api_utils.auth_header(config)
    job_pb = api_pb.Job(link_job=link_job_pb)
    response = retry_call_with_backoff(
        lambda: create_session().post(
            url,
            data=job_pb.SerializeToString(),
            headers=header,
        )
    )
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create link job: " + response_pb.status)
    return response_pb


def create_quantize_job(
    config: ClientConfig, quantize_job_pb: api_pb.QuantizeJob
) -> api_pb.CreateUpdateResponse:
    """
    Create new quantize job.
    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_pb : QuantizeJob
        Protobuf object with new quantize job.
    Returns
    -------
    response_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse. If successful, ``id`` will be nonzero.
        If failure, ``id`` will be zero and ``status`` will contain an error.
    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs")
    header = api_utils.auth_header(config)
    job_pb = api_pb.Job(quantize_job=quantize_job_pb)
    response = create_session().post(
        url,
        data=job_pb.SerializeToString(),
        headers=header,
    )
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create quantize job: " + response_pb.status)
    return response_pb


def create_profile_job(
    config: ClientConfig, profile_job_pb: api_pb.ProfileJob
) -> api_pb.CreateUpdateResponse:
    """
    Create new profile job.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_pb : ProfileJob
        Protobuf object with new profile job.

    Returns
    -------
    response_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse. If successful, ``id`` will be nonzero.
        If failure, ``id`` will be zero and ``status`` will contain an error.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs")
    header = api_utils.auth_header(config)
    job_pb = api_pb.Job(profile_job=profile_job_pb)
    response = retry_call_with_backoff(
        lambda: create_session().post(
            url,
            data=job_pb.SerializeToString(),
            headers=header,
        )
    )
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create profile job: " + response_pb.status)
    return response_pb


def create_inference_job(
    config: ClientConfig, inference_job_pb: api_pb.InferenceJob
) -> api_pb.CreateUpdateResponse:
    """
    Create new inference job.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_pb : InferenceJob
        Protobuf object containing properties for the new inference job

    Returns
    -------
    response_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse. If successful, ``id`` will be nonzero.
        If failure, ``id`` will be zero and ``status`` will contain an error.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs")
    header = api_utils.auth_header(config)
    job_pb = api_pb.Job(inference_job=inference_job_pb)

    response = retry_call_with_backoff(
        lambda: create_session().post(
            url,
            data=job_pb.SerializeToString(),
            headers=header,
        )
    )
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create an inference job: " + response_pb.status)
    return response_pb


def get_job(config: ClientConfig, job_id: str) -> api_pb.Job:
    """
    Get job information.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_id : str
        Job ID.

    Returns
    -------
    job_pb : Job
        Job as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs", job_id)
    if not job_id:
        raise ValueError(f"Invalid job_id: '{job_id}'")
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header)
    return api_utils.response_as_protobuf(response, api_pb.Job, obj_id=job_id)


def set_job_name(
    config: ClientConfig, job_id: str, job_name: str
) -> api_pb.CreateUpdateResponse:
    """
    Set the job's name.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_id : str
        Job ID.
    job_name : str
        Job name.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs", job_id)
    header = api_utils.auth_header(config)
    update_data = api_pb.JobPublicUpdate(name=job_name)

    response = retry_call_with_backoff(
        lambda: create_session().patch(
            url, headers=header, data=update_data.SerializeToString()
        )
    )

    return api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse, obj_id=job_id
    )


def get_job_list(
    config: ClientConfig,
    offset: int = 0,
    limit: int | None = None,
    states: List[api_pb.JobState.ValueType] = [],
    job_type: api_pb.JobType.ValueType = api_pb.JobType.JOB_TYPE_UNSPECIFIED,
    creator: str | None = None,
) -> api_pb.JobList:
    """
    Get list of jobs visible to the authenticated user.

    Parameters
    ----------
    config :
        API authentication configuration.
    offset : int
        Offset the query.
    limit : int
        Limit query response size.
    states :
        Filter by list of states.
    job_type :
        Filter by job type. JOB_TYPE_UNSPECIFIED will return all jobs.
    creator:
        Filter by job creator. If unspecified, will return all jobs created by anyone in the user's organization.

    Returns
    -------
    list_pb : JobList
        List of jobs as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "jobs")

    url_params = api_utils.offset_limit_url_params(offset, limit)
    if creator:
        url_params["creator"] = creator
    if states:
        states_str = ",".join([str(x) for x in states])
        url_params["state"] = states_str
    if job_type == api_pb.JobType.JOB_TYPE_COMPILE:
        url_params["type"] = "compile"
    elif job_type == api_pb.JobType.JOB_TYPE_PROFILE:
        url_params["type"] = "profile"
    elif job_type == api_pb.JobType.JOB_TYPE_INFERENCE:
        url_params["type"] = "inference"
    elif job_type == api_pb.JobType.JOB_TYPE_QUANTIZE:
        url_params["type"] = "quantize"
    elif job_type == api_pb.JobType.JOB_TYPE_LINK:
        url_params["type"] = "link"

    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header, params=url_params)
    return api_utils.response_as_protobuf(response, api_pb.JobList)


def get_job_summary_list(
    config: ClientConfig,
    offset: int = 0,
    limit: int | None = None,
    states: List[api_pb.JobState.ValueType] = [],
    job_type: api_pb.JobType.ValueType = api_pb.JobType.JOB_TYPE_UNSPECIFIED,
    creator: str | None = None,
) -> api_pb.JobSummaryList:
    """
    Get list of summaries of jobs visible to the authenticated user.

    Parameters
    ----------
    config :
        API authentication configuration.
    offset : int
        Index offset at which to start the query.
    limit : int
        Limit query response size.
    states :
        Filter by list of states.
    job_type :
        Filter by job type. JOB_TYPE_UNSPECIFIED will return all jobs.
    creator:
        Filter by job creator. If unspecified, will return all jobs created by anyone in the user's organization.

    Returns
    -------
    list_pb : JobSummaryList
        List of jobs as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "job_summaries")

    url_params = api_utils.offset_limit_url_params(offset, limit)
    if creator:
        url_params["creator"] = creator
    if states:
        states_str = ",".join([str(x) for x in states])
        url_params["state"] = states_str
    if job_type == api_pb.JobType.JOB_TYPE_COMPILE:
        url_params["type"] = "compile"
    elif job_type == api_pb.JobType.JOB_TYPE_LINK:
        url_params["type"] = "link"
    elif job_type == api_pb.JobType.JOB_TYPE_PROFILE:
        url_params["type"] = "profile"
    elif job_type == api_pb.JobType.JOB_TYPE_INFERENCE:
        url_params["type"] = "inference"
    elif job_type == api_pb.JobType.JOB_TYPE_QUANTIZE:
        url_params["type"] = "quantize"

    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header, params=url_params)
    return api_utils.response_as_protobuf(response, api_pb.JobSummaryList)


def get_job_results(config: ClientConfig, job_id: str) -> api_pb.JobResult:
    """
    Get job results, if available.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_id : str
        Job ID as integer.

    Results
    -------
    res_pb : ProfileJobResult
        Result is returned as a protobuf object. Or None if results are not available.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)
    url = api_utils.api_url(config, "jobs", job_id, "result")
    response = create_session().get(url, headers=header)
    return api_utils.response_as_protobuf(response, api_pb.JobResult, obj_id=job_id)


def get_model_vizgraph(config: ClientConfig, model_id: str) -> api_pb.VizGraph:
    """
    Get model vizgraph, if available.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        Model ID.

    Results
    -------
    vizgraph_pb : VizGraph
        Visualization graph representing the model.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)
    url = api_utils.api_url(config, "models", model_id, "vizgraph")
    response = create_session().get(url, headers=header)
    return api_utils.response_as_protobuf(response, api_pb.VizGraph, obj_id=model_id)


class SharedEntityType(Enum):
    """
    Types of objects for which sharing APIs apply.
    """

    JOB = 0
    MODEL = 1
    DATASET = 2

    def to_api_url_name(self):
        if self == SharedEntityType.JOB:
            return "jobs"
        elif self == SharedEntityType.MODEL:
            return "models"
        elif self == SharedEntityType.DATASET:
            return "datasets"
        assert_never(self)


def get_sharing(
    config: ClientConfig, entity_id: str, entity_type: SharedEntityType
) -> api_pb.SharedAccess:
    """
    Get the list of users that the entity is shared with.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    entity_id : str
        Entity ID.
    entity_type: SharedEntityType
        Type of entity being shared.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)
    url = api_utils.api_url(
        config, entity_type.to_api_url_name(), entity_id, "shared_access"
    )

    response = create_session().get(url, headers=header)

    return api_utils.response_as_protobuf(
        response, api_pb.SharedAccess, obj_id=entity_id
    )


def modify_sharing(
    config: ClientConfig,
    entity_id: str,
    entity_type: SharedEntityType,
    add_emails: List[str],
    delete_emails: List[str],
) -> api_pb.CreateUpdateResponse:
    """
    Modifies the list of users that the entity is shared with.

    If the entity is a job, all assets associated with the job will also be shared.
    For inference and profile jobs, the corresponding compile and link jobs (if any)
    will also be shared.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    entity_id : str
        Entity ID.
    entity_type: SharedEntityType
        Type of entity being shared.
    add_emails : List[str]
        List of email addresses to share with.
    delete_emails : List[str]
        List of email addresses to remove from sharing.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)
    url = api_utils.api_url(
        config, entity_type.to_api_url_name(), entity_id, "shared_access"
    )
    update_data = api_pb.SharedAccessChange(
        add_email=add_emails, remove_email=delete_emails
    )

    response = create_session().patch(
        url, headers=header, data=update_data.SerializeToString()
    )

    return api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse, obj_id=entity_id
    )


def disable_sharing(
    config: ClientConfig,
    entity_id: str,
    entity_type: SharedEntityType,
) -> api_pb.CreateUpdateResponse:
    """
    Disable all sharing for the specified entity.

    If the entity is a dataset or model, note that it
    may still be shared via related jobs, even when
    explicitly shared emails are removed via this API.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    entity_id : str
        Entity ID.
    entity_type: SharedEntityType
        Type of entity being shared.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)
    url = api_utils.api_url(
        config, entity_type.to_api_url_name(), entity_id, "shared_access"
    )

    response = create_session().delete(url, headers=header)

    return api_utils.response_as_protobuf(
        response, api_pb.CreateUpdateResponse, obj_id=entity_id
    )


def _create_model(
    config: ClientConfig,
    model_pb: api_pb.Model,
    verbose: bool | None = None,
) -> api_pb.CreateUpdateResponse:
    """
    Create a model object.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_pb : Model
        Model protobuf object
    verbose : bool | None
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    url = api_utils.api_url(config, "models")

    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        retry_call_with_backoff(
            lambda: create_session().post(
                url, data=model_pb.SerializeToString(), headers=header
            )
        ),
        api_pb.CreateUpdateResponse,
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create model: " + response_pb.status)
    return response_pb


def _get_model_upload_url(
    config: ClientConfig,
    model_id: str,
    file_size: int | None = None,
    verbose: bool | None = None,
) -> api_pb.FileUploadURL:
    """
    Get the URL with which the user should upload the model file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        ID of the model to query.
    verbose : bool | None
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : FileUploadURL
        Returns a FileUploadURL protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    url = api_utils.api_url(config, f"models/{model_id}/upload_url")
    params = {"file_size": file_size} if file_size else None
    return api_utils.response_as_protobuf(
        create_session().get(url, headers=header, params=params),
        api_pb.FileUploadURL,
    )


def _get_model_multipart_upload_urls(
    config: ClientConfig, model_id: str, file_size: int, verbose: bool | None = None
) -> api_pb.FileMultipartUploadURL:
    """
    Get the URLs with which the user should upload the model file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        ID of the model to query.
    file_size: int
        Size of the model in bytes.
    verbose : bool | None
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : FileMultipartUploadURL
        Returns a FileMultipartUploadURL protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    url = api_utils.api_url(config, f"models/{model_id}/multipart_upload")
    return api_utils.response_as_protobuf(
        create_session().get(url, params={"file_size": file_size}, headers=header),
        api_pb.FileMultipartUploadURL,
    )


def update_model_pb(
    config: ClientConfig,
    model_id: str,
    model_pb: api_pb.Model,
    verbose: bool | None = None,
    safe_to_retry: bool = False,
) -> api_pb.CreateUpdateResponse:
    """
    Confirm to hub that the upload for the corresponding model is complete.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        ID of the model to update.
    model_pb: Model
        Which fields to updates (the rest should be unspecified).
    verbose : bool
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    url = api_utils.api_url(config, f"models/{model_id}")
    patch = lambda: create_session().patch(  # noqa: E731
        url, data=model_pb.SerializeToString(), headers=header
    )
    if safe_to_retry:
        response = retry_call_with_backoff(patch)
    else:
        response = patch()
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response,
        api_pb.CreateUpdateResponse,
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to confirm model upload: " + response_pb.status)
    return response_pb


def _complete_model_multipart_upload(
    config: ClientConfig,
    model_id: str,
    upload_id: str,
    etags: list[str],
    verbose: bool | None = None,
) -> api_pb.CreateUpdateResponse:
    """
    Confirm to hub that all parts for the corresponding model have been uploaded.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        ID of the model to update.
    upload_id: str
        ID of the multipart upload.
    etags: list[str]
        List of ETags for the uploaded parts.
    verbose : bool
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    complete_multipart_pb = api_pb.FileMultipartUploadComplete(
        upload_id=upload_id, etags=etags
    )
    header = api_utils.auth_header(config)

    url = api_utils.api_url(config, f"models/{model_id}/multipart_upload")

    response = retry_call_with_backoff(
        lambda: create_session().post(  # noqa: E731
            url, data=complete_multipart_pb.SerializeToString(), headers=header
        )
    )
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        response,
        api_pb.CreateUpdateResponse,
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to confirm model upload: " + response_pb.status)
    return response_pb


def _confirm_model_upload(
    config: ClientConfig, model_id: str, verbose: bool | None = None
) -> api_pb.CreateUpdateResponse:
    """
    Confirm to hub that the upload for the corresponding model is complete.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        ID of the model to update.
    verbose : bool
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    model_pb = api_pb.Model(file_upload_complete=True)
    return update_model_pb(
        config, model_id, model_pb, verbose=verbose, safe_to_retry=True
    )


def create_and_upload_model_pb(
    config: ClientConfig,
    path: str,
    model_pb: api_pb.Model,
    verbose: bool | None = None,
    logger: logging.Logger = logging.getLogger("public_rest_api"),
) -> api_pb.CreateUpdateResponse:
    """
    Create a model object and upload the corresponding model file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    path : str or Path
        Local path to the model file.
    verbose : bool | None
        If true, will show progress bar in standard output.
    logger: Logger
        The logger that should be used for emitting logs.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    verbose = verbose if verbose is not None else config.verbose

    # Create the model object
    cup_create_model = _create_model(
        config,
        model_pb,
        verbose=verbose,
    )
    if not cup_create_model.id or cup_create_model.status:
        return cup_create_model
    model_id = cup_create_model.id

    # Get model upload URL
    file_size = os.path.getsize(path)
    model_multipart_urls = _get_model_multipart_upload_urls(
        config, model_id, file_size, verbose
    )

    # Split the file into multiple parts and upload them to multipart URLs.
    # We first upload individual parts to the individual pre-signed URLs received from the server.
    # Once all the parts have been uploaded, we send the server the list of ETags for each part,
    # so that it can stitch them all together.

    # NOTE: If changing this code, use manual_test_flaky_upload_download as a stress test
    max_part_size = model_multipart_urls.max_part_size
    file_offset = 0
    etags = []
    content_type = api_utils.guess_file_http_content_type(path)

    for index in range(len(model_multipart_urls.urls)):
        if verbose:
            message = f"Uploading {os.path.basename(path)}"
            if len(model_multipart_urls.urls) > 1:
                message += f" part {index + 1} of {len(model_multipart_urls.urls)}"
            print(message)

        if index == len(model_multipart_urls.urls) - 1:
            asset_size = file_size - (max_part_size * index)
        else:
            asset_size = max_part_size

        # Upload the model asset file
        with open(path, "rb", buffering=0) as asset_file:
            asset_file.seek(index * max_part_size)
            etag = api_utils.upload_asset(
                upload_url=model_multipart_urls.urls[index],
                asset_file=asset_file,
                asset_size=asset_size,
                full_file_size=file_size,
                file_field_name="file",
                verbose=verbose,
                upload_method="put",
                content_type=content_type,
                logger=logger,
            )

        assert etag, f"ETag not received in response for part number {index}"

        etags.append(etag)
        file_offset += max_part_size

    # Tell Hub that the model upload is done.
    upload_pb = _complete_model_multipart_upload(
        config, model_id, model_multipart_urls.upload_id, etags
    )
    cup_create_model.id = upload_pb.id
    return cup_create_model


def create_and_upload_model(
    config: ClientConfig,
    path: str,
    model_type: api_pb.ModelType.ValueType,
    name: Optional[str] = None,
    verbose: bool | None = None,
    is_directory: bool = False,
    logger: logging.Logger = logging.getLogger("public_rest_api"),
) -> api_pb.CreateUpdateResponse:
    """
    Create a model object and upload the corresponding model file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    path : str or Path
        Local path to the model file.
    model_type : api_pb.ModelType
        Type of the model.
    name : str
        Name of the model. If None, uses basename of path.
    verbose : bool | None
        If true, will show progress bar in standard output.
    is_directory: bool
        Is this model a directory?

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    if not name:
        name = os.path.basename(path)

    # Create the model object
    model_pb = api_pb.Model(
        name=name,
        model_type=model_type,
        is_directory=is_directory,
    )
    return create_and_upload_model_pb(
        config, path, model_pb, verbose=verbose, logger=logger
    )


def _create_dataset(
    config: ClientConfig,
    name: str,
    permanent: bool = False,
    verbose: bool | None = None,
) -> api_pb.CreateUpdateResponse:
    """
    Create a dataset object.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    name : str
        Name of the dataset.
    permanent: bool
        If true, dataset will be retained permanently.
    verbose : bool
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    dataset_pb = api_pb.Dataset(name=name, permanent=permanent)
    url = api_utils.api_url(config, "datasets")
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        retry_call_with_backoff(
            lambda: create_session().post(
                url, data=dataset_pb.SerializeToString(), headers=header
            )
        ),
        api_pb.CreateUpdateResponse,
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to create dataset: " + response_pb.status)
    return response_pb


def _get_dataset_upload_url(
    config: ClientConfig,
    dataset_id: str,
    verbose: bool | None = None,
    file_size: int | None = None,
) -> api_pb.FileUploadURL:
    """
    Get the URL with which the user should upload the dataset file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    dataset_id : str
        ID of the dataset to query.
    verbose : bool | None
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : FileUploadURL
        Returns a FileUploadURL protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    url = api_utils.api_url(config, f"datasets/{dataset_id}/upload_url")
    params = {"file_size": file_size} if file_size else None
    return api_utils.response_as_protobuf(
        create_session().get(url, headers=header, params=params),
        api_pb.FileUploadURL,
    )


def _confirm_dataset_upload(
    config: ClientConfig, dataset_id: str, verbose: bool | None = None
) -> api_pb.CreateUpdateResponse:
    """
    Confirm to hub that the upload for the corresponding dataset is complete.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    dataset_id : str
        ID of the dataset to query.
    verbose : bool | None
        If true, will show progress bar in standard output.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    header = api_utils.auth_header(config)

    dataset_pb = api_pb.Dataset(file_upload_complete=True)
    url = api_utils.api_url(config, f"datasets/{dataset_id}")
    response_pb: api_pb.CreateUpdateResponse = api_utils.response_as_protobuf(
        retry_call_with_backoff(
            lambda: create_session().patch(
                url, data=dataset_pb.SerializeToString(), headers=header
            )
        ),
        api_pb.CreateUpdateResponse,
    )
    if len(response_pb.id) == 0:
        raise ValueError("Failed to confirm dataset upload: " + response_pb.status)
    return response_pb


def create_and_upload_dataset(
    config: ClientConfig,
    path: str | Path,
    name: str,
    permanent: bool = False,
    verbose: bool | None = None,
    logger: logging.Logger = logging.getLogger("public_rest_api"),
) -> api_pb.CreateUpdateResponse:
    """
    Create dataset and upload the corresponding h5 file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    path : str or Path
        Local path to the model file.
    permanent: bool
        If true, the dataset is retained permanently.
    name : Optional[str]
        Name of the model.
    verbose : bool | None
        If true, will show progress bar in standard output.
    logger: Logger
        The logger that should be used for emitting logs.

    Returns
    -------
    res_pb : CreateUpdateResponse
        Returns a CreateUpdateResponse protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    verbose = verbose if verbose is not None else config.verbose
    file_size = os.path.getsize(path)

    # Create the dataset object
    cup_create_dataset = _create_dataset(config, name, permanent, verbose)
    if not cup_create_dataset.id or cup_create_dataset.status:
        return cup_create_dataset
    dataset_id = cup_create_dataset.id

    # Get dataset upload URL
    dataset_url = _get_dataset_upload_url(config, dataset_id, verbose, file_size)

    # Convert proto fields to a python dict.
    fields = {}
    for k, v in dataset_url.fields.items():
        fields[k] = v

    content_type = api_utils.guess_file_http_content_type(path)

    # Upload the dataset asset file
    with open(path, "rb", buffering=0) as asset_file:
        api_utils.upload_asset(
            upload_url=dataset_url.url,
            asset_file=asset_file,
            asset_size=file_size,
            full_file_size=file_size,
            file_field_name=dataset_url.file_field_name,
            fields=fields,
            verbose=verbose,
            progress_bar_description="Uploading dataset",
            content_type=content_type,
            logger=logger,
        )

    # Tell Hub that the dataset upload is done.
    upload_pb = _confirm_dataset_upload(config, dataset_id, verbose)
    cup_create_dataset.id = upload_pb.id
    return cup_create_dataset


def get_dataset(config: ClientConfig, dataset_id: str) -> api_pb.Dataset:
    """
    Get info about an uploaded dataset.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    dataset_id : str
        Dataset ID.

    Returns
    -------
    dataset_pb : Dataset
        Dataset info as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "datasets", dataset_id)
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header)
    return api_utils.response_as_protobuf(response, api_pb.Dataset, obj_id=dataset_id)


def get_dataset_list(
    config: ClientConfig, offset: int = 0, limit: int | None = None
) -> api_pb.DatasetList:
    """
    Get list of datasets visible to the authenticated user.


    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    offset : int
        Offset the query.
    limit : int | None
        Limit query response size.

    Returns
    -------
    list_pb : DatasetList
        Dataset list as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "datasets")
    url_params = api_utils.offset_limit_url_params(offset, limit)
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header, params=url_params)
    return api_utils.response_as_protobuf(response, api_pb.DatasetList)


def get_model(config: ClientConfig, model_id: str) -> api_pb.Model:
    """
    Get info about an uploaded model.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        Model ID.

    Returns
    -------
    model_pb : Model
        Model info as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "models", model_id)
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header)
    return api_utils.response_as_protobuf(response, api_pb.Model, obj_id=model_id)


def get_model_list(
    config: ClientConfig,
    offset: int = 0,
    limit: int | None = None,
    producer_id: str | None = None,
) -> api_pb.ModelList:
    """
    Get list of models visible to the authenticated user.


    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    offset : int
        Offset the query.
    limit : int
        Limit query response size.

    Returns
    -------
    list_pb : ModelList
        Model list as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "models")
    url_params = api_utils.offset_limit_url_params(offset, limit)
    if producer_id is not None:
        url_params["producer"] = producer_id
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header, params=url_params)
    return api_utils.response_as_protobuf(response, api_pb.ModelList)


def download_model_info(config: ClientConfig, model_id: str) -> api_pb.FileDownloadURL:
    """
    Get download information for a previously uploaded model.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        Model ID.

    Returns
    -------
    response : api_pb.FileDownloadURL
        Download information.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "models", model_id, "download")
    header = api_utils.auth_header(config)
    return api_utils.response_as_protobuf(
        create_session().get(url, headers=header), api_pb.FileDownloadURL
    )


def _download_model(
    url: str,
    filename: str,
    dst_path: str,
    verbose: bool,
    extract_if_zipped: bool = False,
):
    """
    Download model at provided destination path and return path to the model

    Parameters
    ----------
    url : str
        Model URL to download
    filename : str
        File name of model to download
    dst_path : str
        Destination path to download model to
    verbose: bool
        Enable logs
    extract_if_zipped: bool
        If set true, extracts zipped model into provided `dst_path`

    Returns
    -------
    model_path : str
        Path to the saved model file/directory.

    Raises
    ------
        ValueError
            if zipped model does not have single base level directory.
        ValueError
            if zipped model is being extracted to a file.
    """
    extract_zipped_model = extract_if_zipped and filename.endswith(".zip")
    with tempfile.TemporaryDirectory() as tmpdir:
        # If not extracting zipped model,
        # download model at expected destination path itself.
        model_path = api_utils.download_file(
            url,
            filename,
            tmpdir if extract_zipped_model else dst_path,
            verbose,
            extract_if_zipped,
        )

        if not extract_zipped_model:
            return model_path

        if not os.path.isdir(dst_path):
            raise ValueError(
                "Model cannot be extracted to a file. Please provide a directory path."
            )

        # Move extracted model from temporary path to destination path
        dst_path = os.path.join(dst_path, os.path.basename(model_path))
        dst_path, _ = api_utils.get_unique_path(dst_path)

        # get_unique_path creates an empty file.
        if os.path.exists(dst_path) and os.path.isfile(dst_path):
            os.remove(dst_path)

        unzipped_model_content = os.listdir(model_path)
        if len(unzipped_model_content) != 1:
            raise ValueError("Extracted model must contain a single base model asset.")

        # Point to base model directory
        model_path = os.path.join(model_path, unzipped_model_content[0])

        shutil.copytree(model_path, dst_path)
        return dst_path


def download_model(
    config: ClientConfig,
    model_id: str,
    file_path: str,
    verbose: bool | None = None,
    extract_model: bool = False,
) -> str:
    """
    Download a previously uploaded model.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    model_id : str
        Model ID.
    file_path : str
        file location to store model to

    Returns
    -------
    model_path : str
        Path to the saved model file/directory.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    response = download_model_info(config, model_id)
    return _download_model(
        response.url,
        response.filename,
        file_path,
        verbose if verbose is not None else config.verbose,
        extract_model,
    )


def download_compiled_model(
    config: ClientConfig, job_id: str, file_path: str, verbose: bool | None = None
) -> str:
    """
    Download compiled model to file.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_id : str
        Job ID.
    file_path : str
        file location to store compiled model to

    Returns
    -------
    model_path : str
        Path to the saved model file/directory.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    # fetch compiled model
    url = api_utils.api_url(config, "jobs", job_id, "download_compiled_model")
    header = api_utils.auth_header(config)
    response = api_utils.response_as_protobuf(
        create_session().get(url, headers=header), api_pb.FileDownloadURL
    )
    return _download_model(
        response.url,
        response.filename,
        file_path,
        verbose if verbose is not None else config.verbose,
    )


def download_dataset_info(
    config: ClientConfig, dataset_id: str
) -> api_pb.FileDownloadURL:
    """
    Get download information for a previously uploaded dataset.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    dataset_id : str
        Dataset ID.

    Returns
    -------
    response : api_pb.FileDownloadURL
        Download information.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "datasets", dataset_id, "download_data")
    header = api_utils.auth_header(config)
    return api_utils.response_as_protobuf(
        create_session().get(url, headers=header), api_pb.FileDownloadURL
    )


def download_dataset(
    config: ClientConfig, dataset_id: str, file_path: str, verbose: bool | None = None
) -> str:
    """
    Download a previously uploaded dataset.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    dataset_id : str
        Dataset ID.
    file_path : str
        file location to store model to

    Returns
    -------
    file_path : str
        Path to the saved file.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    response = download_dataset_info(config, dataset_id)
    return api_utils.download_file(
        response.url,
        response.filename,
        file_path,
        verbose if verbose is not None else config.verbose,
    )


def get_framework_list(
    config: ClientConfig,
) -> api_pb.FrameworkList:
    """
    Get list of active devices.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.

    Returns
    -------
    framework_list_pb : FrameworkList
       Framework list as protobuf object.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(config, "frameworks")
    header = api_utils.auth_header(config)
    response = create_session().get(url, headers=header, params={})
    return api_utils.response_as_protobuf(response, api_pb.FrameworkList)


def download_job_artifact_info(
    config: ClientConfig,
    job_id: str,
    artifact_type: api_pb.JobArtifactType.ValueType | int,
    attempt_number: Optional[int] = None,
) -> api_pb.FileDownloadURL:
    """
    Get a file name and download URL for a previously uploaded artifact.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_id : str
        Job ID.
    artifact_type: api_pb.JobArtifactType | int
        Type of artifact.
    attempt_number: Optional[int]
        Attempt identifier. If none, use Latest.

    Returns
    -------
    response : api_pb.FileDownloadURL
        Download information.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    url = api_utils.api_url(
        config,
        "jobs",
        job_id,
        "device_runs",
        str(attempt_number) if attempt_number is not None else "latest",
        "artifacts",
        str(int(artifact_type)),
    )
    header = api_utils.auth_header(config)
    return api_utils.response_as_protobuf(
        create_session().get(url, headers=header), api_pb.FileDownloadURL
    )


def download_job_artifact(
    config: ClientConfig,
    job_id: str,
    artifact_type: api_pb.JobArtifactType.ValueType | int,
    file_path: str,
    attempt_number: Optional[int] = None,
    verbose: bool | None = None,
    extract_if_zipped: bool = False,
) -> str:
    """
    Download a previously uploaded model.

    Parameters
    ----------
    config : ClientConfig
        API authentication configuration.
    job_id : str
        Job ID.
    artifact_type: api_pb.JobArtifactType | int
        Type of artifact.
    file_path : str
        file location to store model to
    attempt_number: Optional[int]
        Attempt identifier. If none, use Latest.

    Returns
    -------
    artifact_path : str
        Path to the saved model file/directory.

    Raises
    ------
    APIException
        Raised if request has failed.
    """
    response = download_job_artifact_info(config, job_id, artifact_type, attempt_number)
    return api_utils.download_file(
        response.url,
        response.filename,
        file_path,
        verbose if verbose is not None else config.verbose,
        extract_if_zipped,
    )


__all__ = [
    "api_utils",
    "APIException",
    "ClientConfig",
    "get_auth_user",
    "get_dataset",
    "get_dataset_list",
    "get_device_list",
    "get_framework_list",
    "create_profile_job",
    "create_compile_job",
    "create_link_job",
    "get_job",
    "get_job_list",
    "get_job_results",
    "get_job_summary_list",
    "get_model_vizgraph",
    "create_inference_job",
    "create_and_upload_dataset",
    "create_and_upload_model_pb",
    "create_and_upload_model",
    "update_model_pb",
    "download_model",
    "download_compiled_model",
    "download_dataset_info",
    "download_dataset",
    "get_model",
    "get_model_list",
    "get_sharing",
    "modify_sharing",
    "disable_sharing",
    "SharedEntityType",
    "download_job_artifact_info",
    "download_job_artifact",
]
