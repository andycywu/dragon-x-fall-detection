from __future__ import annotations

import json
import os
import posixpath
import shutil
import sys
import tempfile
import textwrap
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    cast,
    overload,
)
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile

import deprecation  # type: ignore
import h5py
import numpy as np
import requests
from packaging.version import Version
from typing_extensions import assert_never

from . import api_status_codes, api_utils
from . import public_api_pb2 as api_pb
from . import public_rest_api as api
from .public_rest_api import APIException, ClientConfig, DatasetEntries, InputSpecs
from .util.dataset_entries_converters import (
    dataset_entries_to_h5,
    h5_to_dataset_entries,
)
from .util.zipped_model import make_zipped_model_compatible, unzip_model, zip_model

SUPPORT_EMAIL = "ai-hub-support@qti.qualcomm.com"

if TYPE_CHECKING:
    # Evaluate to False in general. Only import to resolve Sphinx autodoc
    # typehints forward declaration warnings
    import onnx
    import torch

MISSING_METRIC_VALUE: Any = None

IS_WINDOWS = sys.platform in ["win32", "msys", "cygwin"]

ASSEMBLE_JSON_FILE = "assemble.json"
ESPRESSO_NET_FILE = "model.espresso.net"
TRTMODEL_METADATA_PATHS = ["trt_metadata.json", "trt_metadata.pb"]
# Maximum amount of time to automatically retry on rate-limiting before giving up
# and raising an exception to the user.
RATE_LIMIT_RETRY_TIMEOUT = 10  # minutes


def _dev_to_dev_pb(device: Device):
    dev_pb = api_pb.Device(name=device.name, os=device.os)
    for attr in device.attributes:
        dev_pb.attributes.append(attr)
    return dev_pb


def _devs_to_devs_pb(devices: List[Device]):
    devices_pb = api_pb.DeviceList(total_query_count=len(devices))
    for dev in devices:
        devices_pb.devices.append(_dev_to_dev_pb(dev))
    return devices_pb


def _dev_pb_to_dev(dev_pb: api_pb.Device):
    attrs = [a for a in dev_pb.attributes]
    device = Device(dev_pb.name, dev_pb.os, attrs)
    return device


def _devs_pb_to_devs(devices_pb: api_pb.DeviceList):
    devices = []
    for dev in devices_pb.devices:
        devices.append(_dev_pb_to_dev(dev))
    return devices


def _profile_pb_to_python_dict(profile_pb: api_pb.ProfileDetail) -> Dict[str, Any]:
    layer_details = []
    for layer_detail_pb in profile_pb.layer_details:
        layer_data: Dict[str, Union[str, int]] = {
            "name": layer_detail_pb.name,
            "type": layer_detail_pb.layer_type_name,
            # Remove the compute unit enum prefix (COMPUTE_UNIT_).
            "compute_unit": api_pb.ComputeUnit.Name(layer_detail_pb.compute_unit)[
                len("COMPUTE_UNIT_") :
            ],
        }
        if layer_detail_pb.HasField("execution_time"):
            layer_data["execution_time"] = layer_detail_pb.execution_time
        if layer_detail_pb.HasField("execution_cycles"):
            layer_data["execution_cycles"] = layer_detail_pb.execution_cycles
        layer_details.append(layer_data)

    execution_summary: Dict[str, int | Tuple[int, int] | List[int] | None] = {}

    if profile_pb.major_version == 1:
        execution_summary = {
            "estimated_inference_time": profile_pb.execution_time,
            "estimated_inference_peak_memory": profile_pb.after_execution_peak_memory,
            "first_load_time": profile_pb.cold_load_time,
            "first_load_peak_memory": profile_pb.after_cold_load_peak_memory,
            "warm_load_time": profile_pb.warm_load_time,
            "warm_load_peak_memory": profile_pb.after_warm_load_peak_memory,
            "compile_time": profile_pb.compile_time,
            "compile_peak_memory": profile_pb.after_compile_peak_memory,
        }

        if profile_pb.minor_version >= 1:
            stage_memories: List[Tuple[str, api_pb.ProfileDetail.MemoryUsage]] = [
                ("compile", profile_pb.compile_memory),
                ("first_load", profile_pb.cold_load_memory),
                ("warm_load", profile_pb.warm_load_memory),
                ("inference", profile_pb.execution_memory),
            ]
            for stage, memory in stage_memories:
                # ByteSize() > 0 means the field was explicitly set
                if memory.ByteSize() > 0:
                    increase = memory.increase
                    peak = memory.peak
                    execution_summary[f"{stage}_memory_increase_range"] = (
                        increase.lower,
                        increase.upper,
                    )
                    execution_summary[f"{stage}_memory_peak_range"] = (
                        peak.lower,
                        peak.upper,
                    )
                else:
                    execution_summary[f"{stage}_memory_increase_range"] = (
                        MISSING_METRIC_VALUE
                    )
                    execution_summary[f"{stage}_memory_peak_range"] = (
                        MISSING_METRIC_VALUE
                    )
        if profile_pb.minor_version >= 2:
            stage_all_times: List[Tuple[str, List[int]]] = [
                ("compile", [t for t in profile_pb.all_compile_times]),
                ("first_load", [t for t in profile_pb.all_cold_load_times]),
                ("warm_load", [t for t in profile_pb.all_warm_load_times]),
                ("inference", [t for t in profile_pb.all_execution_times]),
            ]
            for stage, all_times in stage_all_times:
                execution_summary[f"all_{stage}_times"] = all_times

    else:
        execution_summary = {
            "estimated_inference_time": profile_pb.execution_time,
            "estimated_inference_peak_memory": MISSING_METRIC_VALUE,
            "first_load_time": profile_pb.load_time,
            "first_load_peak_memory": MISSING_METRIC_VALUE,
            "warm_load_time": MISSING_METRIC_VALUE,
            "warm_load_peak_memory": MISSING_METRIC_VALUE,
            "compile_time": MISSING_METRIC_VALUE,
            "compile_peak_memory": profile_pb.peak_memory_usage,
            "compile_memory_increase_range": MISSING_METRIC_VALUE,
            "compile_memory_peak_range": MISSING_METRIC_VALUE,
            "first_load_memory_increase_range": MISSING_METRIC_VALUE,
            "first_load_memory_peak_range": MISSING_METRIC_VALUE,
            "warm_load_memory_increase_range": MISSING_METRIC_VALUE,
            "warm_load_memory_peak_range": MISSING_METRIC_VALUE,
            "inference_memory_increase_range": MISSING_METRIC_VALUE,
            "inference_memory_peak_range": MISSING_METRIC_VALUE,
        }

    return {
        "execution_summary": execution_summary,
        "execution_detail": layer_details,
    }


def _class_repr_print(obj, fields) -> str:
    """
    Display a class repr according to some simple rules.

    Parameters
    ----------
    obj: Object to display a repr for
    fields: List[str | (str, str)]
    """

    # Record the max_width so that if width is not provided, we calculate it.
    max_width = len("Class")

    # Add in the section header.
    section_title = obj.__class__.__name__
    out_fields = [section_title, "-" * len(section_title)]

    # Add in all the key-value pairs
    for f in fields:
        if isinstance(f, tuple):
            out_fields.append(f)
            max_width = max(max_width, len(f[0]))
        else:
            out_fields.append((f, getattr(obj, f)))
            max_width = max(max_width, len(f))

    # Add in the empty footer.
    out_fields.append("")

    # Now, go through and format the key_value pairs nicely.
    def format_key_pair(key, value) -> str:
        return key.ljust(max_width, " ") + " : " + str(value)

    out_fields = [s if isinstance(s, str) else format_key_pair(*s) for s in out_fields]
    return "\n".join(out_fields)


def requires_compilation(model_type: SourceModelType) -> bool:
    return (
        model_type == SourceModelType.TORCHSCRIPT
        or model_type == SourceModelType.AIMET_ONNX
    )


def allows_compilation(model_type: SourceModelType) -> bool:
    return model_type == SourceModelType.ONNX or requires_compilation(model_type)


def _get_source_model_type_from_model_type(model_type: api_pb.ModelType.ValueType):
    if model_type not in api_pb.ModelType.values():
        model_type = api_pb.ModelType.MODEL_TYPE_UNSPECIFIED
    return SourceModelType(model_type)


def _is_in_zip(zip: ZipFile, filename: str) -> bool:
    return filename in zip.namelist()


def _assert_is_valid_zipped_model(filepath: str) -> None:
    # Valid if one of following is true:
    # 1. is a valid Runtime model:
    #   * name is <filepath>/foo.trtmodel
    #   * <filepath>/foo.trtmodel/trt_metadata.[json|pb]
    # 2. has mlpackage
    #    <filepath>/foo.mlpackage/
    # 3. has one of following file (valid .mlmodelc)
    #   a. <filepath>/foo.mlmodelc/assemble.json
    #   b. <filepath>/foo.mlmodelc/model.espresso.net
    #   c. <filepath>/foo.mlmodelc/model0/model.espresso.net
    def __get_model_dir(
        model_type: SourceModelType, zippedNames: List[str]
    ) -> Optional[str]:
        """Is there exactly one subdirectory with the correct extension for the given model type?"""
        ext_incl_zip = EXTENSIONS_BY_MODEL_TYPE[model_type]
        suffix = ext_incl_zip[:-4]
        suffix_with_trailing_slash = suffix + "/"
        model_subdirs = [
            dname for dname in zippedNames if dname.endswith(suffix_with_trailing_slash)
        ]
        if not model_subdirs:
            # Zip files do not have to contain separate entries for
            # directories. If this is the case, model_subdirs is empty and we
            # need to infer the sub directories from files.
            def _get_root(path):
                head, tail = os.path.split(path)
                if head == "/" or not head:
                    return tail
                else:
                    return _get_root(head)

            model_subdirs = list(set([_get_root(dname) for dname in zippedNames]))
            model_subdirs = [x for x in model_subdirs if x.endswith(suffix)]
        if len(model_subdirs) > 1:
            raise UserError(
                f"Invalid zipped model contains multiple '{suffix}' directories."
            )
        return model_subdirs[0] if len(model_subdirs) == 1 else None

    with ZipFile(filepath, "r") as zippedModel:
        zippedNames = zippedModel.namelist()
        if __get_model_dir(SourceModelType.AIMET_ONNX, zippedNames) is not None:
            return
        if __get_model_dir(SourceModelType.MLPACKAGE, zippedNames) is not None:
            # Is a valid mlpackage zipped model
            return
        if __get_model_dir(SourceModelType.ONNX, zippedNames) is not None:
            return

        trtmodel_dir = __get_model_dir(SourceModelType.TETRART, zippedNames)
        if trtmodel_dir is not None:
            metadata_paths = [
                os.path.join(trtmodel_dir, x) for x in TRTMODEL_METADATA_PATHS
            ]
            if any([_is_in_zip(zippedModel, p) for p in metadata_paths]):
                return
            raise UserError("Invalid '.trtmodel' bundle has no metadata file.")

        # Check if it's a valid mlmodelc zipped model
        # Find .mlmodelc directory
        mlmodelc_dir = __get_model_dir(SourceModelType.MLMODELC, zippedNames)
        if mlmodelc_dir is None:
            raise UserError(
                "Incorrect zipped model .zip provided."
                " Must have one root level '.trtmodel', '.mlmodelc', or '.mlpackage' directory."
            )

        # Case 3. a): <filepath>/foo.mlmodelc/assemble.json
        if _is_in_zip(zippedModel, os.path.join(mlmodelc_dir, ASSEMBLE_JSON_FILE)):
            return
        # Search in the .mlmodelc directory
        # Case 3. b): <filepath>/foo.mlmodelc/model.espresso.net
        if _is_in_zip(zippedModel, os.path.join(mlmodelc_dir, ESPRESSO_NET_FILE)):
            return
        # Case 3. c): <filepath>/foo.mlmodelc/model0/model.espresso.net
        if _is_in_zip(
            zippedModel, os.path.join(mlmodelc_dir, "model0", ESPRESSO_NET_FILE)
        ):
            return

        # No match in each of the 3 supported types
        raise UserError(
            f"Incorrect mlmodelc.zip provided. Neither {ESPRESSO_NET_FILE} nor {ASSEMBLE_JSON_FILE} found."
        )


def _make_zipped_model_compatible(
    source_path: str, archive_path: str, model_ext: str
) -> str:
    """
    If source_path is a directory, zip it up.
    If source_path is a zip, ensure only one model asset is present in zip.

    Parameters
    ----------
    source_path:
        A model zip archive or directory.
    archive_path:
        Path of archive to create if source path is a directory.

    Returns
    -------
    model_archive_path :
        Path to a zip file containing the source model.

    Raises
    ------
    UserError
        if source_path is a directory but not a model
    UserError
        if provided zipped archive has no or more than one model asset at base path
    """
    if os.path.isdir(source_path):
        if not source_path.endswith(model_ext):
            raise UserError(
                f"Provided source path must point to {model_ext} dir. "
                f"Provided {source_path}."
            )

        return zip_model(
            str(Path(archive_path).with_suffix("")),
            source_path,
        )
    # Make existing archived model compatible with hub
    return make_zipped_model_compatible(source_path, archive_path)


def _is_apple_version_supported(
    device_attributes: Union[str, List[str]],
    os_version: str,
    target_major_ios_version: int,
) -> bool:
    """
    Returns True if given `os_version` belongs to the generation defined by the
    `target_major_ios_version`. Note, if this is set to iOS 16, then macOS 13
    will also return True, since they are generationally equivalent.
    """

    if os_version == "":
        return False
    os_major = Version(os_version).major

    if not isinstance(device_attributes, list):
        device_attributes = [device_attributes]

    # .mlpackage is supported on
    #  - iOS15+
    #  - macOS12+
    # Ref: https://github.com/apple/coremltools/blob/801c705340093cb2d61ffeaf1244408194b4f89e/coremltools/converters/mil/_deployment_compatibility.py#L17
    if "os:ios" in device_attributes:
        return os_major >= target_major_ios_version
    if "os:macos" in device_attributes:
        return os_major >= target_major_ios_version - 3
    return False


def _is_mlpackage_supported(
    device_attributes: Union[str, List[str]], os_version: str, version_buffer: int = 0
) -> bool:
    """
    Returns True if mlpackage is supported for given device i.e.
        - iPhone/iPad with iOS15+
        - mac with macOS12+
    Otherwise, False

    ref: https://github.com/apple/coremltools/blob/801c705340093cb2d61ffeaf1244408194b4f89e/coremltools/converters/mil/_deployment_compatibility.py#L17
    """
    return _is_apple_version_supported(
        device_attributes, os_version, target_major_ios_version=15
    )


## ERROR HANDLING ##
class Error(Exception):
    """
    Base class for all exceptions explicitly thrown by the API.

    Other exception may be raised from dependent third party packages.
    """

    def __init__(self, message):
        super().__init__(message)


class InternalError(Error):
    """
    Internal API failure; please contact ai-hub-support@qti.qualcomm.com for assistance.
    """

    def __init__(self, message):
        super().__init__(message)


class UserError(Error):
    """
    Something in the user input caused a failure; you may need to adjust your input.
    """

    def __init__(self, message):
        super().__init__(message)


class RateLimitedError(Error):
    """
    The operation was rate-limited by the server.
    """

    pass


def _visible_textbox(text: str) -> str:
    """
    Letting exceptions terminate a python program is a cluttered way to give
    user feedback. This box is to draw attention to action items for users.
    """
    width = 70
    text = textwrap.dedent(text).strip()
    wrapper = textwrap.TextWrapper(width=width - 4)
    header = "\n┌" + "─" * (width - 2) + "┐\n"
    footer = "\n└" + "─" * (width - 2) + "┘"

    lines = ["| " + line.ljust(width - 4) + " |" for line in wrapper.wrap(text)]
    return header + "\n".join(lines) + footer


# Retry api calls with exponential back-off and a max duration.
def _api_call_with_retry(api_func, *args, **kwargs) -> Any:
    time_between_retries = 20  # seconds
    max_time_between_retries = 60  # seconds
    total_time_spent_retrying = 0  # seconds

    try:
        response_pb = _api_call(api_func, *args, **kwargs)
    except RateLimitedError as e:
        print(
            _visible_textbox(
                f"{e} Retrying periodically until your request succeeds. Interrupt this and pass retry=False if you don't want this automatic retry."
            )
        )
        while True:
            print(f"Retrying after {time_between_retries} seconds.")
            time.sleep(time_between_retries)
            total_time_spent_retrying += time_between_retries

            try:
                response_pb = _api_call(api_func, *args, **kwargs)
                break
            except RateLimitedError:
                if total_time_spent_retrying > RATE_LIMIT_RETRY_TIMEOUT * 60:
                    raise RateLimitedError(
                        f"Could not create a job after retrying for {RATE_LIMIT_RETRY_TIMEOUT} minutes. Please try again later."
                    ) from None

                time_between_retries = min(
                    time_between_retries * 2, max_time_between_retries
                )
                continue

    return response_pb


def _raise_if_hub_user_error(e: APIException, config: Optional[ClientConfig]):
    def _get_exception_string(exc) -> str:
        # for some 4xx exceptions the actual message is embedded in the exception
        message = str(exc)
        try:
            message = json.loads(message)["detail"]
        finally:
            return message

    config_path = api_utils.get_config_path(expanduser=False)
    web_url = config.web_url if config else api.DEFAULT_HUB_WEB_URL
    account_page_link_text = f": {web_url}/account/"

    if e.status_code == api_status_codes.API_CONFIGURATION_MISSING_FIELDS:
        long_message = _visible_textbox(
            f"Your {config_path} file is missing required fields. "
            "Please go to your Account page for help configuring qai-hub"
            + account_page_link_text
        )
        raise UserError(f"Failed to load configuration file.\n{long_message}") from None
    elif e.status_code == api_status_codes.HTTP_401_UNAUTHORIZED:
        long_message = _visible_textbox(
            "Failure to authenticate is likely caused by a bad or outdated API "
            f"token in your {config_path} file. Please go to your Account page "
            "to view your current token" + account_page_link_text
        )
        raise UserError(f"Failed to authenticate.\n{long_message}") from None
    elif e.status_code == api_status_codes.HTTP_404_NOT_FOUND:
        raise UserError(str(e)) from None
    elif e.status_code == api_status_codes.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
        raise UserError(
            _get_exception_string(e)
            + f"Please contact support at {SUPPORT_EMAIL} if you need assistance."
        )
    elif e.status_code == api_status_codes.HTTP_426_UPGRADE_REQUIRED:
        raise UserError(_visible_textbox(_get_exception_string(e))) from None
    elif e.status_code == api_status_codes.HTTP_429_TOO_MANY_REQUESTS:
        raise RateLimitedError(_get_exception_string(e)) from None
    elif e.status_code and e.status_code >= 400 and e.status_code < 500:
        raise UserError(_get_exception_string(e)) from None


def _is_hub_request(api_url: Optional[str], url: Optional[str]):
    # when we don't have enough info, assume Hub
    return url.startswith(api_url) if api_url and url else True


def _raise_internal_error(
    message: str,
    cause: Exception,
    api_url: Optional[str],
    url: Optional[str],
    contact_support=False,
):
    is_hub_request = _is_hub_request(api_url, url)

    if is_hub_request:
        service = "Qualcomm AI Hub"
    else:
        request_url = urlparse(url)
        service = str(request_url.netloc)

    long_message = message.format(service=service)

    if is_hub_request and api_url is not None:
        long_message += f" Please visit {api_url} to check the service's status."

    if contact_support:
        long_message += f" Please contact support at {SUPPORT_EMAIL}."

    raise InternalError(
        f"Internal API failure.\n{_visible_textbox(long_message)}"
    ) from cause


def _extract_exception_url(e: requests.exceptions.RequestException):
    return (
        e.request.url if e.request is not None and e.request.url is not None else None
    )


def _api_call(api_func, *args, **kwargs) -> Any:
    """
    Wrapper to re-raise the most common API exceptions appropriate for the
    client.
    """

    config = args[0] if args and isinstance(args[0], ClientConfig) else None
    api_url = config.api_url if config else None

    try:
        return api_func(*args, **kwargs)
    except requests.exceptions.RetryError as e:
        url = _extract_exception_url(e)
        if (
            str(e.args[0].reason) == "too many 502 error responses"
            or str(e.args[0].reason) == "too many 503 error responses"
        ):
            _raise_internal_error(
                "{service} is unavailable right now.", e, api_url, url
            )
        else:
            _raise_internal_error(
                "{service} reported errors. ",
                e,
                api_url,
                url,
                contact_support=_is_hub_request(api_url, url),
            )
    except requests.exceptions.ConnectionError as e:
        url = _extract_exception_url(e)
        _raise_internal_error("Could not connect to {service}.", e, api_url, url)
    except requests.exceptions.Timeout as e:
        url = _extract_exception_url(e)
        _raise_internal_error(
            "Timeout occurred while communicating with {service}.", e, api_url, url
        )
    except api.APIException as e:
        url = e.url
        is_hub_request = _is_hub_request(api_url, url)

        if is_hub_request:
            _raise_if_hub_user_error(e, config)

        if (
            e.status_code == api_status_codes.HTTP_502_BAD_GATEWAY
            or e.status_code == api_status_codes.HTTP_503_SERVICE_UNAVAILABLE
        ):
            _raise_internal_error(
                "{service} is unavailable right now.", e, api_url, url
            )
        elif e.status_code and e.status_code >= 500:
            _raise_internal_error(
                "{service} reported errors.",
                e,
                api_url,
                url,
                contact_support=is_hub_request,
            )
        elif not is_hub_request:
            # 4xx or other errors from another service like AWS means a bug in AI Hub code
            _raise_internal_error(str(e), e, api_url, url, contact_support=True)
        else:
            # Re-raise, let the function catch it, or let it bubble up
            raise


## DATASET ##


class Dataset:
    """

    A dataset should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.upload_dataset`,  :py:func:`qai_hub.get_dataset` or :py:func:`qai_hub.get_datasets`.

    Attributes
    ----------
    dataset_id : str
        The dataset ID.
    creation_time : datetime
        The time this dataset was created.
    dataset_name : str
        Name of this dataset
    expiration_time: datetime
        The time this dataset will expire.
    """

    def __init__(
        self,
        owner: Client,
        dataset_id: str,
        creation_time: datetime,
        expiration_time: datetime | None,
        dataset_name: str,
        verbose: bool,
        data: DatasetEntries | None = None,
    ):
        self._owner = owner
        self.name = dataset_name
        self.dataset_id = dataset_id
        self.creation_time = creation_time
        self.expiration_time = expiration_time
        self.verbose = verbose
        self._data = data

    @overload
    def download(self) -> DatasetEntries: ...

    @overload
    def download(self, filename: str) -> str: ...

    @overload
    def download(self, filename: str | None) -> DatasetEntries | str: ...

    def download(self, filename: str | None = None) -> DatasetEntries | str:
        """
        Downloads the dataset entries either to memory or to an h5py (.h5) file.

        Parameters
        ----------
        filename:
            If filename is specified the dataset is downloaded to file, otherwise to memory.
            If the filename doesn't end with the correct file extension,
            the appropriate file extension is added to the name.

        Returns
        -------
        : DatasetEntries | str
            Loaded data instance or file name.
        """
        if self._data is None:
            if self.is_expired():
                raise UserError(f"Cannot download expired dataset. {self}")

            if filename is not None:
                download_file = filename
            else:
                # delete=False to be compatible with Windows
                with tempfile.NamedTemporaryFile(delete=False) as file:
                    download_file = file.name
                # Close the file to avoid double-open on Windows

            download_file = _api_call(
                api.download_dataset,
                self._owner.config,
                self.dataset_id,
                file_path=download_file,
                verbose=self.verbose,
            )
            if filename is not None:
                print(f"Downloaded dataset to {download_file}")
                return download_file

            with h5py.File(download_file, "r") as h5f:
                self._data = h5_to_dataset_entries(h5f)

            os.remove(download_file)

            return self._data
        else:
            if filename is None:
                return self._data

            if os.path.isdir(filename):
                # Grab filename from the API and append it to the path.
                dataset_info = _api_call(
                    api.download_dataset_info, self._owner.config, self.dataset_id
                )
                filename = os.path.join(filename, dataset_info.filename)

                # Append suffix if necessary, so we don't overwrite.
                filename, _ = api_utils.get_unique_path(filename)
            elif not filename.endswith(".h5"):
                filename += ".h5"

            with h5py.File(filename, "w") as h5f:
                dataset_entries_to_h5(self._data, h5f)

            assert isinstance(filename, str)
            print(f"Downloaded dataset to {filename}")
            return filename

    def __str__(self) -> str:
        return f"Dataset(id='{self.dataset_id}', name='{self.name}', expiration_time='{self.expiration_time}')"

    def get_expiration_status(self) -> str:
        if self.is_expired():
            return "Expired"
        else:
            return "Not Expired"

    def is_expired(self) -> bool:
        return datetime.now() > self.expiration_time if self.expiration_time else False

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "dataset_id",
                "name",
                "creation_time",
                ("expiration_status", self.get_expiration_status()),
            ],
        )

    def get_sharing(self) -> List[str]:
        """
        Get the list of email addresses of users that this dataset has been shared with.
        """
        response = _api_call(
            api.get_sharing,
            self._owner.config,
            self.dataset_id,
            api.SharedEntityType.DATASET,
        )
        return response.email

    def disable_sharing(self) -> None:
        """
        Disable all sharing for this dataset.

        Note that the dataset will still be accessible by users with which related job(s) are shared.
        """
        _api_call(
            api.disable_sharing,
            self._owner.config,
            self.dataset_id,
            api.SharedEntityType.DATASET,
        )

    def modify_sharing(
        self, add_emails: List[str] = [], delete_emails: List[str] = []
    ) -> None:
        """
        Modifies the list of users that the dataset is shared with.
        """
        if not add_emails and not delete_emails:
            raise UserError(
                "Either add_emails or delete_emails must be specified and non-empty"
            )

        if not isinstance(add_emails, list) or not isinstance(delete_emails, list):
            raise UserError("add_emails and delete_emails must both be lists")

        _api_call(
            api.modify_sharing,
            self._owner.config,
            self.dataset_id,
            api.SharedEntityType.DATASET,
            add_emails,
            delete_emails,
        )


## DEVICES ##


def _validate_device_params(
    name: str, os: str, attributes: Union[str, List[str]]
) -> None:
    if name == "" and os != "" and attributes == []:
        raise ValueError(
            "Cannot filter devices when provided only an OS version. Please provide a device name and/or attributes."
        )


@dataclass
class Device:
    """
    Create a target device representation.

    The actual target device selection is done when a job is submitted.

    Attributes
    ----------
    name:str
        A name must be an exact match with an existing device, e.g. `"Samsung Galaxy S23"`.
    os:str
        The OS can either be empty, a specific version, or a version interval. If a
        specific vesion is specified (`"15.2"`), it must be an exact match with an
        existing device.  An interval can be used to get a range of OS
        versions. The OS interval must be a
        `right-open mixed interval <https://simple.wikipedia.org/wiki/Interval_(mathematics)#Mixed_Intervals>`_.
        Either side of an interval can be empty, e.g. `"[12,13)"` or `"[12,)"`.
        If the OS is empty, this device represents the device with the latest OS version
        selected from all devices compatible with the name and attriutes.
    attributes: str|List[str]
        Additional device attributes. The selected device is compatible with all
        attributes specified. Supported attributes are:

            * ``"format:phone"``
            * ``"format:tablet"``
            * ``"framework:tflite"``
            * ``"framework:qnn"``
            * ``"framework:onnx"``
            * ``"vendor:google"``
            * ``"vendor:samsung"``
            * ``"vendor:xiaomi"``
            * ``"vendor:oneplus"``

            * ``"os:android"``

            * ``"chipset:qualcomm-snapdragon-429"``
            * ``"chipset:qualcomm-snapdragon-670"``
            * ``"chipset:qualcomm-snapdragon-678"``
            * ``"chipset:qualcomm-snapdragon-730"``
            * ``"chipset:qualcomm-snapdragon-730g"``
            * ``"chipset:qualcomm-snapdragon-765g"``
            * ``"chipset:qualcomm-snapdragon-778g"``
            * ``"chipset:qualcomm-snapdragon-845"``
            * ``"chipset:qualcomm-snapdragon-855"``
            * ``"chipset:qualcomm-snapdragon-865+"``
            * ``"chipset:qualcomm-snapdragon-888"``
            * ``"chipset:qualcomm-snapdragon-8gen1"``
            * ``"chipset:qualcomm-snapdragon-8gen2"``

    Examples
    --------
    ::

        import qai_hub as hub

    Select a target device for Samsung Galaxy S23 with specifically Android 13:

        device = hub.Device("Samsung Galaxy S23", "13")

    Select a target device with OS major version 11::

        device = hub.Device(os="[11,12)", attributes="os:android")

    Select a target device with a Snapdragon 8 Gen 2 chipset::

        device = hub.Device(attributes="chipset:qualcomm-snapdragon-8gen2")

    Fetch a list of devices using :py:func:`~qai_hub.get_devices`::

        devices = hub.get_devices()
    """

    name: str = ""
    os: str = ""
    attributes: str | List[str] = cast(
        Union[str, List[str]], field(default_factory=list)
    )

    def __post_init__(self):
        _validate_device_params(self.name, self.os, self.attributes)


## FRAMEWORKS ##


@dataclass
class Framework:
    """
    A representation of an ML framework.

    Attributes
    ----------
    name:str
        The name of the ML framework (i.e., "QAIRT").
    api_version:str
        The version of the specified ML framework compatible with AI Hub APIs (i.e., "2.28").
    api_tags: List[str]
        Additional tags that describe the framework:
            * ``"default"``: the default version of QNN used by AI Hub.
            * ``"latest"``: the newest, most recent version of QNN available on AI Hub.
    full_version:str
        The full version of the specified ML framework (i.e., "2.28.0").
    """

    name: str = ""
    api_version: str = ""
    api_tags: List[str] = cast(List[str], field(default_factory=list))
    full_version: str = ""


## MODELS ##

SourceModel = Union[
    "torch.jit.TopLevelTracedModule",  # type: ignore # noqa: F821 (imported conditionally)
    "torch.jit.ScriptModule",  # type: ignore # noqa: F821 (imported conditionally)
    "onnx.ModelProto",  # type: ignore # noqa: F821 (imported conditionally)
    bytes,
]

TargetModel = bytes  # for QNN, ONNX, and TF-Lite


# Mirrors api_pb.ModelType
class SourceModelType(Enum):
    """
    Set of supported input model types.
    """

    UNRECOGNIZED_MODEL_TYPE = api_pb.ModelType.MODEL_TYPE_UNSPECIFIED
    TORCHSCRIPT = api_pb.ModelType.MODEL_TYPE_TORCHSCRIPT
    MLMODEL = api_pb.ModelType.MODEL_TYPE_MLMODEL
    TFLITE = api_pb.ModelType.MODEL_TYPE_TFLITE
    MLMODELC = api_pb.ModelType.MODEL_TYPE_MLMODELC
    ONNX = api_pb.ModelType.MODEL_TYPE_ONNX
    MLPACKAGE = api_pb.ModelType.MODEL_TYPE_MLPACKAGE
    TETRART = api_pb.ModelType.MODEL_TYPE_TETRART
    QNN_LIB_AARCH64_ANDROID = api_pb.ModelType.MODEL_TYPE_QNN_LIB_AARCH64_ANDROID
    QNN_LIB_X86_64_LINUX = api_pb.ModelType.MODEL_TYPE_QNN_LIB_X86_64_LINUX
    QNN_CONTEXT_BINARY = api_pb.ModelType.MODEL_TYPE_QNN_CONTEXT_BINARY
    AIMET_ONNX = api_pb.ModelType.MODEL_TYPE_AIMET_ONNX
    QNN_DLC = api_pb.ModelType.MODEL_TYPE_QNN_DLC

    @classmethod
    def _missing_(cls, value):
        return SourceModelType.UNRECOGNIZED_MODEL_TYPE


# Mirrors api_pb.ModelMetadataKey
class ModelMetadataKey(Enum):
    """
    Model metadata key.
    """

    UNSPECIFIED = api_pb.ModelMetadataKey.MODEL_METADATA_KEY_UNSPECIFIED
    QNN_SDK_VERSION = api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_SDK_VERSION
    QNN_SDK_VARIANT = api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_SDK_VARIANT
    QAIRT_SDK_VERSION = api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QAIRT_SDK_VERSION
    QNN_CONTEXT_BIN_GRAPH_NAMES = (
        api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_CONTEXT_BIN_GRAPH_NAMES
    )
    QNN_CONTEXT_BIN_HEXAGON_VERSION = (
        api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_CONTEXT_BIN_HEXAGON_VERSION
    )
    QNN_CONTEXT_BIN_SOC_MODEL = (
        api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_CONTEXT_BIN_SOC_MODEL
    )
    QNN_CONTEXT_BIN_BACKEND = (
        api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_CONTEXT_BIN_BACKEND
    )
    QNN_CONTEXT_BIN_VTCM = (
        api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_CONTEXT_BIN_VTCM
    )
    QNN_CONTEXT_BIN_OPTIMIZATION_LEVEL = (
        api_pb.ModelMetadataKey.MODEL_METADATA_KEY_QNN_CONTEXT_BIN_OPTIMIZATION_LEVEL
    )

    @classmethod
    def _missing_(cls, value):
        return ModelMetadataKey.UNSPECIFIED


class QuantizeDtype(Enum):
    """Supported data types when submitting quantize jobs."""

    INT8 = api_pb.QuantizeDtype.QUANTIZE_DTYPE_INT8
    INT16 = api_pb.QuantizeDtype.QUANTIZE_DTYPE_INT16
    INT4 = api_pb.QuantizeDtype.QUANTIZE_DTYPE_INT4


# We do not support
# api_pb.ModelType.MODEL_TYPE_DEPRECATED_UNTRACED_TORCHSCRIPT
# api_pb.ModelType.MODEL_TYPE_AIMET_PT
# api_pb.ModelType.MODEL_TYPE_ORT
assert len(SourceModelType) == len(api_pb.ModelType.items()) - 3

MODEL_TYPES_BY_EXTENSION = {
    ".bin": SourceModelType.QNN_CONTEXT_BINARY,
    ".mlmodel": SourceModelType.MLMODEL,
    ".mlmodelc": SourceModelType.MLMODELC,
    ".mlpackage": SourceModelType.MLPACKAGE,
    ".onnx": SourceModelType.ONNX,
    ".pt": SourceModelType.TORCHSCRIPT,
    ".pth": SourceModelType.TORCHSCRIPT,
    ".tflite": SourceModelType.TFLITE,
    ".trtmodel": SourceModelType.TETRART,
    ".aimet": SourceModelType.AIMET_ONNX,
    ".dlc": SourceModelType.QNN_DLC,
}


def _validate_onnx_model_dir(onnx_dir: str) -> None:
    files = os.listdir(onnx_dir)
    if len(files) != 2:
        raise UserError(
            f"ONNX model directory '{onnx_dir}' must contain exactly 2 files."
        )
    onnx_files = [f for f in files if f.endswith(".onnx")]
    if len(onnx_files) != 1:
        raise UserError(
            f"ONNX model directory '{onnx_dir}' must contain exactly one .onnx file."
        )
    onnx_name = os.path.splitext(onnx_files[0])[0]
    for suffix in [".bin", ".data"]:
        data_files = [f for f in files if f.endswith(suffix)]
        if len(data_files) == 1:
            if os.path.splitext(data_files[0])[0] != onnx_name:
                raise UserError(
                    f".onnx file and {suffix} file in ONNX model directory '{onnx_dir}' must have the same basename."
                )
            return
    raise UserError(
        f"ONNX model directory '{onnx_dir}' must contain a .bin or a .data file."
    )


def _validate_aimet_model_dir(aimet_dir: str) -> None:
    files = os.listdir(aimet_dir)
    onnx_files = [f for f in files if f.endswith(".onnx")]
    if len(onnx_files) != 1:
        raise UserError(
            f"AIMET model directory '{aimet_dir}' must contain exactly one .onnx file."
        )
    encoding_files = [f for f in files if f.endswith(".encodings")]
    if len(encoding_files) != 1:
        raise UserError(
            f"AIMET model directory '{aimet_dir}' must contain exactly one .encodings file."
        )
    weight_files = [f for f in files if f.endswith(".data")]
    if len(weight_files) > 1:
        raise UserError(
            f"AIMET model directory '{aimet_dir}' can contain at most one weight file."
        )
    if len(files) - len(weight_files) != 2:
        raise UserError(
            f"AIMET model directory '{aimet_dir}' must contain exactly {2 + len(weight_files)} files."
        )


def _filepath_to_model_type(path: str) -> SourceModelType | None:
    suffix = os.path.splitext(path)[1]
    if suffix not in MODEL_TYPES_BY_EXTENSION:
        return None
    if os.path.isdir(path):
        # high level validation for some directory based models
        if suffix == ".onnx":
            _validate_onnx_model_dir(path)
        elif suffix == ".aimet":
            _validate_aimet_model_dir(path)
    return MODEL_TYPES_BY_EXTENSION[suffix]


# Caution: there is some mild fudging going on here:
#  * We do not associate an extension with UNRECOGNIZED_MODEL_TYPE
#  * not part of MODEL_TYPES_BY_EXTENSION dict.
#  * We have two for TORCHSCRIPT
#  * .so (2x for QNN_LIB) is not a supported source model type in the client.
assert len(MODEL_TYPES_BY_EXTENSION) == len(SourceModelType) - 2

ZIPPABLE_MODEL_TYPES = {
    SourceModelType.MLMODELC,
    SourceModelType.MLPACKAGE,
    SourceModelType.TETRART,
    SourceModelType.AIMET_ONNX,
    SourceModelType.ONNX,
}

EXTENSIONS_BY_MODEL_TYPE = {
    MODEL_TYPES_BY_EXTENSION[ext]: (
        ext + ".zip" if MODEL_TYPES_BY_EXTENSION[ext] in ZIPPABLE_MODEL_TYPES else ext
    )
    for ext in MODEL_TYPES_BY_EXTENSION
}

# PyTorch has two extensions. Affirmatively pick one.
EXTENSIONS_BY_MODEL_TYPE[SourceModelType.TORCHSCRIPT] = ".pt"


class Model:
    """
    Neural network model object.

    A model should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.upload_model`, :py:func:`qai_hub.get_model`, or
    :py:func:`qai_hub.get_models`.

    Attributes
    ----------
    model_id : str
        The model ID.
    date : datetime
        The time this model was uploaded.
    model_type : SourceModelType
        The type of the model.
    name : str
        An optional user-provided name to identify the model.
    metadata : Dict[ModelMetadataKey, str]
        Model metadata.
    """

    def __init__(
        self,
        owner: Client,
        model_id: str,
        date: datetime,
        model_type: SourceModelType,
        name: str,
        metadata: Dict[ModelMetadataKey, str],
        model: Any | None,  # Any instead of SourceModel to keep mypy happy
        verbose: bool,
        producer: Job | None,
    ):
        self._owner = owner
        self.model_id = model_id
        self.date = date
        self.model_type = model_type
        self.name = name
        self.metadata = metadata
        self._model = model  # access through download
        self.verbose = verbose
        self.producer = producer

    @property
    def url(self) -> str:
        """
        Returns the URL for the model.

        Returns
        -------
        : str
            The URL for the model.
        """

        return f"{self._owner._web_url_of_model(self.model_id)}"

    @overload
    def download(self, filename: str) -> str: ...

    @overload
    def download(self) -> SourceModel: ...

    def download(self, filename: str | None = None) -> SourceModel | str:
        """
        Downloads source model either to memory or to file.

        Parameters
        ----------
        filename:
            If filename is specified the model is downloaded to file,
            otherwise to memory.
            If the filename doesn't end with the correct file extension,
            the appropriate file extension is added to the name.

        Returns
        -------
        : SourceModel | str
            If `filename` is `None`, return `SourceModel`. Otherwise return the path to the downloaded model.
        """
        if filename is not None:
            download_file = filename
        else:
            if self.model_type == SourceModelType.UNRECOGNIZED_MODEL_TYPE:
                raise UserError(
                    "Model not recognized."
                    " Please upgrade qai-hub client to be able to download the model."
                )
            elif IS_WINDOWS and self.model_type == SourceModelType.MLMODEL:
                raise UserError(
                    "Cannot load .mlmodel into memory on Windows "
                    "platform. Specify `filename` to download to disk."
                )
            elif self.model_type == SourceModelType.MLMODELC:
                raise UserError(
                    "Cannot load .mlmodelc into memory. "
                    "Please specify a filename to download it to disk without loading it."
                )
            elif self.model_type == SourceModelType.MLPACKAGE:
                raise UserError(
                    "Cannot load .mlpackage into memory. "
                    "Please specify a filename to download it to disk without loading it."
                )

            # delete=False to be compatible with Windows
            with tempfile.NamedTemporaryFile(delete=False) as file:
                download_file = file.name
            # Close the file to avoid double-open on Windows

        download_file = _api_call(
            api.download_model,
            self._owner.config,
            self.model_id,
            file_path=download_file,
            verbose=self.verbose,
        )
        if filename is not None:
            print(f"Downloaded model to {download_file}")
            return download_file

        elif self.model_type == SourceModelType.TORCHSCRIPT:
            import torch

            self._model = torch.jit.load(download_file)
        elif self.model_type == SourceModelType.MLMODEL:
            import coremltools

            self._model = coremltools.models.MLModel(download_file)
        elif self.model_type == SourceModelType.TFLITE:
            with open(download_file, "rb") as tf_file:
                self._model = tf_file.read()

        elif self.model_type == SourceModelType.ONNX:
            import onnx

            path = str(download_file)
            if os.path.splitext(path)[1] == ".zip":
                with tempfile.TemporaryDirectory() as tmp_dir:
                    unzip_model(path, tmp_dir)
                    model_dir = os.path.join(tmp_dir, os.listdir(tmp_dir)[0])
                    onnx_files = [
                        f for f in os.listdir(model_dir) if f.endswith(".onnx")
                    ]
                    onnx_file = os.path.join(model_dir, onnx_files[0])
                    self._model = onnx.load(onnx_file)
            else:
                self._model = onnx.load(download_file)
        # Depreated runtime target, keep download available for existing artifacts
        elif self.model_type == api_pb.ModelType.MODEL_TYPE_ORT:
            with open(download_file, "rb") as ort_file:
                self._model = ort_file.read()
        else:
            raise ValueError(
                f"Model type `{self.model_type.name}` cannot be loaded into memory. "
                "Please pass a filename to the download function to save it to disk."
            )

        os.remove(download_file)

        assert self._model is not None

        return self._model

    def get_sharing(self) -> List[str]:
        """
        Get the list of email addresses of users that this model has been shared with.
        """
        response = _api_call(
            api.get_sharing,
            self._owner.config,
            self.model_id,
            api.SharedEntityType.MODEL,
        )
        return response.email

    def disable_sharing(self) -> None:
        """
        Disable all sharing for this model.

        Note that the model will still be accessible by users with which related job(s) are shared.
        """
        _api_call(
            api.disable_sharing,
            self._owner.config,
            self.model_id,
            api.SharedEntityType.MODEL,
        )

    def modify_sharing(
        self, add_emails: List[str] = [], delete_emails: List[str] = []
    ) -> None:
        """
        Modifies the list of users that the model is shared with.

        If this model was compiled by hub, it will have an associated Compile Job.
        The associated Compile Job will not be visible unless said Compile Job is also shared.
        """
        if not add_emails and not delete_emails:
            raise UserError(
                "Either add_emails or delete_emails must be specified and non-empty"
            )

        if not isinstance(add_emails, list) or not isinstance(delete_emails, list):
            raise UserError("add_emails and delete_emails must both be lists")

        _api_call(
            api.modify_sharing,
            self._owner.config,
            self.model_id,
            api.SharedEntityType.MODEL,
            add_emails,
            delete_emails,
        )

    def __str__(self) -> str:
        return f"Model(model_id='{self.model_id}', name='{self.name}')"

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "model_id",
                "url",
                "name",
                ("model_type", self.model_type.name),
                (
                    "producer_id",
                    None if self.producer is None else self.producer.job_id,
                ),
                "date",
            ],
        )


def _determine_model_type(
    model: Model | SourceModel | TargetModel | str | Path | None,
) -> SourceModelType:
    error_message = """
        - TorchScript: Extension .pt or .pth
        - Tensorflow Lite: Extension .tflite
        - ONNX: Extension .onnx
        - QNN Binary: Extension .bin
        - AIMET Model: Directory ending with .aimet
    """
    if model is None:
        raise UserError(
            "Model passed in was 'None' (make sure this is not the target of a failed compile job)"
        )
    elif isinstance(model, Model):
        return model.model_type
    elif isinstance(model, (str, Path)):
        path = str(model)
        if os.path.splitext(path)[1] == ".zip":
            with tempfile.TemporaryDirectory() as tmp_dir:
                return _determine_model_type(unzip_model(path, tmp_dir))
        model_type = _filepath_to_model_type(path)
        if model_type is None:
            raise UserError(
                rf"Unsupported model type for {model}. The following types are supported {error_message}"
            )
        return model_type
    elif type(model).__name__ in {"TopLevelTracedModule", "RecursiveScriptModule"}:
        return SourceModelType.TORCHSCRIPT
    elif type(model).__name__ == "MLModel":
        import coremltools

        assert isinstance(model, coremltools.models.model.MLModel)

        # MLModel distinguishes NeuralNetwork and MLPackage format
        # with following field
        # https://github.com/apple/coremltools/blob/d52d536a399011933c6faf23d8fa19bcf79c5dca/coremltools/models/model.py#L360
        if model.is_package:
            return SourceModelType.MLPACKAGE
        return SourceModelType.MLMODEL
    elif isinstance(model, bytes) and model[4:8] == b"TFL3":
        return SourceModelType.TFLITE
    elif type(model).__name__ == "ModelProto":
        return SourceModelType.ONNX
    else:
        module_name_list = [model_type.__module__ for model_type in type(model).mro()]
        if "torch.nn.modules.module" in module_name_list:
            raise UserError("The torch model must be traced.")
        raise UserError(
            f"Unsupported model type. The following types are supported {error_message}"
        )


def _determine_model_extension(type: SourceModelType) -> str:
    suffix = EXTENSIONS_BY_MODEL_TYPE.get(type, None)
    if suffix is not None:
        return suffix
    raise RuntimeError(f"Unsupported model type: {type}")


## JOBS ##


@dataclass(
    unsafe_hash=True  # ideally would be frozen but that would be backwards-incompatible
)
class JobStatus:
    """
    Status of a job.

    Attributes
    ----------
    code: str
        Status code for the job as a string such as "SUCCESS" or "OPTIMIZING_MODEL".
        See :py:class:`JobStatus.State` for a list of possible states.
    message: str
        Optional error message.
    """

    class State(Enum):
        SUCCESS = api_pb.JobState.JOB_STATE_DONE
        FAILED = api_pb.JobState.JOB_STATE_FAILED
        CREATED = api_pb.JobState.JOB_STATE_CREATED
        UNSPECIFIED = api_pb.JobState.JOB_STATE_UNSPECIFIED
        OPTIMIZING_MODEL = api_pb.JobState.JOB_STATE_OPTIMIZING_MODEL
        PROVISIONING_DEVICE = api_pb.JobState.JOB_STATE_PROVISIONING_DEVICE
        MEASURING_PERFORMANCE = api_pb.JobState.JOB_STATE_MEASURING_PERFORMANCE
        RUNNING_INFERENCE = api_pb.JobState.JOB_STATE_RUNNING_INFERENCE
        QUANTIZING_MODEL = api_pb.JobState.JOB_STATE_QUANTIZING_MODEL
        LINKING_MODELS = api_pb.JobState.JOB_STATE_LINKING_MODELS

        @classmethod
        def _missing_(cls, value):
            return JobStatus.State.UNSPECIFIED

        def _is_terminal_state(self) -> bool:
            return (
                self is JobStatus.State.SUCCESS or self is JobStatus.State.FAILED
            ) and not (
                self is JobStatus.State.CREATED
                or self is JobStatus.State.OPTIMIZING_MODEL
                or self is JobStatus.State.QUANTIZING_MODEL
                or self is JobStatus.State.PROVISIONING_DEVICE
                or self is JobStatus.State.MEASURING_PERFORMANCE
                or self is JobStatus.State.RUNNING_INFERENCE
                or self is JobStatus.State.LINKING_MODELS
                or self is JobStatus.State.UNSPECIFIED
            )
            assert_never(self)

        def _is_running_state(self) -> bool:
            return (
                self is JobStatus.State.OPTIMIZING_MODEL
                or self is JobStatus.State.QUANTIZING_MODEL
                or self is JobStatus.State.PROVISIONING_DEVICE
                or self is JobStatus.State.MEASURING_PERFORMANCE
                or self is JobStatus.State.RUNNING_INFERENCE
                or self is JobStatus.State.LINKING_MODELS
                or self is JobStatus.State.UNSPECIFIED
            ) and not (
                self is JobStatus.State.SUCCESS
                or self is JobStatus.State.FAILED
                or self is JobStatus.State.CREATED
            )
            assert_never(self)

    @staticmethod
    def all_running_states():
        """
        Returns
        -------
        : List[JobStatus.State]
        returns a list of all states in which jobs are running (not finished or pending)
        """
        return [state for state in JobStatus.State if state._is_running_state()]

    _len_largest_state: ClassVar[int] = max([len(enum_val.name) for enum_val in State])

    state: JobStatus.State
    message: str | None = None

    @property
    def code(self) -> str:
        return self.state.name

    @property
    def symbol(self) -> str:
        if self.failure:
            return "❌"
        elif self.success:
            return "✅"
        elif self.state == JobStatus.State.UNSPECIFIED:
            return ""
        else:
            return "⏳"

    @property
    def success(self) -> bool:
        """
        Returns whether a job finished succesfully.

        Returns
        -------
        : bool
            returns true if the job finished succesfully.
        """
        return self.state == JobStatus.State.SUCCESS

    @property
    def failure(self) -> bool:
        """
        Returns whether a job failed.

        Returns
        -------
        : bool
            returns true if the job failed.
        """
        return self.state == JobStatus.State.FAILED

    @property
    def finished(self) -> bool:
        """
        Returns whether a job finished.

        Returns
        -------
        : bool
            returns true if the job finished.
        """
        return self.state._is_terminal_state()

    @property
    def running(self) -> bool:
        """
        Returns whether a job is still running.

        Returns
        -------
        : bool
            returns true if the job is still running.
        """
        return self.state._is_running_state()

    @property
    def pending(self) -> bool:
        """
        Returns whether a job is waiting to start running.

        Returns
        -------
        : bool
            returns true if the job is waiting to start.
        """
        return self.state == JobStatus.State.CREATED

    def __eq__(self, obj) -> bool:
        if isinstance(obj, JobStatus.State):
            return self.state == obj
        elif isinstance(obj, str):
            return self.code == obj
        return self.state == obj.state and self.message == obj.message

    def __repr__(self) -> str:
        return _class_repr_print(self, ["code", "message"])


class JobType(Enum):
    """
    The type of a job (compile, profile, etc.)
    """

    COMPILE = api_pb.JobType.JOB_TYPE_COMPILE
    PROFILE = api_pb.JobType.JOB_TYPE_PROFILE
    INFERENCE = api_pb.JobType.JOB_TYPE_INFERENCE
    QUANTIZE = api_pb.JobType.JOB_TYPE_QUANTIZE
    LINK = api_pb.JobType.JOB_TYPE_LINK
    UNSPECIFIED = api_pb.JobType.JOB_TYPE_UNSPECIFIED

    @classmethod
    def _missing_(cls, value):
        return JobType.UNSPECIFIED

    @property
    def display_name(self) -> str:
        return self.name.lower()


@dataclass
class JobResult:
    """
    Job result structure.

    Attributes
    ----------
    status : JobStatus
        Status of the job.
    url: str
        The url for the job.
    artifacts_dir:str
        Directory where the results are stored.
    """

    status: JobStatus
    url: str | None
    artifacts_dir: str


@dataclass
class CompileJobResult(JobResult):
    """
    Compile Job result structure.

    Examples
    --------
    Fetch a job result::

        import qai_hub as hub
        job = hub.get_job("jabc123")
        job_result = job.download_results("artifacts")

    """

    def __repr__(self) -> str:
        # Successful job
        if self.status.success:
            return _class_repr_print(self, ["status", "artifacts_dir"])
        else:
            # Failed job
            return _class_repr_print(self, ["status"])


@dataclass
class QuantizeJobResult(JobResult):
    """
    Quantize Job result structure.

    Examples
    --------
    Fetch a job result::

        import qai_hub as hub
        job = hub.get_job("jabc123")
        job_result = job.download_results("artifacts")

    """

    def __repr__(self) -> str:
        return _class_repr_print(self, ["status"])


@dataclass
class LinkJobResult(JobResult):
    """
    Link Job result structure.

    Examples
    --------
    Fetch a job result::

        import qai_hub as hub
        job = hub.get_job("jabc123")
        job_result = job.download_results("artifacts")

    """

    def __repr__(self) -> str:
        # Successful job
        if self.status.success:
            return _class_repr_print(self, ["status", "artifacts_dir"])
        else:
            # Failed job
            return _class_repr_print(self, ["status"])


@dataclass
class InferenceJobResult(JobResult):
    """
    Inference Job result structure.

    Examples
    --------
    Fetch a job result::

        import qai_hub as hub
        job = hub.get_job("jabc123")
        job_result = job.download_results("artifacts")

    """

    def __repr__(self) -> str:
        # Successful job
        if self.status.success:
            return _class_repr_print(self, ["status", "artifacts_dir"])
        else:
            # Failed job
            return _class_repr_print(self, ["status"])


@dataclass
class ProfileJobResult(JobResult):
    """
    Profile Job result structure.

    Attributes
    ----------
    profile : Dict
        The profile result as a python dictionary for a successful job.

    Examples
    --------
    Fetch a job result::

        import qai_hub as hub
        job = hub.get_job("jabc123")

    Print the profiling results as a dictionary structure::

        profile = job.download_profile()

    Print the model runtime latency in milliseconds::

        latency_ms = profile["execution_summary"]["estimated_inference_time"] / 1000


    """

    profile: Dict

    @property
    def _compute_unit_breakdown(self) -> Dict[str, int]:
        breakdown: Dict[str, int] = dict(NPU=0, GPU=0, CPU=0)
        for layer_detail in self.profile["execution_detail"]:
            breakdown[layer_detail["compute_unit"]] += 1
        return breakdown

    def __repr__(self) -> str:
        # Successful job
        if self.status.success:
            profile_sum = self.profile["execution_summary"]
            breakdown = self._compute_unit_breakdown
            breakdown_str = ", ".join(
                f"{k}: {v}" for k, v in breakdown.items() if v > 0
            )
            return _class_repr_print(
                self,
                [
                    "status",
                    "url",
                    "artifacts_dir",
                    (
                        "Estimated Inference Time (ms)",
                        profile_sum["estimated_inference_time"] / 1000,
                    ),
                    ("Load Time (ms)", profile_sum["warm_load_time"] / 1000),
                    (
                        "Peak Memory (MB)",
                        profile_sum["estimated_inference_peak_memory"] / 1024 / 1024,
                    ),
                    ("Compute Units (layers)", breakdown_str),
                ],
            )
        else:
            # Failed job
            return _class_repr_print(self, ["status", "url"])


@dataclass(frozen=True)
class JobSummary(ABC):
    """
    Summary information about a job and its current status. Job summaries can be queried
    in bulk for many jobs at a time through :py:func:`qai_hub.get_job_summaries`.

    A job summary should not be constructed directly.

    See also :py:class:`CompileJobSummary`, :py:class:`ProfileJobSummary`, :py:class:`InferenceJobSummary`, :py:class:`QuantizeJobSummary`

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job.
    date : datetime
        The time this job was submitted.
    username : str
        Username of the user who submitted the job.
    status: JobStatus
        Status of the job.
    url: str
        Returns the URL for the job.
    """

    job_id: str
    name: str
    date: datetime
    username: str
    status: JobStatus
    job_type: JobType
    url: str

    # Documented in subclasses because 'device' means a different thing in each
    device_name: Optional[str]

    def __str__(self) -> str:
        return f"Job(job_id={self.job_id}, device={self.device_name})"

    def __repr__(self) -> str:
        attrs = [
            "job_id",
            "url",
            "name",
            "date",
            "username",
            ("status", self.status.code),
        ]
        if self.device_name is not None:
            attrs.append("device_name")
        return _class_repr_print(self, attrs)


@dataclass(frozen=True)
class CompileJobSummary(JobSummary):
    """
    Summary information about a compile job and its current status. Job summaries can be queried
    in bulk for many jobs at a time through :py:func:`qai_hub.get_job_summaries`.

    A compile job summary should not be constructed directly.

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job.
    date : datetime
        The time this job was submitted.
    username : str
        Username of the user who submitted the job.
    status: JobStatus
        Status of the job.
    device_name : str
        The name of the device compiled for.
    """

    @classmethod
    def _summary_from_pb(
        cls,
        owner: Client,
        compile_job_pb: api_pb.CompileJobSummary,
    ):
        status = JobStatus(
            JobStatus.State(compile_job_pb.job_state)
        )  # note: no failure reason
        return CompileJobSummary(
            job_id=compile_job_pb.job_id,
            name=compile_job_pb.name,
            date=owner._creation_date_from_timestamp(compile_job_pb),
            username=compile_job_pb.user.email,
            status=status,
            job_type=JobType.COMPILE,
            url=owner._web_url_of_job(compile_job_pb.job_id),
            device_name=compile_job_pb.device_name,
        )


@dataclass(frozen=True)
class QuantizeJobSummary(JobSummary):
    """
    Summary information about a quantize job and its current status. Job summaries can be queried
    in bulk for many jobs at a time through :py:func:`qai_hub.get_job_summaries`.

    A quantize job summary should not be constructed directly.

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job.
    date : datetime
        The time this job was submitted.
    username : str
        Username of the user who submitted the job.
    status: JobStatus
        Status of the job.
    """

    @classmethod
    def _summary_from_pb(
        cls,
        owner: Client,
        quantize_job_pb: api_pb.QuantizeJobSummary,
    ):
        status = JobStatus(
            JobStatus.State(quantize_job_pb.job_state)
        )  # note: no failure reason
        return QuantizeJobSummary(
            job_id=quantize_job_pb.job_id,
            name=quantize_job_pb.name,
            date=owner._creation_date_from_timestamp(quantize_job_pb),
            username=quantize_job_pb.user.email,
            status=status,
            job_type=JobType.QUANTIZE,
            url=owner._web_url_of_job(quantize_job_pb.job_id),
            device_name=None,
        )


class LinkJobSummary(JobSummary):
    """
    Summary information about a link job and its current status. Job summaries can be queried
    in bulk for many jobs at a time through :py:func:`qai_hub.get_job_summaries`.

    A link job summary should not be constructed directly.

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job.
    date : datetime
        The time this job was submitted.
    username : str
        Username of the user who submitted the job.
    status: JobStatus
        Status of the job.
    """

    @classmethod
    def _summary_from_pb(
        cls,
        owner: Client,
        link_job_pb: api_pb.LinkJobSummary,
    ):
        status = JobStatus(
            JobStatus.State(link_job_pb.job_state)
        )  # note: no failure reason
        return LinkJobSummary(
            job_id=link_job_pb.job_id,
            name=link_job_pb.name,
            date=owner._creation_date_from_timestamp(link_job_pb),
            username=link_job_pb.user.email,
            status=status,
            job_type=JobType.LINK,
            url=owner._web_url_of_job(link_job_pb.job_id),
            device_name=None,
        )


@dataclass(frozen=True)
class ProfileJobSummary(JobSummary):
    """
    Summary information about a profile job and its current status. Job summaries can be queried
    in bulk for many jobs at a time through :py:func:`qai_hub.get_job_summaries`.

    A profile job summary should not be constructed directly.

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job.
    date : datetime
        The time this job was submitted.
    username : str
        Username of the user who submitted the job.
    status: JobStatus
        Status of the job.
    device_name : str
        The name of the device on which the model is being profiled.
    estimated_inference_time: int
        Time spent in inference, in microseconds.
    inference_memory_peak_range: (int, int)
        Estimated lower and upper bound of peak memory used in inference, in bytes
    """

    estimated_inference_time: int
    inference_memory_peak_range: Tuple[int, int]

    @classmethod
    def _summary_from_pb(
        cls,
        owner: Client,
        profile_job_pb: api_pb.ProfileJobSummary,
    ):
        status = JobStatus(JobStatus.State(profile_job_pb.job_state))
        inference_memory_peak_range = (
            profile_job_pb.execution_peak_memory.lower,
            profile_job_pb.execution_peak_memory.upper,
        )
        return ProfileJobSummary(
            job_id=profile_job_pb.job_id,
            name=profile_job_pb.name,
            date=owner._creation_date_from_timestamp(profile_job_pb),
            username=profile_job_pb.user.email,
            status=status,
            job_type=JobType.PROFILE,
            url=owner._web_url_of_job(profile_job_pb.job_id),
            device_name=profile_job_pb.device_name,
            estimated_inference_time=profile_job_pb.execution_time,
            inference_memory_peak_range=inference_memory_peak_range,
        )

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "job_id",
                "url",
                "name",
                "date",
                "username",
                ("status", self.status.code),
                "device_name",
                "estimated_inference_time",
                "inference_memory_peak_range",
            ],
        )


@dataclass(frozen=True)
class InferenceJobSummary(JobSummary):
    """
    Summary information about an inference job and its current status. Job summaries can be queried
    in bulk for many jobs at a time through :py:func:`qai_hub.get_job_summaries`.

    An inference job summary should not be constructed directly.

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job.
    date : datetime
        The time this job was submitted.
    username : str
        Username of the user who submitted the job.
    status: JobStatus
        Status of the job.
    device_name : str
        The name of the device on which inference is being performed.
    """

    @classmethod
    def _summary_from_pb(
        cls,
        owner: Client,
        inference_job_pb: api_pb.InferenceJobSummary,
    ):
        status = JobStatus(JobStatus.State(inference_job_pb.job_state))
        return InferenceJobSummary(
            job_id=inference_job_pb.job_id,
            name=inference_job_pb.name,
            date=owner._creation_date_from_timestamp(inference_job_pb),
            username=inference_job_pb.user.email,
            status=status,
            job_type=JobType.INFERENCE,
            url=owner._web_url_of_job(inference_job_pb.job_id),
            device_name=inference_job_pb.device_name,
        )


class Job(ABC):
    """
    abstract Job base class.

    A job should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.submit_compile_job`, :py:func:`qai_hub.submit_profile_job`,
    :py:func:`qai_hub.submit_inference_job`, or :py:func:`qai_hub.get_job`.

    See also :py:class:`CompileJob`, :py:class:`ProfileJob`, :py:class:`InferenceJob`

    Attributes
    ----------
    job_id : str
        The job ID.
    name : str
        Name of this job
    date : datetime
        The time this job was submitted.
    options: str
        Options passed during the job submission.
    """

    _polling_interval: int = 10

    def __init__(
        self,
        owner: Client,
        job_id: str,
        name: str,
        date: datetime,
        hub_version: str,
        options: str,
        verbose: bool,
        job_type: JobType,
        in_progress_states: List[JobStatus.State],
    ):
        self._owner = owner
        self._job_type = job_type
        self.job_id = job_id
        self.name = name
        self.date = date
        self.hub_version = hub_version
        self.options = options
        self.verbose = verbose
        self._in_progress_states = in_progress_states
        self._final_status: JobStatus | None = None

    @property
    def url(self) -> str:
        """
        Returns the URL for the job.

        Returns
        -------
        : str
            The URL for the job.
        """

        return f"{self._owner._web_url_of_job(self.job_id)}"

    @property
    def job_type(self) -> str:
        return self._job_type.display_name

    def wait(self, timeout: int | None = None) -> JobStatus:
        """
        Block until this job finishes.

        Parameters
        ----------
        timeout:
            If provided, a TimeoutError will be raised after waiting this many seconds.

            If `None`, this client will not time out the job, meaning it will block
            an indefinite amount of time waiting for the job to finish.

            HOWEVER, Qualcomm AI Hub will fail / time out any job a set amount of time
            after its creation. Therefore, even if `timeout` is `None`, the
            runtime of this method will still have a finite upper bound.

        Returns
        -------
        : str
            The final, "finished" (SUCCESS or FAILED) status for this job.

        Raises
        ------
        TimeoutError
            Raised only if a **client-side** timeout occurs, when param "timeout" != None.

            If the Qualcomm AI Hub server times out the job, this error will NOT be raised, and a
            FAILED job status will be returned instead.

        """

        def status_text(job_status: JobStatus) -> str:
            """
            Generates status text:
            [Status Symbol] [Status Name] [Progress Bar] [Progress Counter]
            """
            # Make sure we always output a string of the same size
            # by padding smaller status codes with spaces.
            status_code = job_status.code.ljust(JobStatus._len_largest_state)

            progress_bar: str
            progress_count: str
            if job_status.finished:
                # Don't show progress bar when we finish.
                # Pad with empty spaces to make sure we always
                # output the same string length.
                progress_count = "".ljust(3)
                progress_bar = progress_count
            else:
                # Determine number of done states to generate progress bar & count.
                total_states = len(self._in_progress_states)
                done_states = self._in_progress_states.index(job_status.state)

                progress_count = f"{str(done_states)}/{str(total_states)}"
                progress_bar = (
                    f"{'█' * done_states}{'░' * (total_states - done_states)}"
                )

            # Construct and return the status string.
            return f"{status.symbol} {status_code}{status.message or ''} {progress_bar} {progress_count}"

        def get_in_progress_dots(num_dots) -> Tuple[int, str]:
            """Generates a string of length 3 that contains num_dots periods."""
            num_dots = 0 if num_dots >= 3 else num_dots + 1
            return (num_dots, "." * num_dots + " " * (3 - num_dots))

        status = self.get_status()
        if status.running or status.pending:
            if self.verbose:
                print(
                    f"Waiting for {self.job_type} job ({self.job_id}) completion. Type Ctrl+C to stop waiting at any time."
                )

            num_dots = 3
            time_elapsed = 0
            sleep_seconds = Job._polling_interval if not self.verbose else 1
            while status.running or status.pending:
                if self.verbose:
                    num_dots, dots_str = get_in_progress_dots(num_dots)
                    print(f"    {status_text(status)} {dots_str}", end="\r")

                if timeout and time_elapsed >= timeout:
                    raise TimeoutError(
                        f"Waiting for {self.job_type} job ({self.job_id}) completion timed out after {time_elapsed} seconds."
                    )

                time.sleep(sleep_seconds)
                time_elapsed += sleep_seconds

                if time_elapsed % Job._polling_interval == 0:
                    status = self.get_status()

            if self.verbose:
                print(f"    {status_text(status)}    ", end="\a\n")
        return status

    @abstractmethod
    def _extract_job_specific_pb(
        self, job_pb: api_pb.Job
    ) -> (
        api_pb.CompileJob
        | api_pb.LinkJob
        | api_pb.QuantizeJob
        | api_pb.ProfileJob
        | api_pb.InferenceJob
    ):
        """
        Extract job specific part of pb.
        """

    def get_status(self) -> JobStatus:
        """
        Returns the status of a job.

        Returns
        -------
        : JobStatus
            The status of the job
        """
        if self._final_status is not None:
            return self._final_status
        job_pb = _api_call(api.get_job, self._owner.config, self.job_id)
        job_specific_pb = self._extract_job_specific_pb(job_pb)
        job_status = JobStatus(
            JobStatus.State(job_specific_pb.job_state), job_specific_pb.failure_reason
        )
        if job_status.finished:
            self._final_status = job_status
        return job_status

    def set_name(self, job_name: str) -> None:
        """
        Sets the name of a job to the specified value.
        """
        _api_call(api.set_job_name, self._owner.config, self.job_id, job_name)
        # Any failure during the API call would throw an exception.
        # so, if execution reaches the next line, it's safe to assume that the
        # job name has been updated on Hub.
        self.name = job_name

    @abstractmethod
    def download_results(self, artifacts_dir: str) -> JobResult:
        raise NotImplementedError

    def get_sharing(self) -> List[str]:
        """
        Get the list of email addresses of users that this job has been shared with.
        """
        response = _api_call(
            api.get_sharing, self._owner.config, self.job_id, api.SharedEntityType.JOB
        )
        return response.email

    def disable_sharing(self) -> None:
        """
        Disable all sharing for this job.
        """
        _api_call(
            api.disable_sharing,
            self._owner.config,
            self.job_id,
            api.SharedEntityType.JOB,
        )

    def modify_sharing(
        self, add_emails: List[str] = [], delete_emails: List[str] = []
    ) -> None:
        """
        Modifies the list of users that the job is shared with.

        All assets (models, datasets, artifacts, etc.) associated with the job will also be shared.
        For inference and profile jobs, the corresponding compile and link jobs (if any) will also be shared.
        """
        if not add_emails and not delete_emails:
            raise UserError(
                "Either add_emails or delete_emails must be specified and non-empty"
            )

        if not isinstance(add_emails, list) or not isinstance(delete_emails, list):
            raise UserError("add_emails and delete_emails must both be lists")

        _api_call(
            api.modify_sharing,
            self._owner.config,
            self.job_id,
            api.SharedEntityType.JOB,
            add_emails,
            delete_emails,
        )


class CompileJob(Job):
    """
    Compile job for a model, a set of input specs, and a set of device.

    A compile job should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.submit_compile_job`, or :py:func:`qai_hub.get_job`.

    Attributes
    ----------
    device : Device
        The device compiled for.
    compatible_devices : List[Device]
        The devices compiled for in case of single compile.
    model : Model
        The model for the job.
    date : datetime
        The time this job was submitted.
    shapes : InputSpecs
        The input specs for the model to be compiled.
    target_shapes : InputSpecs
        The input specs for the compiled model to run (profile or inference).
    calibration_dataset : Optional[Dataset]
        The dataset used with post training quantization run during compilation.
    """

    _job_type = JobType.COMPILE

    def __init__(
        self,
        job_pb: api_pb.Job,
        owner: Client,
        device: Device,
        compatible_devices: List[Device],
        model: Model,
        date: datetime,
        shapes: InputSpecs,
        target_shapes: InputSpecs,
        calibration_dataset: Optional[Dataset],
    ):
        compile_job_pb = job_pb.compile_job
        super().__init__(
            owner=owner,
            job_id=compile_job_pb.compile_job_id,
            name=compile_job_pb.name,
            date=date,
            hub_version=job_pb.hub_version,
            options=compile_job_pb.options,
            verbose=owner.verbose,
            job_type=self._job_type,
            in_progress_states=[
                JobStatus.State.CREATED,
                JobStatus.State.OPTIMIZING_MODEL,
            ],
        )
        self.device = device
        self.model = model
        self.shapes = shapes
        self.target_shapes = target_shapes
        self._target_model = owner._make_target_model(compile_job_pb, self)
        self.compatible_devices = compatible_devices
        self.calibration_dataset = calibration_dataset

    def get_target_model(self) -> Model | None:
        """
        Returns the target model object.
        If the job is not ready, this function will block until completion.

        Returns
        -------
        : TargetModel | None
            The target model object, or None if the job failed.
        """
        self.wait()

        return self._target_model

    @overload
    def download_target_model(self, filename: str) -> str | None: ...

    @overload
    def download_target_model(self) -> TargetModel | None: ...

    def download_target_model(
        self, filename: str | None = None
    ) -> TargetModel | str | None:
        """
        Returns the downloaded target model, either in memory or as a file.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        filename:
            If filename is specified the target model is downloaded to file, otherwise
            to memory.

        Returns
        -------
        : TargetModel | str | None
            The downloaded target model, filename, or None if the job failed.
        """
        target_model = self.get_target_model()
        if target_model is None:
            return None
        # Asserting the return type is correct requires importing coremltools.
        # Seems like overkill so we're just going to trust that we didn't get
        # a SourceModel that isn't also a TargetModel.
        return target_model.download(filename)  # type: ignore

    def download_results(self, artifacts_dir: str) -> CompileJobResult:
        """
        Returns all the results of a job.

        This includes the compiled target model.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        artifacts_dir:
            Directory name where the job artifacts are stored.
            If the directory does not exist, it is created.

        Returns
        -------
        : CompileJobResult
            Job results.
        """
        artifacts_dir = os.path.abspath(os.path.expanduser(artifacts_dir))
        os.makedirs(artifacts_dir, exist_ok=True)

        self.download_target_model(artifacts_dir)

        return CompileJobResult(
            status=self.get_status(),
            url=self.url,
            artifacts_dir=artifacts_dir,
        )

    def wait(self, timeout: int | None = None) -> JobStatus:
        status = super().wait(timeout)
        if status.success and self._target_model is None:
            compile_job_pb = _api_call(
                api.get_job, self._owner.config, job_id=self.job_id
            ).compile_job
            self.target_shapes = dict(
                api_utils.tensor_type_list_pb_to_list_shapes(
                    compile_job_pb.target_tensor_type_list
                )
            )
            self._target_model = self._owner._make_target_model(compile_job_pb, self)
        return status

    def _extract_job_specific_pb(self, job_pb: api_pb.Job) -> api_pb.CompileJob:
        return job_pb.compile_job

    def __str__(self) -> str:
        return f"Job(job_id={self.job_id}, model_id={self.model.model_id}, device={self.device})"

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "job_id",
                "url",
                ("status", self.get_status().code),
                "model",
                "name",
                "options",
                "shapes",
                "target_shapes",
                "device",
                "compatible_devices",
                "date",
                "calibration_dataset",
            ],
        )


class QuantizeJob(Job):
    """
    Quantize job for a model, a set of input specs, and a set of device.

    A quantize job should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.submit_quantize_job`, :py:func:`qai_hub.get_job`, or
    :py:func:`qai_hub.get_jobs`.

    Attributes
    ----------
    model : Model
        The model for the job.
    date : datetime
        The time this job was submitted.
    shapes : InputSpecs
        The input specs for the model to be compiled.
    target_shapes : InputSpecs
        The input specs for the compiled model to run (profile or inference).
    calibration_dataset : Optional[Dataset]
        The dataset used with post training quantization run during compilation.
    """

    _job_type = JobType.QUANTIZE

    def __init__(
        self,
        job_pb: api_pb.Job,
        weights_dtype: QuantizeDtype,
        activations_dtype: QuantizeDtype,
        owner: Client,
        model: Model,
        date: datetime,
        shapes: InputSpecs,
        calibration_dataset: Dataset,
    ):
        quantize_job_pb = job_pb.quantize_job
        super().__init__(
            owner=owner,
            job_id=quantize_job_pb.quantize_job_id,
            name=quantize_job_pb.name,
            date=date,
            hub_version=job_pb.hub_version,
            options=quantize_job_pb.options,
            verbose=owner.verbose,
            job_type=self._job_type,
            in_progress_states=[
                JobStatus.State.CREATED,
                JobStatus.State.QUANTIZING_MODEL,
            ],
        )
        self.model = model
        self.shapes = shapes
        self._target_model = owner._make_target_model(quantize_job_pb, self)
        self.calibration_dataset = calibration_dataset
        self.weights_dtype = weights_dtype
        self.activations_dtype = activations_dtype

    def get_target_model(self) -> Model | None:
        """
        Returns the target model object.
        If the job is not ready, this function will block until completion.

        Returns
        -------
        : TargetModel | None
            The target model object, or None if the job failed.
        """
        self.wait()

        return self._target_model

    @overload
    def download_target_model(self, filename: str) -> str | None: ...

    @overload
    def download_target_model(self) -> TargetModel | None: ...

    def download_target_model(
        self, filename: str | None = None
    ) -> TargetModel | str | None:
        """
        Returns the downloaded target model, either in memory or as a file.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        filename:
            If filename is specified the target model is downloaded to file, otherwise
            to memory.

        Returns
        -------
        : TargetModel | str | None
            The downloaded target model, filename, or None if the job failed.
        """
        target_model = self.get_target_model()
        if target_model is None:
            return None
        # Asserting the return type is correct requires importing coremltools.
        # Seems like overkill so we're just going to trust that we didn't get
        # a SourceModel that isn't also a TargetModel.
        return target_model.download(filename)  # type: ignore

    def download_results(self, artifacts_dir: str) -> QuantizeJobResult:
        """
        Returns all the results of a job.

        This includes compiled target model.

        If the job is not ready, this function will block until completion.

        Returns
        -------
        : QuantizeJobResult
            Job results.
        """
        artifacts_dir = os.path.abspath(os.path.expanduser(artifacts_dir))
        os.makedirs(artifacts_dir, exist_ok=True)

        self.download_target_model(artifacts_dir)

        return QuantizeJobResult(
            status=self.get_status(),
            url=self.url,
            artifacts_dir=artifacts_dir,
        )

    def wait(self, timeout: int | None = None) -> JobStatus:
        status = super().wait(timeout)
        if status.success and self._target_model is None:
            quantize_job_pb = _api_call(
                api.get_job, self._owner.config, job_id=self.job_id
            ).quantize_job
            self._target_model = self._owner._make_target_model(quantize_job_pb, self)
        return status

    def _extract_job_specific_pb(self, job_pb: api_pb.Job) -> api_pb.QuantizeJob:
        return job_pb.quantize_job

    def __str__(self) -> str:
        return f"Job(job_id={self.job_id}, model_id={self.model.model_id})"

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "job_id",
                "url",
                ("status", self.get_status().code),
                "model",
                "name",
                "options",
                "shapes",
                "date",
                "calibration_dataset",
                "weights_dtype",
                "activations_dtype",
            ],
        )


class LinkJob(Job):
    """
    Link job for a collection of models.

    A link job should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.submit_link_job`, or :py:func:`qai_hub.get_job`.

    Attributes
    ----------
    models : List[Model]
        The models for the job.
    date : datetime
        The time this job was submitted.
    """

    __in_progress_states: ClassVar[List[JobStatus.State]] = [
        JobStatus.State.CREATED,
        JobStatus.State.LINKING_MODELS,
    ]
    _job_type = JobType.LINK

    def __init__(
        self,
        job_pb,
        owner: Client,
        models: List[Model],
        date: datetime,
    ):
        link_job_pb = job_pb.link_job
        super().__init__(
            owner=owner,
            job_id=link_job_pb.link_job_id,
            name=link_job_pb.name,
            date=date,
            hub_version=job_pb.hub_version,
            options=link_job_pb.options,
            verbose=owner.verbose,
            job_type=self._job_type,
            in_progress_states=self.__in_progress_states,
        )
        self.models = models
        self._target_model: Model | None = owner._make_target_model(link_job_pb, self)

    def wait(self, timeout: int | None = None) -> JobStatus:
        status = super().wait(timeout)
        if status.success and self._target_model is None:
            link_job_pb = _api_call(
                api.get_job, self._owner.config, job_id=self.job_id
            ).link_job
            self._target_model = self._owner._make_target_model(link_job_pb, self)
        return status

    def _extract_job_specific_pb(self, job_pb: api_pb.Job) -> api_pb.LinkJob:
        return job_pb.link_job

    def get_target_model(self) -> Model | None:
        """
        Returns the target model object.
        If the job is not ready, this function will block until completion.

        Returns
        -------
        : TargetModel | None
            The target model object, or None if the job failed.
        """
        self.wait()

        return self._target_model

    @overload
    def download_target_model(self, filename: str) -> str | None: ...

    @overload
    def download_target_model(self) -> TargetModel | None: ...

    def download_target_model(
        self, filename: str | None = None
    ) -> TargetModel | str | None:
        """
        Returns the downloaded target model, either in memory or as a file.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        filename:
            If filename is specified the target model is downloaded to file, otheriwse
            to memory.

        Returns
        -------
        : TargetModel | str | None
            The downloaded target model, filename, or None if the job failed.
        """
        target_model = self.get_target_model()
        if target_model is None:
            return None
        return target_model.download(filename)  # type: ignore

    def download_results(self, artifacts_dir: str) -> LinkJobResult:
        """
        Returns all the results of a job.

        This includes the linked target model.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        artifacts_dir:
            Directory name where the job artifacts are stored.
            If the directory does not exist, it is created.

        Returns
        -------
        : LinkJobResult
            Job results.
        """
        artifacts_dir = os.path.abspath(os.path.expanduser(artifacts_dir))
        os.makedirs(artifacts_dir, exist_ok=True)

        self.download_target_model(artifacts_dir)

        return LinkJobResult(
            status=self.get_status(),
            url=self.url,
            artifacts_dir=artifacts_dir,
        )

    def __str__(self) -> str:
        return (
            f"Job(job_id={self.job_id}, model_id={[m.model_id for m in self.models]})"
        )

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "job_id",
                "url",
                ("status", self.get_status().code),
                ("models", [m.model_id for m in self.models]),
                "name",
                "options",
                "date",
            ],
        )


class ProfileJob(Job):
    """
    Profile job for a model, a set of input specs, and a device.

    A profile job should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.submit_profile_job`, or :py:func:`qai_hub.get_job`.

    Attributes
    ----------
    device : Device
        The device on which the model is being profiled.
    model : Model
        The model for the job.
    date : datetime
        The time this job was submitted.
    shapes : InputSpecs
        The input specs for the model.
    """

    _job_type = JobType.PROFILE

    def __init__(
        self,
        job_pb,
        owner: Client,
        device: Device,
        model: Model,
        date: datetime,
        shapes: InputSpecs,
    ):
        profile_job_pb = job_pb.profile_job
        super().__init__(
            owner=owner,
            job_id=profile_job_pb.profile_job_id,
            name=profile_job_pb.name,
            date=date,
            hub_version=job_pb.hub_version,
            options=profile_job_pb.options,
            verbose=owner.verbose,
            job_type=self._job_type,
            in_progress_states=[
                JobStatus.State.CREATED,
                JobStatus.State.PROVISIONING_DEVICE,
                JobStatus.State.MEASURING_PERFORMANCE,
            ],
        )
        self.device = device
        self.model = model
        self.shapes: InputSpecs = shapes

    def _write_profile(self, profile: Dict, dst_path: str) -> str:
        """
        Saves the profile json to disk.

        Parameters
        ----------
        dst_path:
            Dir or filename to save to.

        Returns
        -------
        : str
            The path of the saved profile json.
        """
        if os.path.isdir(dst_path):
            # Append a reasonable filename to save to.
            dst_path = os.path.join(dst_path, f"{self.name}_{self.job_id}_results.json")
            # Append suffix if destination file exists.
            dst_path, _ = api_utils.get_unique_path(dst_path)
        elif not dst_path.endswith(".json"):
            dst_path += ".json"

        with open(dst_path, "w") as file:
            json.dump(profile, file)
        print(f"Saved profile results to {dst_path}")
        return dst_path

    @overload
    def download_profile(self, filename: str) -> str: ...

    @overload
    def download_profile(self) -> Dict: ...

    def download_profile(self, filename: str | None = None) -> Dict | str:
        """
        Returns the downloaded profile, either in memory or as a file.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        filename:
            If filename is specified the profile is downloaded to file, otherwise to memory.

        Returns
        -------
        : Dict | str
            The downloaded profile results as a dict,
            or filename of a downloaded yaml file containing the profile results
        """
        status = self.wait()
        profile = {}
        if status.success:
            res_pb = _api_call(api.get_job_results, self._owner.config, self.job_id)
            if res_pb.WhichOneof("result") == "profile_job_result":
                profile = _profile_pb_to_python_dict(res_pb.profile_job_result.profile)
                if filename is not None:
                    return self._write_profile(profile, filename)
            else:
                raise UserError("The supplied job ID is not for a Profile job")

        return profile

    def download_results(self, artifacts_dir: str) -> ProfileJobResult:
        """
        Returns all the results of a job.

        This includes the profile and the compiled target model.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        artifacts_dir:
            Directory name where the job artifacts are stored.
            If the directory does not exist, it is created.

        Returns
        -------
        : ProfileJobResult
            Job results.
        """
        artifacts_dir = os.path.abspath(os.path.expanduser(artifacts_dir))
        os.makedirs(artifacts_dir, exist_ok=True)

        profile = self.download_profile()
        assert isinstance(profile, Dict)
        self._write_profile(profile, artifacts_dir)

        return ProfileJobResult(
            status=self.get_status(),
            url=self.url,
            artifacts_dir=artifacts_dir,
            profile=profile,
        )

    def wait(self, timeout: int | None = None) -> JobStatus:
        status = super().wait(timeout)
        if not self.shapes:
            profile_job_pb = _api_call(
                api.get_job, self._owner.config, job_id=self.job_id
            ).profile_job
            self.shapes = dict(
                api_utils.tensor_type_list_pb_to_list_shapes(
                    profile_job_pb.tensor_type_list
                )
            )
        return status

    def _extract_job_specific_pb(self, job_pb: api_pb.Job) -> api_pb.ProfileJob:
        return job_pb.profile_job

    def __str__(self) -> str:
        return f"Job(job_id={self.job_id}, model_id={self.model.model_id}, device={self.device})"

    def __repr__(self) -> str:
        return _class_repr_print(
            self,
            [
                "job_id",
                "url",
                ("status", self.get_status().code),
                "model",
                "name",
                "options",
                "shapes",
                "device",
                "date",
            ],
        )


class InferenceJob(Job):
    """
    Inference job for a model, user provided inputs, and a device.

    An inference job should not be constructed directly. It is constructed by the hub client
    through :py:func:`qai_hub.submit_inference_job`, or :py:func:`qai_hub.get_job`.

    Attributes
    ----------
    device : Device
        The device for this job.
    model : Model
        The model for the job.
    date : datetime
        The time this job was submitted.
    inputs : Dataset
        The inputs provided by user.
    """

    _job_type = JobType.INFERENCE

    def __init__(
        self,
        job_pb,
        owner: Client,
        device: Device,
        model: Model,
        date: datetime,
        inputs: Dataset,
    ):
        inference_job_pb = job_pb.inference_job
        super().__init__(
            owner=owner,
            job_id=inference_job_pb.inference_job_id,
            name=inference_job_pb.name,
            date=date,
            hub_version=job_pb.hub_version,
            options=inference_job_pb.options,
            verbose=owner.verbose,
            job_type=self._job_type,
            in_progress_states=[
                JobStatus.State.CREATED,
                JobStatus.State.PROVISIONING_DEVICE,
                JobStatus.State.RUNNING_INFERENCE,
            ],
        )
        self.device = device
        self.model = model
        self.inputs = inputs
        self.outputs: Dataset | None = None

    def get_output_dataset(self) -> Dataset | None:
        """
        Returns the output dataset for a job.

        If the job is not ready, this function will block until completion.

        Returns
        -------
        : Dataset | None
            The output data if the job succeeded
        """
        if not self.outputs:
            status = self.wait()
            if status.success:
                result = _api_call(api.get_job_results, self._owner.config, self.job_id)
                self.outputs = self._owner.get_dataset(
                    result.inference_job_result.output_dataset_id
                )

        return self.outputs

    @overload
    def download_output_data(self, filename: str) -> str | None: ...

    @overload
    def download_output_data(self) -> DatasetEntries | None: ...

    def download_output_data(
        self, filename: str | None = None
    ) -> DatasetEntries | str | None:
        """
        Returns the downloaded output data, either in memory or as a h5f file.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        filename:
            If filename is specified the output data is downloaded to file, otherwise to memory.

        Returns
        -------
        : DatasetEntries | str | None
            The downloaded output data, filename, or None if the job failed.
        """
        dataset = self.get_output_dataset()

        if dataset is None:
            return None
        else:
            return dataset.download(filename)

    def download_results(self, artifacts_dir: str) -> InferenceJobResult:
        """
        Returns all the results of an inference job.

        If the job is not ready, this function will block until completion.

        Parameters
        ----------
        artifacts_dir:
            Directory name where the job artifacts are stored.
            If the directory does not exist, it is created.

        Returns
        -------
        : InferenceJobResult
            Job results.
        """
        artifacts_dir = os.path.abspath(os.path.expanduser(artifacts_dir))
        os.makedirs(artifacts_dir, exist_ok=True)

        self.download_output_data(artifacts_dir)

        return InferenceJobResult(
            status=self.get_status(), url=None, artifacts_dir=artifacts_dir
        )

    def _extract_job_specific_pb(self, job_pb: api_pb.Job) -> api_pb.InferenceJob:
        return job_pb.inference_job

    def __str__(self) -> str:
        return f"Job(job_id={self.job_id}, model_id={self.model.model_id}, device={self.device}, inputs={self.inputs})"

    def __repr__(self) -> str:
        if self.get_status().failure:
            return _class_repr_print(
                self,
                [
                    "job_id",
                    ("status", self.get_status().code),
                    ("failure_reason", self.get_status().message),
                    "model",
                    "options",
                    "name",
                    "inputs",
                    "device",
                    "date",
                ],
            )

        return _class_repr_print(
            self,
            [
                "job_id",
                ("status", self.get_status().code),
                "model",
                "name",
                "inputs",
                "device",
                "date",
            ],
        )


def _model_metadata_to_dict(
    metadata_pb: api_pb.ModelMetadata,
) -> Dict[ModelMetadataKey, str]:
    metadata: Dict[ModelMetadataKey, str] = {}
    for key, value in metadata_pb.entries.items():
        enum_key = ModelMetadataKey(key)
        if enum_key != ModelMetadataKey.UNSPECIFIED:
            metadata[enum_key] = value
    return metadata


class Client:
    """
    Client object to interact with the Qualcomm AI Hub API.

    A default client, using credentials from ``~/.qai_hub/client.ini`` can be
    accessed through the ``qai_hub`` module::

        import qai_hub as hub

        # Calls Client.upload_model on a default Client instance.
        hub.upload_model("model.pt")
    """

    # Note: This class is primarily used through a default instantiation
    # through hub (e.g. import qai_hub as hub; hub.upload_model(...)). For that
    # reason, all examples and cross references should point to qai_hub for
    # documentation generation purposes.

    def __init__(self, config: ClientConfig | None = None):
        self._config = config

    @property
    def verbose(self):
        return self.config.verbose

    @property
    def config(self) -> ClientConfig:
        if self._config is None:
            try:
                self._config = _api_call(api_utils.load_default_api_config)
            except FileNotFoundError as e:
                raise UserError(
                    "Failed to load client configuration file.\n"
                    + _visible_textbox(str(e))
                )
        return self._config

    @staticmethod
    def _creation_date_from_timestamp(
        pb: (
            api_pb.Dataset
            | api_pb.CompileJob
            | api_pb.LinkJob
            | api_pb.ProfileJob
            | api_pb.InferenceJob
            | api_pb.QuantizeJob
            | api_pb.CompileJobSummary
            | api_pb.QuantizeJobSummary
            | api_pb.LinkJobSummary
            | api_pb.ProfileJobSummary
            | api_pb.InferenceJobSummary
            | api_pb.Model
        ),
    ) -> datetime:
        return datetime.fromtimestamp(pb.creation_time.seconds)

    @staticmethod
    def _expiration_date_from_timestamp(pb: api_pb.Dataset) -> datetime | None:
        if pb.permanent or not pb.HasField("expiration_time"):
            return None
        return datetime.fromtimestamp(pb.expiration_time.seconds)

    def _web_url(self, asset_type_plural: str, asset_id: str) -> str:
        # Final empty '' is to produce a trailing slash (esthetic choice)
        return urljoin(
            self.config.web_url, posixpath.join(asset_type_plural, asset_id, "")
        )

    def _web_url_of_job(self, job_id: str) -> str:
        return self._web_url("jobs", job_id)

    def _web_url_of_model(self, model_id: str) -> str:
        return self._web_url("models", model_id)

    def set_verbose(self, verbose: bool = True) -> None:
        """
        If true, API calls may print progress to standard output.

        Parameters
        ----------
        verbose:
            Verbosity.
        """
        self.config.verbose = verbose

    def _get_devices(
        self,
        name: str = "",
        os: str = "",
        attributes: str | List[str] = [],
        select: bool = False,
    ) -> List[Device]:
        def _validate_interval(os: str) -> None:
            def _is_valid_version(version: str) -> bool:
                """
                This rationalizes the difference between setuptools version 66 and earlier.
                Version 66 will throw on invalid version numbers. Previous versions do not.
                """
                try:
                    valid_type = type(Version("0"))
                    return type(Version(version)) is valid_type
                except Exception:
                    return False

            if len(os) > 0 and os[0] == "[":
                e = os.split("[", 1)
                if len(e) == 2 and len(e[0]) == 0:
                    e = e[1].split(",")
                    if len(e) == 2 and (len(e[0]) == 0 or _is_valid_version(e[0])):
                        e = e[1].rsplit(")", 1)
                        if (
                            len(e) == 2
                            and len(e[1]) == 0
                            and (len(e[0]) == 0 or _is_valid_version(e[0]))
                        ):
                            return
                raise UserError(f"Incorrectly formed OS interval {os}")

        if isinstance(attributes, str):
            attributes = [attributes]
        _validate_device_params(name, os, attributes)
        _validate_interval(os)
        devices_pb = _api_call(
            api.get_device_list, self.config, name, os, attributes, select=select
        )
        devices = []
        for dev in devices_pb.devices:
            attrs = [a for a in dev.attributes]
            devices.append(Device(dev.name, dev.os, attrs))
        return devices

    def get_devices(
        self, name: str = "", os: str = "", attributes: str | List[str] = []
    ) -> List[Device]:
        """
        Returns a list of available devices.

        The returned list of devices are compatible with the supplied
        name, os, and attributes.
        The name must be an exact match with an existing device and os can either be a
        version ("15.2") or a version range ("[14,15)").

        Parameters
        ----------
        name:
            Only devices with this exact name will be returned.
        os:
            Only devices with an OS version that is compatible with this os are returned
        attributes:
            Only devices that have all requested properties are returned.

        Returns
        -------
        device_list : List[Device]
            List of available devices, comptatible with the supplied filters.

        Examples
        --------
        ::

            import qai_hub as hub

            # Get all devices
            devices = hub.get_devices()

            # Get all devices matching this operating system
            devices = hub.get_devices(os="12")

            # Get all devices matching this chipset
            devices = hub.get_devices(attributes=["chipset:quantization-snapdragon-8gen2"])

            # Get all devices matching hardware
            devices = hub.get_devices(name="Samsung Galaxy S23")
        """
        return self._get_devices(name, os, attributes)

    def _get_device(self, device: Device) -> Device | None:
        devices = self._get_devices(device.name, device.os, device.attributes, True)
        assert len(devices) <= 1
        return devices[0] if len(devices) == 1 else None

    def get_device_attributes(self) -> List[str]:
        """
        Returns the super set of available device attributes.

        Any of these attributes can be used to filter devices when using
        :py:func:`~qai_hub.get_devices`.

        Returns
        -------
        attribute_list : List[str]
            Super set of all available device attributes.

        Examples
        --------
        ::

            import qai_hub as hub
            attributes = hub.get_device_attributes()

        """
        attrs = set()
        for d in self.get_devices():
            attrs |= set(d.attributes)
        attributes = list(attrs)
        attributes.sort()
        return attributes

    def get_frameworks(self) -> List[Framework]:
        """
        Returns a list of available ML frameworks.

        Returns
        -------
        framework_list : List[Framework]
            List of available frameworks.

        Examples
        --------
        ::

            import qai_hub as hub

            # Get all frameworks
            frameworks = hub.get_frameworks()
        """

        frameworks_pb = _api_call(api.get_framework_list, self.config)
        frameworks = []
        for fw in frameworks_pb.frameworks:
            api_tags = [t for t in fw.api_tags]
            frameworks.append(
                Framework(fw.name, fw.api_version, api_tags, fw.full_version)
            )
        return frameworks

    ## model related members ##
    def _make_model(
        self,
        model_pb: api_pb.Model,
        model: SourceModel | None = None,
        producer: Job | None = None,
    ) -> Model:
        date = self._creation_date_from_timestamp(model_pb)
        model_type = _get_source_model_type_from_model_type(model_pb.model_type)
        if producer is None and model_pb.producer_id:
            producer = self.get_job(model_pb.producer_id)

        return Model(
            self,
            model_pb.model_id,
            date,
            model_type,
            model_pb.name,
            _model_metadata_to_dict(model_pb.metadata),
            model,
            self.verbose,
            producer,
        )

    def _make_target_model(
        self, job_pb: api_pb.CompileJob | api_pb.QuantizeJob, producer: Job
    ) -> Model | None:
        if job_pb.HasField("target_model"):
            target_model = self._make_model(job_pb.target_model, producer=producer)
            if target_model is None:
                raise APIException(
                    message=f"We were unable to retrieve the target model. Please contact support at {SUPPORT_EMAIL} for help."
                )
            return target_model
        else:
            return None

    def _upload_model(
        self,
        model: (
            Model | Any | str | Path  # Any instead of SourceModel to keep mypy happy
        ),
        model_type: SourceModelType,
        name: str | None = None,
    ) -> Model:
        if isinstance(model, Model):
            return model
        suffix = _determine_model_extension(model_type)
        api_model_type = cast("api_pb.ModelType.ValueType", model_type.value)

        # Create a temporary file to be used if we need to write a model to disk before upload.
        # delete=False to be compatible with Windows
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as model_tempfile:
            file_path_to_upload = model_tempfile.name

        model_name: str | None = None
        is_directory = False
        if isinstance(model, (str, Path)):
            # TODO (#11279): Consolidate model zip logic with
            # zip_model_if_necessary used by celery compiler worker
            file_path_to_upload = os.path.expanduser(str(model))
            model_name = os.path.basename(file_path_to_upload)
            model = None
            if model_type in ZIPPABLE_MODEL_TYPES:
                # Some models are directory based assets.
                # Ensure we upload these as zipped model.
                assert suffix.endswith(".zip")
                model_suffix = suffix.rsplit(".", 1)[0]
                # Skip making ONNX files compatible to zip structure
                # if the file_path_to_upload is not a directory and
                # is not a zip file already.

                skip_zip_check = model_suffix == ".onnx" and not (
                    os.path.isdir(file_path_to_upload)
                    or file_path_to_upload.endswith(".zip")
                )
                if not skip_zip_check:
                    file_path_to_upload = _make_zipped_model_compatible(
                        file_path_to_upload, model_tempfile.name, model_suffix
                    )
                    _assert_is_valid_zipped_model(file_path_to_upload)
                    is_directory = True

        elif model_type == SourceModelType.TORCHSCRIPT:
            import torch

            torch.jit.save(model, file_path_to_upload)
            model_name = model.original_name
        elif model_type == SourceModelType.MLMODEL:
            model.save(file_path_to_upload)
            model_name = "MLModel"
        elif model_type == SourceModelType.TFLITE:
            with open(file_path_to_upload, "wb") as f:
                f.write(model)
            model_name = "TFLite"
        elif model_type == SourceModelType.ONNX:
            import onnx

            onnx.save(model, file_path_to_upload)

            model_name = "ONNX"
        elif model_type == SourceModelType.MLPACKAGE:
            with tempfile.TemporaryDirectory() as tempdir:
                mlpackage_path = os.path.join(tempdir, "model.mlpackage")
                model.save(mlpackage_path)
                zipped_model_path = zip_model(tempdir, mlpackage_path)
                shutil.copy(zipped_model_path, file_path_to_upload)
            is_directory = True
            model_name = "MLPackage"

        model_name = name or model_name
        res_pb = _api_call(
            api.create_and_upload_model,
            self.config,
            file_path_to_upload,
            name=model_name,
            model_type=api_model_type,
            verbose=self.verbose,
            is_directory=is_directory,
        )

        os.remove(model_tempfile.name)

        if res_pb.id:
            model_pb = api_pb.Model(
                model_id=res_pb.id,
                name=model_name,
                creation_time=res_pb.creation_time,
                model_type=api_model_type,
                is_directory=is_directory,
            )
            return self._make_model(model_pb, model)

        raise InternalError("Failed to upload model.")

    def upload_model(self, model: SourceModel | str, name: str | None = None) -> Model:
        """
        Uploads a model.

        Parameters
        ----------
        model:
            In memory representation or filename of the model to upload.

        name:
            Optional name of the model. If a name is not specified, it is decided
            either based on the model or the file name.

        Returns
        -------
        model : Model
            Returns a model if successful.

        Raises
        ------
        UserError
            Failure in the model input.

        Examples
        --------
        ::

            import qai_hub as hub
            import torch

            pt_model = torch.jit.load("model.pt")

            # Upload model
            model = hub.upload_model(pt_model)

            # Jobs can now be scheduled using this model
            device = hub.Device("Samsung Galaxy S23", "12")
            cjob = hub.submit_compile_job(model, device=device,
                                          name="pt_model (1, 3, 256, 256)",
                                          input_shapes=dict(x=(1, 3, 256, 256)))
            model = cjob.get_target_model()
            pjob = hub.submit_profile_job(model, device=device,
                                          name="pt_model (1, 3, 256, 256)")

        """
        model_type = _determine_model_type(model)
        return self._upload_model(model, model_type, name)

    def _make_dataset(
        self,
        dataset_pb: api_pb.Dataset,
        data: DatasetEntries | None = None,
    ) -> Dataset:
        creation_date = self._creation_date_from_timestamp(dataset_pb)
        expiration_date = self._expiration_date_from_timestamp(dataset_pb)
        return Dataset(
            self,
            dataset_id=dataset_pb.dataset_id,
            dataset_name=dataset_pb.name,
            creation_time=creation_date,
            expiration_time=expiration_date,
            verbose=self.verbose,
            data=data,
        )

    def _upload_dataset(
        self,
        inputs: Dataset | DatasetEntries | str,
        name: str | None = None,
        permanent: bool = False,
    ) -> Dataset:
        if isinstance(inputs, Dataset):
            self._check_data_entries(inputs)
            return inputs
        # delete=False to be compatible with Windows
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as file:
            path = file.name

        if isinstance(inputs, str):
            path = inputs
            data_name = os.path.basename(inputs)
            data = None
        else:
            data_name = "h5-dataset"
            data = inputs
            with h5py.File(path, "w") as h5f:
                dataset_entries_to_h5(data, h5f)

        name = name or data_name
        res_pb = _api_call(
            api.create_and_upload_dataset,
            self.config,
            path,
            name,
            verbose=self.verbose,
            permanent=permanent,
        )

        os.remove(file.name)

        if res_pb.id:
            dataset_pb = api_pb.Dataset(
                dataset_id=res_pb.id,
                creation_time=res_pb.creation_time,
                # This is left at the default value (time.seconds == 0) if the dataset is permanent.
                expiration_time=None if permanent else res_pb.expiration_time,
                permanent=permanent,
                name=name,
            )
            return self._make_dataset(dataset_pb, data)

        raise InternalError("Failed to upload data.")

    def upload_dataset(
        self, data: DatasetEntries | str, name: str | None = None
    ) -> Dataset:
        """
        Upload a dataset that expires in 30 days. A Dataset has an ordered
        named schema. For example, dict(x=..., y=...) has a different schema
        than dict(y=..., x=...).

        Parameters
        ----------
        data:
            If data is a dict, ordered string keys defines the dataset schema.
            Length of the list is the number of samples and must be the same
            for all features

            If string, it must be an h5 path (str) to a saved dataset.

        name : str | None
            Optional name of the dataset. If a name is not specified, it is decided
            either based on the data or the file name.

        Returns
        -------
        dataset : Dataset
            Returns a dataset object if successful.

        Examples
        --------
        ::

            import qai_hub as hub
            import numpy as np

            # Define dataset
            array = np.reshape(np.array(range(15)), (3, 5)).astype(np.float32)

            # Upload dataset
            hub.upload_dataset(dict(x=[array]), 'simplenet_dataset')
        """
        self._check_data_entries(data)
        return self._upload_dataset(data, name)

    def get_datasets(self, offset: int = 0, limit: int = 50) -> List[Dataset]:
        """
        Returns a list of datasets visible to you.

        Parameters
        ----------
        offset : int
            Offset the query to get even older datasets.
        limit : int
            Maximum numbers of datasets to return.

        Returns
        -------
        dataset_list: List[Dataset]
            List of datasets.

        Examples
        --------
        Fetch :py:class:`Dataset` objects for your five most recent datasets::

            import qai_hub as hub

            datasets = hub.get_datasets(limit=5)
        """
        datasets = []
        if limit > 0:
            dataset_pb = _api_call(
                api.get_dataset_list, self.config, offset=offset, limit=limit
            )
            datasets = [self._make_dataset(dataset) for dataset in dataset_pb.datasets]

        return datasets

    def get_dataset(self, dataset_id: str) -> Dataset:
        """
        Returns a dataset for a given id.

        Parameters
        ----------
        dataset_id : str
            id of a dataset.

        Returns
        -------
        dataset: Dataset
            The dataset for the id.

        Examples
        --------
        Get dataset and print information about it (granted you provide a
        valid dataset ID)::

            import qai_hub as hub

            dataset = hub.get_dataset("dabc123")
            print("Dataset information:", dataset)
        """
        dataset_pb = _api_call(api.get_dataset, self.config, dataset_id=dataset_id)
        return self._make_dataset(dataset_pb)

    def get_model(self, model_id: str) -> Model:
        """
        Returns a model for a given id.

        Parameters
        ----------
        model_id : str
            id of a model.

        Returns
        -------
        model: Model
            The model for the id.

        """
        model_pb = _api_call(api.get_model, self.config, model_id=model_id)
        return self._make_model(model_pb)

    def get_models(self, offset: int = 0, limit: int = 50) -> List[Model]:
        """
        Returns a list of models.

        Parameters
        ----------
        offset : int
            Offset the query to get even older models.
        limit : int
            Maximum numbers of models to return.

        Returns
        -------
        model_list: List[Model]
            List of models.

        Examples
        --------
        Fetch :py:class:`Model` objects for your five most recent models::

            import qai_hub as hub

            models = hub.get_models(limit=5)

        """
        models = []
        if limit > 0:
            model_list_pb = _api_call(
                api.get_model_list, self.config, offset=offset, limit=limit
            )
            for model_pb in model_list_pb.models:
                models.append(self._make_model(model_pb))
        return models

    ## job related members ##
    def _make_job(
        self,
        job_pb: api_pb.Job,
        model: Model | List[Model] | None = None,
        dataset: Dataset | None = None,
    ) -> Job | None:
        if job_pb.WhichOneof("job") == "compile_job":
            assert model is None or isinstance(model, Model)
            compile_job_pb = job_pb.compile_job
            model = model or self._make_model(compile_job_pb.model)
            shapes = dict(
                api_utils.tensor_type_list_pb_to_list_shapes(
                    compile_job_pb.tensor_type_list
                )
            )
            target_shapes = dict(
                api_utils.tensor_type_list_pb_to_list_shapes(
                    compile_job_pb.target_tensor_type_list
                )
            )
            date = self._creation_date_from_timestamp(compile_job_pb)
            device = _dev_pb_to_dev(compile_job_pb.device)
            compatible_devices = _devs_pb_to_devs(compile_job_pb.devices)
            dataset = dataset or (
                self._make_dataset(compile_job_pb.calibration_dataset)
                if compile_job_pb.calibration_dataset.dataset_id
                else None
            )

            return CompileJob(
                job_pb=job_pb,
                owner=self,
                shapes=shapes,
                device=device,
                compatible_devices=compatible_devices,
                model=model,
                date=date,
                target_shapes=target_shapes,
                calibration_dataset=dataset,
            )
        elif job_pb.WhichOneof("job") == "link_job":
            link_job_pb = job_pb.link_job
            assert model is None or isinstance(model, List)
            models = model or [self._make_model(m) for m in link_job_pb.models.models]
            date = self._creation_date_from_timestamp(link_job_pb)

            return LinkJob(
                job_pb=job_pb,
                owner=self,
                models=models,
                date=date,
            )
        elif job_pb.WhichOneof("job") == "profile_job":
            assert model is None or isinstance(model, Model)
            profile_job_pb = job_pb.profile_job
            model = model or self._make_model(profile_job_pb.model)
            shapes = dict(
                api_utils.tensor_type_list_pb_to_list_shapes(
                    profile_job_pb.tensor_type_list
                )
            )
            date = self._creation_date_from_timestamp(profile_job_pb)
            device = _dev_pb_to_dev(profile_job_pb.device)
            return ProfileJob(
                job_pb=job_pb,
                owner=self,
                shapes=shapes,
                device=device,
                model=model,
                date=date,
            )
        elif job_pb.WhichOneof("job") == "inference_job":
            assert model is None or isinstance(model, Model)
            inference_job_pb = job_pb.inference_job
            model = model or self._make_model(inference_job_pb.model)
            dataset = dataset or self._make_dataset(inference_job_pb.dataset)
            date = self._creation_date_from_timestamp(inference_job_pb)
            device = _dev_pb_to_dev(inference_job_pb.device)
            return InferenceJob(
                job_pb=job_pb,
                owner=self,
                device=device,
                model=model,
                date=date,
                inputs=dataset,
            )
        elif job_pb.WhichOneof("job") == "quantize_job":
            assert model is None or isinstance(model, Model)
            quantize_job_pb = job_pb.quantize_job
            model = model or self._make_model(quantize_job_pb.model)
            calibration_dataset = dataset or self._make_dataset(
                quantize_job_pb.calibration_dataset
            )
            date = self._creation_date_from_timestamp(quantize_job_pb)
            shapes = dict(
                api_utils.tensor_type_list_pb_to_list_shapes(
                    quantize_job_pb.tensor_type_list
                )
            )
            weights_dtype = QuantizeDtype(quantize_job_pb.weights_dtype)
            activations_dtype = QuantizeDtype(quantize_job_pb.activations_dtype)
            return QuantizeJob(
                job_pb=job_pb,
                weights_dtype=weights_dtype,
                activations_dtype=activations_dtype,
                calibration_dataset=calibration_dataset,
                owner=self,
                model=model,
                shapes=shapes,
                date=date,
            )
        else:
            return None

    @overload
    def get_job(self, job_id: str) -> Job: ...

    @overload
    def get_job(
        self, job_id: str, job_type: Literal[JobType.COMPILE]
    ) -> CompileJob: ...

    @overload
    def get_job(
        self, job_id: str, job_type: Literal[JobType.PROFILE]
    ) -> ProfileJob: ...

    @overload
    def get_job(
        self, job_id: str, job_type: Literal[JobType.INFERENCE]
    ) -> InferenceJob: ...

    @overload
    def get_job(
        self, job_id: str, job_type: Literal[JobType.QUANTIZE]
    ) -> QuantizeJob: ...

    @overload
    def get_job(self, job_id: str, job_type: Literal[JobType.LINK]) -> LinkJob: ...

    def get_job(self, job_id: str, job_type: Optional[JobType] = None) -> Job:
        """
        Returns a job for a given id.

        Parameters
        ----------
        job_id : str
            id of a job.

        job_type: Optional[JobType]
            Type of the job.
            If this is not None and the target job is not this type, this method will raise.

        Returns
        -------
        job: Job
            The job for the id.

        Examples
        --------
        Get job and print its status. The job ID is an alphanumeric string starting with `j`
        that you can get from the job's URL (`/jobs/<job ID>`).::

            import qai_hub as hub

            job = hub.get_job("jabc123")
            status = job.get_status()
        """
        job_pb = _api_call(api.get_job, self.config, job_id=job_id)
        job = self._make_job(job_pb)
        if job is None:  # probably unknown job type
            raise InternalError(f"Unable to retrieve job {job_id}")
        if job_type and job._job_type != job_type:
            raise ValueError(
                f"Requested job of type {job_type.display_name}, but got job of type {job._job_type.display_name}"
            )
        return job

    @deprecation.deprecated(
        deprecated_in="0.15.0",
        details="Please use the 'get_job_summaries' API instead.",
    )
    def get_jobs(
        self, offset: int = 0, limit: int = 50, creator: Optional[str] = None
    ) -> List[Job]:
        """
        Deprecated.

        Please use the :py:func:`qai_hub.get_job_summaries` API instead.
        """
        jobs = []
        if limit > 0:
            job_list_pb = _api_call(
                api.get_job_list,
                self.config,
                offset=offset,
                limit=limit,
                creator=creator,
            )
            for job_pb in job_list_pb.jobs:
                job = self._make_job(job_pb)
                if job is not None:
                    jobs.append(job)
        return jobs

    def _make_job_summary(self, job_summary_pb: api_pb.JobSummary) -> JobSummary | None:
        if job_summary_pb.WhichOneof("job") == "compile_job_summary":
            return CompileJobSummary._summary_from_pb(
                self,
                job_summary_pb.compile_job_summary,
            )
        elif job_summary_pb.WhichOneof("job") == "link_job_summary":
            return LinkJobSummary._summary_from_pb(
                self,
                job_summary_pb.link_job_summary,
            )
        elif job_summary_pb.WhichOneof("job") == "profile_job_summary":
            return ProfileJobSummary._summary_from_pb(
                self,
                job_summary_pb.profile_job_summary,
            )
        elif job_summary_pb.WhichOneof("job") == "inference_job_summary":
            return InferenceJobSummary._summary_from_pb(
                self,
                job_summary_pb.inference_job_summary,
            )
        elif job_summary_pb.WhichOneof("job") == "quantize_job_summary":
            return QuantizeJobSummary._summary_from_pb(
                self,
                job_summary_pb.quantize_job_summary,
            )
        else:
            return None

    def get_job_summaries(
        self,
        offset: int = 0,
        limit: int = 50,
        creator: Optional[str] = None,
        state: Union[Optional[JobStatus.State], List[JobStatus.State]] = None,
        type: Optional[JobType] = None,
    ) -> List[JobSummary]:
        """
        Returns summary information for jobs matching the specified filters.

        Parameters
        ----------
        creator: Optional[str]
            Fetch only jobs created by the specified creator. If unspecified, fetch all jobs owned by your organization.
        state: Optional[JobStatus.State] | List[JobStatus.State]
            Fetch only jobs that are currently in the specified state(s).
        type: Optional[JobType]
            Fetch only jobs of the specified type (compile, profile, etc.).
        limit : int
            Maximum number of jobs to return.
        offset : int
            How many jobs to skip over (in order to retrieve older jobs).

        Returns
        -------
        : List[JobSummary]
            List of job summaries in reverse chronological order (i.e., most recent first).

        Examples
        --------
        Print a selection of recent jobs::

            import qai_hub as hub

            running = hub.get_job_summaries(limit=10, state=hub.JobStatus.all_running_states())
            failed = hub.get_job_summaries(limit=10, state=hub.JobStatus.State.FAILED)
            more_failed = hub.get_job_summaries(offset=10, limit=10, state=hub.JobStatus.State.FAILED)
            for j in running + failed + more_failed:
                print(f"{j.job_id}: {j.name} running since {j.date}: currently {j.status.code}")
        """
        job_summaries = []
        states = (
            [state]
            if isinstance(state, JobStatus.State)
            else []
            if state is None
            else state
        )
        if limit > 0:
            job_summary_list_pb = _api_call(
                api.get_job_summary_list,
                self.config,
                offset=offset,
                limit=limit,
                creator=creator,
                states=[s.value for s in states],
                job_type=(
                    type.value
                    if type is not None
                    else api_pb.JobType.JOB_TYPE_UNSPECIFIED
                ),
            )
            for job_summary_pb in job_summary_list_pb.job_summaries:
                summary = self._make_job_summary(job_summary_pb)
                if summary is not None:
                    job_summaries.append(summary)
        return job_summaries

    def _check_input_specs(
        self,
        model_type: SourceModelType,
        input_specs: InputSpecs | None = None,
    ) -> None:
        if model_type == SourceModelType.TORCHSCRIPT:
            if input_specs is None:
                raise UserError("input_specs must be provided for TorchScript models.")
        elif model_type in [
            SourceModelType.MLMODEL,
            SourceModelType.TFLITE,
            SourceModelType.ONNX,
        ]:
            # input_specs is optional for these models. If not
            # None, the provided shapes must be compatible with the model, or
            # the server returns an error.
            pass

        if input_specs is not None:
            if not isinstance(input_specs, dict):
                raise UserError(
                    f"input_specs must be Dict[str, Tuple[Tuple[int, ...], str]]]. Got {input_specs}"
                )
            for name, spec in input_specs.items():
                if isinstance(spec[0], tuple):
                    shape = spec[0]
                else:
                    shape = spec  # type: ignore

                for dim in shape:
                    assert isinstance(dim, int)
                    if dim < 1:
                        raise UserError(
                            f"The shape of input '{name}' {shape} defines an empty tensor. "
                            "Remove the input or modify the input shape (all dim lengths should be > 0) and try again."
                        )

    _SUPPORTED_NUMPY_DTYPES: List[np.dtype] = [
        np.dtype("float16"),
        np.dtype("float32"),
        np.dtype("bool"),
        np.dtype("int8"),
        np.dtype("int16"),
        np.dtype("int32"),
        np.dtype("int64"),
        np.dtype("uint8"),
        np.dtype("uint16"),
    ]

    def _check_data_entries(self, inputs: Dataset | DatasetEntries | str) -> None:
        if isinstance(inputs, Dataset):
            if inputs.is_expired():
                raise UserError(f"Dataset {inputs.dataset_id} is expired.")
            return
        if isinstance(inputs, str):
            _, suffix = os.path.splitext(inputs)
            if suffix != ".h5":
                raise UserError('Dataset file must have ".h5" extension.')
            return
        if not isinstance(inputs, dict):
            raise UserError(
                "Dataset must be Dict[str, List[np.ndarray]] where the "
                "ordered keys define the schema, and the length of the list is "
                "the number of samples."
            )
        batchsizes: set[int] = set()
        for value in inputs.values():
            if isinstance(value, list) and all(
                isinstance(data, np.ndarray)
                and data.dtype in self._SUPPORTED_NUMPY_DTYPES
                for data in value
            ):
                batchsizes |= set([len(value)])
            else:
                raise UserError(
                    f"The values in inputs dictionary must be list of numpy arrays "
                    f"with a type in ({', '.join([x.name for x in self._SUPPORTED_NUMPY_DTYPES])})."
                )
        if len(batchsizes) > 1:
            raise UserError("Batchsize of all inputs must be the same.")

    def _check_devices(
        self,
        device: Device | List[Device],
        model_type: SourceModelType,
        compile_job: bool = False,
    ) -> List[Device]:
        if isinstance(device, Device):
            device = [device]
        devices = []
        for dev in device:
            d = self._get_device(dev)
            if d is None:
                raise UserError(f"{dev} is not available.")

            if not compile_job:
                # check if model is compatible with the device frameworks
                if (
                    model_type == SourceModelType.MLMODEL
                    or model_type == SourceModelType.MLPACKAGE
                    or model_type == SourceModelType.MLMODELC
                ) and "framework:coreml" not in d.attributes:
                    raise UserError(f"device {d} does not support Core ML model input")
                if (
                    model_type == SourceModelType.TFLITE
                    and "framework:tflite" not in d.attributes
                ):
                    raise UserError(f"device {d} does not support TFLite model input")
                if (
                    model_type == SourceModelType.ONNX
                    and "framework:onnx" not in d.attributes
                ):
                    raise UserError(f"device {d} does not support ONNX model input")
                if (
                    model_type == SourceModelType.QNN_LIB_AARCH64_ANDROID
                    or model_type == SourceModelType.QNN_LIB_X86_64_LINUX
                    or model_type == SourceModelType.QNN_CONTEXT_BINARY
                    or model_type == SourceModelType.QNN_DLC
                ) and "framework:qnn" not in d.attributes:
                    raise UserError(f"device {d} does not support QNN model input")

                # check if model is compatible with the device os
                if (
                    model_type == SourceModelType.QNN_LIB_AARCH64_ANDROID
                    and "os:android" not in d.attributes
                ):
                    raise UserError(
                        f"Aarch64 Android device {d} does not support model type {model_type}."
                    )

                # additional checks
                if (
                    model_type == SourceModelType.MLPACKAGE
                    and not _is_mlpackage_supported(d.attributes, d.os)
                ):
                    raise UserError(
                        f"device {d} does not support Core ML .mlpackage."
                        " Please either provide target iOS 15+ (or macOS 12+) for .mlpackage or .mlmodel for iOS 14 (or macOS 11) and below."
                    )

            devices.append(d)

        return devices

    @overload
    def submit_compile_job(
        self,
        model: Model | SourceModel | str | Path | None,
        device: List[Device],
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        options: str = "",
        single_compile: bool = True,
        calibration_data: Dataset | DatasetEntries | str | None = None,
        retry: bool = True,
    ) -> CompileJob | List[CompileJob]: ...

    @overload
    def submit_compile_job(
        self,
        model: Model | SourceModel | str | Path | None,
        device: Device,
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        options: str = "",
        single_compile: bool = True,
        calibration_data: Dataset | DatasetEntries | str | None = None,
        retry: bool = True,
    ) -> CompileJob: ...

    def submit_compile_job(
        self,
        model: Model | SourceModel | str | Path | None,
        device: Device | List[Device],
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        options: str = "",
        single_compile: bool = True,
        calibration_data: Dataset | DatasetEntries | str | None = None,
        retry: bool = True,
    ) -> CompileJob | List[CompileJob]:
        """
        Submits a compile job.

        Parameters
        ----------
        model:
            Model to compile. The model must be a PyTorch model or an ONNX model

        device:
            Devices for which to compile the input model.

        name:
            Optional name for the job. Job names need not be unique.

        input_specs:
            Required if `model` is a PyTorch model. Keys in `Dict` (which is
            ordered in Python 3.7+) define the input names for the target
            model (e.g., TFLite model) created from this profile job, and may
            be different from the names in PyTorch model.

            An input shape can either be a Tuple[int, ...], ie (1, 2, 3), or it
            can be a Tuple[Tuple[int, ...], str], ie ((1, 2, 3), "int32")). The
            latter form can be used to specify the type of the input.  If a type
            is not specified, it defaults to "float32". Currently, only "float32",
            "int8", "int16", "int32", "int64", "uint8", and "uint16" are accepted types.

            For example, a PyTorch module with `forward(self, x, y)` may have
            `input_specs=dict(a=(1,2), b=(1, 3))`. When using the resulting
            target model (e.g. a TFLite model) from this profile job, the
            inputs must have keys `a` and `b`, not `x` and `y`. Similarly, if
            this target model is used in an inference job
            (see :py:func:`qai_hub.submit_inference_job`), the dataset must
            have entries `a`, `b` in this order, not `x`, `y`

            If `model` is an ONNX model, `input_specs` are optional.
            `input_specs` can be used to overwrite the model's input names
            and the dynamic extents for the input shapes.
            If input_specs is not None, it must be compatible with
            the model, or the server will return an error.

        options:
            Cli-like flag options. See :ref:`api_compile_options`.

        single_compile:
            If True, submits a single compile job that creates an asset compatible with all devices.
            If False, create a compile job for each device.

        calibration_data:
            Data, Dataset, or Dataset ID to use for post-training quantization.
            PTQ will be applied to the model during translation.

        retry:
            If job creation fails due to rate-limiting, keep retrying periodically until creation succeeds.

        Returns
        -------
        job: CompileJob | List[CompileJob]
            Returns the compile jobs. Always one job if single_compile is "True",
            and possibly multiple jobs if it is "False".

        Examples
        --------
        Submit a traced Torch model for compile on an Samsung Galaxy S23::

            import qai_hub as hub
            import torch

            pt_model = torch.jit.load("mobilenet.pt")

            input_specs = (1, 3, 224, 224)

            model = hub.upload_model(pt_model)

            job = hub.submit_compile_job(model, device=hub.Device("Samsung Galaxy S23"),
                                         name="mobilenet (1, 3, 224, 224)",
                                         input_specs=dict(x=input_specs))

        For more examples, see :ref:`compile_examples`.
        """
        # Determine the model type
        model_type = _determine_model_type(model)
        if not allows_compilation(model_type):
            raise UserError("Input model type cannot be compiled.")
        devices = self._check_devices(device, model_type, compile_job=True)
        self._check_input_specs(model_type=model_type, input_specs=input_specs)
        model = self._upload_model(model, model_type=model_type)
        tensor_type_list_pb = api_utils.input_shapes_to_tensor_type_list_pb(input_specs)

        # Get Dataset
        if calibration_data:
            calibration_dataset = self._upload_dataset(calibration_data)
            calibration_dataset_pb = api_pb.Dataset(
                dataset_id=calibration_dataset.dataset_id
            )
        else:
            calibration_dataset_pb = None

        job_name = name if name else model.name
        options = options.strip()
        jobs = []
        if single_compile and len(devices) > 1:
            compatible_devices_pb = _devs_to_devs_pb(devices)
            model_pb = api_pb.Model(model_id=model.model_id)
            compile_job_pb = api_pb.CompileJob(
                model=model_pb,
                name=job_name,
                devices=compatible_devices_pb,
                tensor_type_list=tensor_type_list_pb,
                options=options,
                calibration_dataset=calibration_dataset_pb,
            )

            if retry:
                response_pb = _api_call_with_retry(
                    api.create_compile_job, self.config, compile_job_pb
                )
            else:
                response_pb = _api_call(
                    api.create_compile_job, self.config, compile_job_pb
                )

            # this fetches the job, including the selected device compiled for
            job = self.get_job(response_pb.id)
            assert isinstance(job, CompileJob)
            jobs.append(job)
            if self.verbose:
                msg = (
                    f"Scheduled compile job ({job.job_id}) successfully. To see "
                    "the status and results:\n"
                    f"    {job.url}\n"
                )
                print(msg)
        else:
            for dev in devices:
                devices_pb = _devs_to_devs_pb([dev])
                model_pb = api_pb.Model(model_id=model.model_id)
                compile_job_pb = api_pb.CompileJob(
                    model=model_pb,
                    name=job_name,
                    devices=devices_pb,
                    tensor_type_list=tensor_type_list_pb,
                    options=options,
                    calibration_dataset=calibration_dataset_pb,
                )
                response_pb = _api_call(
                    api.create_compile_job, self.config, compile_job_pb
                )
                job = self.get_job(response_pb.id)
                assert isinstance(job, CompileJob)
                jobs.append(job)
                if self.verbose:
                    msg = (
                        f"Scheduled compile job ({job.job_id}) successfully. To see "
                        "the status and results:\n"
                        f"    {job.url}\n"
                    )
                    print(msg)

        return jobs[0] if len(jobs) == 1 else jobs

    def submit_quantize_job(
        self,
        model: Model | SourceModel | str | Path | None,
        calibration_data: Dataset | DatasetEntries | str,
        weights_dtype: QuantizeDtype = QuantizeDtype.INT8,
        activations_dtype: QuantizeDtype = QuantizeDtype.INT8,
        name: str | None = None,
        options: str = "",
    ) -> QuantizeJob:
        """
        Submits a quantize job. Input model must be onnx. The resulting target model
        on a completed job will be a quantized onnx model in QDQ format.

        Parameters
        ----------
        model:
            Model to quantize. The model must be a PyTorch model or an ONNX model

        calibration_data:
            Data, Dataset, or Dataset ID used to calibrate quantization parameters.

        name:
            Optional name for the job. Job names need not be unique.

        weights_dtype:
            The data type to which weights will be quantized.

        activations_dtype:
            The data type to which activations will be quantized.

        options:
            Cli-like flag options. See :ref:`api_quantize_options`.

        Returns
        -------
        job: QuantizeJob
            Returns the quantize job.

        Examples
        --------
        Submit an onnx model for quantization::

            import numpy as np
            import qai_hub as hub

            model_file = "mobilenet_v2.onnx"
            calibration_data = {"t.1": [np.random.randn(1, 3, 224, 224).astype(np.float32)]}
            job = hub.submit_quantize_job(
                model_file,
                calibration_data,
                weights_dtype=hub.QuantizeDtype.INT8,
                activations_dtype=hub.QuantizeDtype.INT8,
                name="mobilenet",
            )
        """
        if weights_dtype != QuantizeDtype.INT8 and activations_dtype not in [
            QuantizeDtype.INT8,
            QuantizeDtype.INT16,
        ]:
            raise ValueError(
                "Weights must be INT8 and activations must be INT8 or INT16."
            )
        # Determine the model type
        model_type = _determine_model_type(model)
        if model_type != SourceModelType.ONNX:
            raise UserError("Input model must be ONNX.")
        model = self._upload_model(model, model_type=model_type)

        # Get Dataset
        calibration_dataset = self._upload_dataset(calibration_data)
        calibration_dataset_pb = api_pb.Dataset(
            dataset_id=calibration_dataset.dataset_id
        )

        job_name = name if name else model.name
        model_pb = api_pb.Model(model_id=model.model_id)
        quantize_job_pb = api_pb.QuantizeJob(
            model=model_pb,
            name=job_name,
            weights_dtype=weights_dtype.value,
            activations_dtype=activations_dtype.value,
            calibration_dataset=calibration_dataset_pb,
            options=options,
        )

        response_pb = _api_call(api.create_quantize_job, self.config, quantize_job_pb)

        # This fetches the job
        job = self.get_job(response_pb.id)
        assert isinstance(job, QuantizeJob)
        if self.verbose:
            msg = (
                f"Scheduled quantize job ({job.job_id}) successfully. To see "
                "the status and results:\n"
                f"    {job.url}\n"
            )
            print(msg)

        return job

    def submit_link_job(
        self,
        models: List[Model],
        name: str | None = None,
        options: str = "",
    ) -> LinkJob:
        """
        Submits a link job.

        A link job combines multiple models into a single one with multiple
        graphs. This is particularly useful if the input models contain
        overlapping weights, since the weights will be shared between the
        graphs. This feature is exclusive to QNN context binaries.

        To profile or inference a multi-graph QNN context binary, please use
        ``--qnn_options context_enable_graphs=<graph name>`` to select the graph.

        Parameters
        ----------
        models:
            Models to link. Each model in the list must be an AI Hub compiled QNN context binary model.

        name:
            Optional name for the job. Job names need not be unique.

        options:
            Cli-like flag options. See :ref:`api_link_options`.

        Returns
        -------
        job: LinkJob
            Returns the link job.

        """
        if len(models) < 2:
            raise UserError("A link job takes at least two input models.")
        models_pb = api_pb.ModelList(total_query_count=len(models))
        for model in models:
            if (
                model.producer is None
                or not isinstance(model.producer, CompileJob)
                or model.model_type != SourceModelType.QNN_CONTEXT_BINARY
            ):
                raise UserError(
                    "Supplied models must all be an AI Hub-compiled QNN context binary (from single-graph compile jobs)"
                )
            models_pb.models.append(api_pb.Model(model_id=model.model_id))
        job_name = name if name else models[-1].name
        link_job_pb = api_pb.LinkJob(
            models=models_pb,
            name=job_name,
            options=options.strip(),
        )
        response_pb = _api_call(api.create_link_job, self.config, link_job_pb)
        link_job_pb.link_job_id = response_pb.id
        link_job_pb.creation_time.CopyFrom(response_pb.creation_time)
        job_pb = api_pb.Job(link_job=link_job_pb)
        job = self._make_job(job_pb, models)
        assert isinstance(job, LinkJob)
        return job

    @overload
    def submit_profile_job(
        self,
        model: Model | TargetModel | str | Path | None,
        device: Device,
        name: str | None = None,
        options: str = "",
        retry: bool = True,
    ) -> ProfileJob: ...

    @overload
    def submit_profile_job(
        self,
        model: Model | TargetModel | str | Path | None,
        device: List[Device],
        name: str | None = None,
        options: str = "",
        retry: bool = True,
    ) -> List[ProfileJob]: ...

    def submit_profile_job(
        self,
        model: Model | TargetModel | str | Path | None,
        device: Device | List[Device],
        name: str | None = None,
        options: str = "",
        retry: bool = True,
    ) -> ProfileJob | List[ProfileJob]:
        """
        Submits a profile job.

        Parameters
        ----------
        model:
            Model to profile. Must not be a PyTorch model.

        device:
            Devices on which to run the profile job.

        name:
            Optional name for the job. Job names need not be unique.

        options:
            Cli-like flag options. See :ref:`api_profile_and_inference_options`.

        retry:
            If job creation fails due to rate-limiting, keep retrying periodically until creation succeeds.

        Returns
        -------
        job: ProfileJob | List[ProfileJob]
            Returns the profile jobs.

        Examples
        --------
        Submit a tflite model for profiling on a Samsung Galaxy S23::

            import qai_hub as hub

            model = hub.upload_model("mobilenet.tflite")

            job = hub.submit_profile_job(model,
                                         device=hub.Device("Samsung Galaxy S23"),
                                         name="mobilenet (1, 3, 224, 224)")

        For more examples, see :ref:`profile_examples`.
        """
        # Determine the model type
        model_type = _determine_model_type(model)
        if requires_compilation(model_type):
            raise UserError(
                "Supplied model type cannot be profiled until is has been compiled."
            )
        devices = self._check_devices(device, model_type)
        model = self._upload_model(model, model_type=model_type)
        job_name = name if name else model.name
        jobs = []
        for dev in devices:
            dev_pb = _dev_to_dev_pb(dev)
            model_pb = api_pb.Model(model_id=model.model_id)
            profile_job_pb = api_pb.ProfileJob(
                model=model_pb,
                name=job_name,
                device=dev_pb,
                options=options.strip(),
            )
            if retry:
                response_pb = _api_call_with_retry(
                    api.create_profile_job, self.config, profile_job_pb
                )
            else:
                response_pb = _api_call(
                    api.create_profile_job, self.config, profile_job_pb
                )

            profile_job_pb.profile_job_id = response_pb.id
            profile_job_pb.creation_time.CopyFrom(response_pb.creation_time)
            job_pb = api_pb.Job(profile_job=profile_job_pb)
            job = self._make_job(job_pb, model)
            assert isinstance(job, ProfileJob)
            jobs.append(job)
            if self.verbose:
                msg = (
                    f"Scheduled profile job ({job.job_id}) successfully. To see "
                    "the status and results:\n"
                    f"    {job.url}\n"
                )
                print(msg)

        return jobs[0] if len(jobs) == 1 else jobs

    @overload
    def submit_inference_job(
        self,
        model: Model | TargetModel | str | Path | None,
        device: Device,
        inputs: Dataset | DatasetEntries | str,
        name: str | None = None,
        options: str = "",
        retry: bool = True,
    ) -> InferenceJob: ...

    @overload
    def submit_inference_job(
        self,
        model: Model | TargetModel | str | Path | None,
        device: List[Device],
        inputs: Dataset | DatasetEntries | str,
        name: str | None = None,
        options: str = "",
        retry: bool = True,
    ) -> List[InferenceJob]: ...

    def submit_inference_job(
        self,
        model: Model | TargetModel | str | Path | None,
        device: Device | List[Device],
        inputs: Dataset | DatasetEntries | str,
        name: str | None = None,
        options: str = "",
        retry: bool = True,
    ) -> InferenceJob | List[InferenceJob]:
        """
        Submits an inference job.

        Parameters
        ----------
        model:
            Model to run inference with. Must be one of the following:
            (1) Model object from a compile job via :py:func:`qai_hub.CompileJob.get_target_model`
            (2) Any TargetModel
            (3) Path to Any TargetModel

        device:
            Devices on which to run the job.

        inputs:
            If `Dataset`, it must have matching schema  to `model`. For
            example, if `model` is a target model from a compile job, and the
            compile job was submitted with `input_shapes=dict(a=(1, 2), b=(1,
            3))`. The dataset must also be created with
            `dict(a=<list_of_np_array>, b=<list_of_np_array>)`. See
            :py:func:`qai_hub.submit_compile_job` for details.

            If `Dict`, it's uploaded as a new `Dataset`, equivalent to
            calling :py:func:`qai_hub.upload_dataset` with arbitrary name.
            Note that `Dict` is ordered in Python 3.7+ and we rely on the
            order to match the schema. See the paragraph above for an example.

            If str, it's a h5 path to Dataset.

        name:
            Optional name for the job. Job names need not be unique.

        options:
            Cli-like flag options. See :ref:`api_profile_and_inference_options`.

        retry:
            If job creation fails due to rate-limiting, keep retrying periodically until creation succeeds.

        Returns
        -------
        job: InferenceJob | List[InferenceJob]
            Returns the inference jobs.

        Examples
        --------
        Submit a TFLite model for inference on a Samsung Galaxy S23::

            import qai_hub as hub
            import numpy as np

            # TFlite model path
            tflite_model = "squeeze_net.tflite"

            # Setup input data
            input_tensor = np.random.random((1, 3, 227, 227)).astype(np.float32)

            # Submit inference job
            job = hub.submit_inference_job(
                tflite_model,
                device=hub.Device("Samsung Galaxy S23"),
                name="squeeze_net (1, 3, 227, 227)",
                inputs=dict(image=[input_tensor]),
            )

            # Load the output data into a dictionary of numpy arrays
            output_tensors = job.download_output_data()

        For more examples, see :ref:`inference_examples`.
        """

        # Determine the model type
        model_type = _determine_model_type(model)
        if requires_compilation(model_type):
            raise UserError(
                "Supplied model type cannot be profiled until is has been compiled."
            )

        devices = self._check_devices(device, model_type)
        self._check_data_entries(inputs)
        model = self._upload_model(model, model_type=model_type)
        dataset = self._upload_dataset(inputs)

        job_name = name if name else model.name
        jobs = []
        for dev in devices:
            dev_pb = _dev_to_dev_pb(dev)
            model_pb = api_pb.Model(model_id=model.model_id)
            dataset_pb = api_pb.Dataset(dataset_id=dataset.dataset_id)
            inference_job_pb = api_pb.InferenceJob(
                model=model_pb,
                name=job_name,
                device=dev_pb,
                dataset=dataset_pb,
                options=options.strip(),
            )

            if retry:
                response_pb = _api_call_with_retry(
                    api.create_inference_job, self.config, inference_job_pb
                )
            else:
                response_pb = _api_call(
                    api.create_inference_job, self.config, inference_job_pb
                )

            inference_job_pb.inference_job_id = response_pb.id
            inference_job_pb.creation_time.CopyFrom(response_pb.creation_time)
            job_pb = api_pb.Job(inference_job=inference_job_pb)
            job = self._make_job(job_pb, model, dataset)
            assert isinstance(job, InferenceJob)
            jobs.append(job)
            if self.verbose:
                msg = (
                    f"Scheduled inference job ({job.job_id}) successfully. To see "
                    "the status and results:\n"
                    f"    {job.url}\n"
                )
                print(msg)

        return jobs[0] if len(jobs) == 1 else jobs

    @overload
    def submit_compile_and_profile_jobs(
        self,
        model: Model | SourceModel | TargetModel | str | Path | None,
        device: Device,
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        compile_options: str = "",
        profile_options: str = "",
        single_compile: bool = True,
        calibration_data: Dataset | DatasetEntries | str | None = None,
        retry: bool = True,
    ) -> Tuple[CompileJob | None, ProfileJob | None]: ...

    @overload
    def submit_compile_and_profile_jobs(
        self,
        model: Model | SourceModel | TargetModel | str | Path | None,
        device: List[Device],
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        compile_options: str = "",
        profile_options: str = "",
        single_compile: bool = True,
        calibration_data: Dataset | DatasetEntries | str | None = None,
        retry: bool = True,
    ) -> List[Tuple[CompileJob | None, ProfileJob | None]]: ...

    def submit_compile_and_profile_jobs(
        self,
        model: Model | SourceModel | TargetModel | str | Path | None,
        device: Device | List[Device],
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        compile_options: str = "",
        profile_options: str = "",
        single_compile: bool = True,
        calibration_data: Dataset | DatasetEntries | str | None = None,
        retry: bool = True,
    ) -> (
        Tuple[CompileJob | None, ProfileJob | None]
        | List[Tuple[CompileJob | None, ProfileJob | None]]
    ):
        """
        Submits a compilation job and a profile job.

        Parameters
        ----------
        model:
            Model to profile.

        device:
            Devices on which to run the jobs.

        name:
            Optional name for both the jobs. Job names need not be unique.

        input_specs:
            Required if `model` is a PyTorch model. Keys in `Dict` (which is
            ordered in Python 3.7+) define the input names for the target
            model (e.g., TFLite model) created from this profile job, and may
            be different from the names in PyTorch model.

            An input shape can either be a Tuple[int, ...], ie (1, 2, 3), or it
            can be a Tuple[Tuple[int, ...], str], ie ((1, 2, 3), "int32")). The
            latter form can be used to specify the type of the input.  If a type
            is not specified, it defaults to "float32". Currently, only "float32",
            "int8", "int16", "int32", "int64", "uint8", and "uint16" are accepted types.

            For example, a PyTorch module with `forward(self, x, y)` may have
            `input_specs=dict(a=(1,2), b=(1, 3))`. When using the resulting
            target model (e.g. a TFLite model) from this profile job, the
            inputs must have keys `a` and `b`, not `x` and `y`. Similarly, if
            this target model is used in an inference job
            (see :py:func:`qai_hub.submit_inference_job`), the dataset must
            have entries `a`, `b` in this order, not `x`, `y`

            If `model` is an ONNX model, `input_specs` are optional.
            `input_specs` can be used to overwrite the model's input names
            and the dynamic extents for the input shapes.
            If input_specs is not None, it must be compatible with
            the model, or the server will return an error.

        single_compile:
            If True, create a single compile job on a single device compatible with all devices.
            The CompileJob in every tuple in the returned List will point the same AI Hub job.

            If False, create a compile job for each device.

        compile_options:
            Cli-like flag options for the compile job. See :ref:`api_compile_options`.

        profile_options:
            Cli-like flag options for the profile job. See :ref:`api_profile_and_inference_options`.

        calibration_data:
            Data, Dataset, or Dataset ID to use for post-training quantization.
            PTQ will be applied to the model during translation.

        retry:
            If job creation fails due to rate-limiting, keep retrying periodically until creation succeeds.

        Returns
        -------
        jobs: Tuple[CompileJob | None, ProfileJob | None] | List[Tuple[CompileJob | None, ProfileJob | None]
            Returns a tuple of CompileJob and ProfileJob.

        Examples
        --------
        Submit a traced Torch model for profiling as a QNN Model Library on a
        Samsung Galaxy S23::

            import qai_hub as hub
            import torch

            pt_model = torch.jit.load("mobilenet.pt")

            input_shapes = (1, 3, 224, 224)

            model = hub.upload_model(pt_model)

            jobs = hub.submit_compile_and_profile_jobs(
                model, device=hub.Device("Samsung Galaxy 23"),
                name="mobilenet (1, 3, 224, 224)",
                input_specs=dict(x=input_shapes),
                compile_options="--target_runtime qnn_lib_aarch64_android"
            )

        For more examples, see :ref:`compile_examples` and ref:`profile_examples`.
        """
        devices = [device] if isinstance(device, Device) else device
        num_jobs = len(devices)
        model_type = _determine_model_type(model)
        if not allows_compilation(model_type):
            # Ignoring type because the above predicate ensures that model is a TargetModel
            pjobs: Any = self.submit_profile_job(model, devices, name, profile_options)  # type: ignore
            if isinstance(pjobs, ProfileJob):
                pjobs = [pjobs]
            assert isinstance(pjobs, List)
            cjobs: Any = [None] * num_jobs
        else:
            cjobs = self.submit_compile_job(
                model,
                devices,
                name,
                input_specs,
                compile_options.strip(),
                single_compile=single_compile,
                calibration_data=calibration_data,
                retry=retry,
            )
            if isinstance(cjobs, CompileJob):
                cjobs = [cjobs] * num_jobs
            assert isinstance(cjobs, List)
            pjobs = []
            for cjob, dev in zip(cjobs, devices):
                assert isinstance(cjob, CompileJob)
                target_model = cjob.get_target_model()
                if target_model is not None:
                    job_name = name if name else cjob.name
                    pjob = self.submit_profile_job(
                        target_model,
                        dev,
                        job_name,
                        profile_options.strip(),
                        retry=retry,
                    )
                else:
                    pjob = None
                pjobs.append(pjob)
        jobs = list(zip(cjobs, pjobs))
        return jobs[0] if len(jobs) == 1 else jobs

    def submit_compile_and_quantize_jobs(
        self,
        model: Model | SourceModel | str | Path | None,
        device: Device,
        calibration_data: Dataset | DatasetEntries | str,
        name: str | None = None,
        input_specs: InputSpecs | None = None,
        compile_options: str = "",
        quantize_options: str = "",
        weights_dtype: QuantizeDtype = QuantizeDtype.INT8,
        activations_dtype: QuantizeDtype = QuantizeDtype.INT8,
        retry: bool = True,
    ) -> Tuple[CompileJob, QuantizeJob]:
        """
        Compiles a model to onnx and runs a quantize job on the produced onnx model.

        The input model can be PyTorch or ONNX.

        Parameters
        ----------
        model:
            Model to compile and quantize.

        device:
            Device for which to compile the onnx model.

        name:
            Optional name for both the jobs. Job names need not be unique.

        input_specs:
            Required if `model` is a PyTorch model. Keys in `Dict` (which is
            ordered in Python 3.7+) define the input names for the target
            model (e.g., TFLite model) created from this profile job, and may
            be different from the names in PyTorch model.

            An input shape can either be a Tuple[int, ...], ie (1, 2, 3), or it
            can be a Tuple[Tuple[int, ...], str], ie ((1, 2, 3), "int32")). The
            latter form can be used to specify the type of the input.  If a type
            is not specified, it defaults to "float32". Currently, only "float32",
            "int8", "int16", "int32", "int64", "uint8", and "uint16" are accepted types.

            For example, a PyTorch module with `forward(self, x, y)` may have
            `input_specs=dict(a=(1,2), b=(1, 3))`. When using the resulting
            target model (e.g. a TFLite model) from this profile job, the
            inputs must have keys `a` and `b`, not `x` and `y`. Similarly, if
            this target model is used in an inference job
            (see :py:func:`qai_hub.submit_inference_job`), the dataset must
            have entries `a`, `b` in this order, not `x`, `y`

            If `model` is an ONNX model, `input_specs` are optional.
            `input_specs` can be used to overwrite the model's input names
            and the dynamic extents for the input shapes.
            If input_specs is not None, it must be compatible with
            the model, or the server will return an error.

        compile_options:
            Cli-like flag options for the compile job. See :ref:`api_compile_options`.

        quantize_options:
            Cli-like flag options for the quantize job. See :ref:`api_quantize_options`.

        calibration_data:
            Data, Dataset, or Dataset ID to use during calibration in the quantize job.

        weights_dtype:
            The data type to which weights will be quantized.

        activations_dtype:
            The data type to which activations will be quantized.

        retry:
            If compile job creation fails due to rate-limiting, keep retrying periodically until creation succeeds.

        Returns
        -------
        jobs: Tuple[CompileJob, QuantizeJob]
            Returns a tuple of CompileJob and ProfileJob.

        Examples
        --------
        Submit an torch model for compile and quantize::

            import torch
            import numpy as np
            import qai_hub as hub

            pt_model = torch.jit.load("mobilenet_v2.pt")
            input_shapes = (1, 3, 224, 224)

            calibration_data = {"image": [np.random.randn(*input_shapes).astype(np.float32)]}
            job = hub.submit_compile_and_quantize_jobs(
                pt_model,
                hub.Device("Samsung Galaxy S23"),
                calibration_data,
                input_specs={"image": (input_shapes, "float32")},
                weights_dtype=hub.QuantizeDtype.INT8,
                activations_dtype=hub.QuantizeDtype.INT8,
                name="mobilenet",
            )
        """
        model_type = _determine_model_type(model)
        if not allows_compilation(model_type):
            raise UserError("Input model type cannot be compiled.")

        if "--target_runtime" in compile_options:
            raise UserError(
                "Cannot set --target_runtime, it will be automatically set to ONNX."
            )
        compile_job = self.submit_compile_job(
            model,
            device,
            name,
            input_specs,
            compile_options.strip() + " --target_runtime onnx",
            retry=retry,
        )

        assert isinstance(compile_job, CompileJob)
        target_model = compile_job.get_target_model()
        assert target_model is not None
        job_name = name if name else compile_job.name

        quantize_job = self.submit_quantize_job(
            target_model,
            calibration_data,
            weights_dtype,
            activations_dtype,
            job_name,
            options=quantize_options,
        )
        return (compile_job, quantize_job)


__all__ = [
    "Error",
    "InternalError",
    "UserError",
    "Device",
    "Framework",
    "Model",
    "Job",
    "CompileJob",
    "QuantizeJob",
    "LinkJob",
    "ProfileJob",
    "InferenceJob",
    "JobSummary",
    "CompileJobSummary",
    "QuantizeJobSummary",
    "LinkJobSummary",
    "ProfileJobSummary",
    "InferenceJobSummary",
    "ModelMetadataKey",
    "SourceModelType",
    "JobResult",
    "CompileJobResult",
    "QuantizeJobResult",
    "LinkJobResult",
    "ProfileJobResult",
    "InferenceJobResult",
    "QuantizeDtype",
    "JobStatus",
    "JobType",
    "Dataset",
    "InputSpecs",
]
