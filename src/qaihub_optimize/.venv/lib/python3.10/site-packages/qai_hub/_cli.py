import argparse
import configparser
import json
import logging
import os
import shutil
import textwrap
import warnings
from getpass import getpass
from typing import List, Optional, Union

from prettytable import PrettyTable

import qai_hub as hub

from .api_utils import QAIHUB_CLIENT_ENV, get_config_path, get_token

_HUB_URL = "https://app.aihub.qualcomm.com"


def _get_maybe_dataset(dataset_id: Optional[str]) -> Optional[hub.Dataset]:
    if dataset_id and dataset_id != "none":
        return hub.get_dataset(dataset_id)
    else:
        return None


def set_config_path(profile_name: str) -> None:
    os.environ[QAIHUB_CLIENT_ENV] = f"~/.qai_hub/{profile_name}.ini"


def add_device_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--device",
        action="store",
        help="Device name.",
        required=False,
    )
    parser.add_argument(
        "--device-attr",
        action="append",
        help="Device attribute. This may be repeated for multiple attributes.",
        required=False,
    )
    parser.add_argument(
        "--device-os",
        action="store",
        help="Device OS version.",
        required=False,
    )


def add_job_arguments(
    job_parser: argparse.ArgumentParser,
    job_type: str,
) -> None:
    # Arguments for all jobs
    job_parser.add_argument(
        "--clone",
        metavar="JOB_ID",
        action="store",
        help="Uses this job as template (any argument can be overridden).",
        required=False,
    )
    job_parser.add_argument(
        "--name",
        action="store",
        help="Optional job name.",
        required=False,
    )
    job_parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for job to finish",
        required=False,
    )

    # Jobs that include compilation
    if job_type in ["compile", "compile_and_profile"]:
        job_parser.add_argument(
            "--model",
            action="store",
            help="Model ID of source framework model in AI Hub or path to a source framework model file on disk.",
            required=False,
        )
        job_parser.add_argument(
            "--compile_options",
            action="store",
            help="Compile Job options.",
            required=False,
        )
        job_parser.add_argument(
            "--input_specs",
            action="store",
            help="Input specs for compile jobs. Example: \"{'x': (1, 3, 224, 224)}\" and \"{'x': ((24, 48), 'int32')}\"",
            required=False,
        )
        job_parser.add_argument(
            "--calibration_data",
            action="store",
            help="Dataset ID of quantization calibration data. Accepts 'none' to mean no calibration data.",
            required=False,
        )

    # Jobs that only profile
    if job_type in ["profile"]:
        job_parser.add_argument(
            "--model",
            action="store",
            help="Model ID of target model in AI Hub or path to a target model file on disk.",
            required=False,
        )

    # Jobs that include profiling
    if job_type in ["profile", "compile_and_profile"]:
        job_parser.add_argument(
            "--profile_options",
            action="store",
            help="Profile Job options.",
            required=False,
        )

    if job_type in ["link"]:
        job_parser.add_argument(
            "--models",
            nargs="+",
            action="store",
            help="Model IDs of AI Hub-compiled QNN context binaries.",
            required=False,
        )
        job_parser.add_argument(
            "--link_options",
            action="store",
            help="Link Job options.",
            required=False,
        )


def add_config_arguments(config_parser: argparse.ArgumentParser) -> None:
    config_parser.add_argument(
        "--api_token",
        action="store",
        help="API token (from the accounts tab in the settings page).",
        required=False,
    )
    config_parser.add_argument(
        "--email",
        action="store",
        help=argparse.SUPPRESS,
        required=False,
    )
    config_parser.add_argument(
        "--password",
        action="store",
        help=argparse.SUPPRESS,
        required=False,
    )
    config_parser.add_argument(
        "--api_url",
        action="store",
        help=argparse.SUPPRESS,
        default=_HUB_URL,
    )
    config_parser.add_argument(
        "--web_url",
        action="store",
        help=argparse.SUPPRESS,
        default=_HUB_URL,
    )
    config_parser.add_argument("--verbose", action="store_true")
    config_parser.add_argument("--no-verbose", dest="verbose", action="store_false")
    config_parser.set_defaults(verbose=True)


def add_list_devices_parser(subparsers: argparse._SubParsersAction) -> None:
    list_devices_parser = subparsers.add_parser(
        "list-devices", help="List available devices"
    )
    add_device_arguments(list_devices_parser)


def add_list_frameworks_parser(subparsers: argparse._SubParsersAction) -> None:
    list_frameworks_parser = subparsers.add_parser(
        "list-frameworks", help="List available frameworks"
    )
    list_frameworks_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )


def add_config_parser(subparsers: argparse._SubParsersAction) -> None:
    config_parser = subparsers.add_parser("configure", help="Configure qai-hub client")
    add_config_arguments(config_parser)


def add_upload_model_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    cmd = "upload-model"
    cmd_name = f"qai-hub {cmd}"
    epilog = textwrap.dedent(
        f"""
    examples:

      # Upload Torchscript model
      {cmd_name} --model resnet50.pt
    """
    )

    upload_model_parser = subparsers.add_parser(
        cmd,
        help="Upload model",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    upload_model_parser.add_argument(
        "--model",
        action="store",
        help="Path to local model to upload to AI Hub",
        required=True,
    )
    upload_model_parser.add_argument(
        "--name",
        action="store",
        help="Optional model name.",
        required=False,
    )


def add_submit_compile_and_profile_parser(
    subparsers: argparse._SubParsersAction,
) -> None:
    cmd = "submit-compile-and-profile-jobs"
    cmd_name = f"qai-hub {cmd}"
    epilog = textwrap.dedent(
        f"""
    examples:

      # Submit Torchscript model
      {cmd_name} --model resnet50.pt --input_specs '{{"x": (1, 3, 224, 224)}}' --device "Samsung Galaxy S23"

      # Re-submit existing job
      {cmd_name} --clone jnp1wlnlg
    """
    )

    profile_parser = subparsers.add_parser(
        cmd,
        help="Submit compile + profile job",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_device_arguments(profile_parser)
    add_job_arguments(profile_parser, job_type="compile_and_profile")


def add_submit_profile_parser(subparsers: argparse._SubParsersAction) -> None:
    cmd = "submit-profile-job"
    cmd_name = f"qai-hub {cmd}"
    epilog = textwrap.dedent(
        f"""
    examples:
      # Profile model previously compiled on Hub using Model ID
      {cmd_name} --model m9egnr5ox --device "Samsung Galaxy S23"

      # Profile using TFLite model from disk
      {cmd_name} --model resnet50.tflite --device "Samsung Galaxy S23"

      # Profile with the most recent version of the QAIRT framework
      {cmd_name} --model resnet50.tflite --profile_options " --qairt_framework latest"

      # Re-submit existing job
      {cmd_name} --clone jnp1wlnlg

      # Re-submit with modifications
      {cmd_name} --clone jnp1wlnlg --profile_options " --compute_unit cpu"
    """
    )

    profile_parser = subparsers.add_parser(
        cmd,
        help="Submit profile job",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_device_arguments(profile_parser)
    add_job_arguments(profile_parser, job_type="profile")


def add_submit_compile_parser(subparsers: argparse._SubParsersAction):
    cmd = "submit-compile-job"
    cmd_name = f"qai-hub {cmd}"
    epilog = textwrap.dedent(
        f"""
    examples:

      # Compile Torchscript model for Android
      {cmd_name} --model resnet50.pt --device "Samsung Galaxy S23"

      # Compile for a specific runtime
      {cmd_name} --model resnet50.pt --device "Samsung Galaxy S23" --compile_options " --target_runtime onnx"

      # Compile with a specific version of QAIRT
      {cmd_name} --model resnet50.pt --compile_options " --qairt_version latest"

      # Re-submit existing job
      {cmd_name} --clone jnp1wlnlg

      # Re-submit with modifications
      {cmd_name} --clone jnp1wlnlg --compile_options " --quantize_full_type int8"
    """
    )

    compile_parser = subparsers.add_parser(
        cmd,
        help="Submit compile job",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_device_arguments(compile_parser)
    add_job_arguments(compile_parser, job_type="compile")


def add_submit_link_parser(subparsers: argparse._SubParsersAction):
    cmd = "submit-link-job"
    cmd_name = f"qai-hub {cmd}"
    epilog = textwrap.dedent(
        f"""
    examples:

      # Link models
      {cmd_name} --models m9egnr5ox m2rmd0vn3
    """
    )

    link_parser = subparsers.add_parser(
        cmd,
        help="Submit link job",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_device_arguments(link_parser)
    add_job_arguments(link_parser, job_type="link")


def get_cli_parser() -> argparse.ArgumentParser:
    # Main CLI arguments
    main_parser = argparse.ArgumentParser(description="CLI interface for qai-hub")
    subparsers = main_parser.add_subparsers(dest="command")

    # arguments
    main_parser.add_argument(
        "--profile",
        action="store",
        help="Alternate client profile. Translates to ~/.qai_hub/PROFILE.ini.",
        required=False,
    )
    main_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
        required=False,
    )

    add_config_parser(subparsers)

    add_list_devices_parser(subparsers)
    add_list_frameworks_parser(subparsers)
    add_upload_model_parser(subparsers)
    add_submit_compile_and_profile_parser(subparsers)
    add_submit_profile_parser(subparsers)
    add_submit_compile_parser(subparsers)
    add_submit_link_parser(subparsers)

    # arguments for configure
    # Return the argument parser
    return main_parser


def configure(config_data: dict, tetra_config_ini_path: str) -> None:
    # Make a backup if it exists
    if os.path.exists(tetra_config_ini_path):
        backup_tetra_config = f"{tetra_config_ini_path}.bak"
        warnings.warn(
            f"Overwriting configuration: {tetra_config_ini_path} (previous configuration saved to {backup_tetra_config})"
        )
        shutil.copy(tetra_config_ini_path, backup_tetra_config)

    # Create a configuration
    config = configparser.ConfigParser()
    for section in config_data:
        config.add_section(section)
        for key, value in config_data[section].items():
            config.set(section, key, value)

    # Create and save the file
    os.makedirs(os.path.dirname(tetra_config_ini_path), exist_ok=True)
    with open(tetra_config_ini_path, "w") as configfile:
        config.write(configfile)

    # Let the user know they are ready to go.
    print(f"qai-hub configuration saved to {tetra_config_ini_path}")
    print("=" * 20, f"{tetra_config_ini_path}", "=" * 20)
    with open(tetra_config_ini_path, "r") as configfile:
        print(configfile.read())


class DeviceParams:
    name: str = ""
    os: str = ""
    attrs: List[str] = []

    def is_default(self):
        return not self.name and not self.os and not self.attrs


def parse_model(model: str) -> Union[hub.Model, str]:
    # Check if path
    if os.path.exists(model):
        return model
    else:
        import re

        pattern = re.compile("m[a-z0-9]+")
        if pattern.fullmatch(model) is not None:
            return hub.get_model(model)
        else:
            raise RuntimeError(
                f"Model {model} must be either a valid path to file on disk or a valid model ID on AI Hub."
            )


def parse_device(args: argparse.Namespace) -> DeviceParams:
    params = DeviceParams()

    if args.device:
        params.name = args.device
    if args.device_os:
        params.os = args.device_os
    if args.device_attr:
        params.attrs = args.device_attr

    return params


def parse_input_specs(
    input_specs_str: str,
) -> Optional[hub.InputSpecs]:
    if not input_specs_str:
        return None

    input_specs = None
    if input_specs_str:
        try:
            input_specs = eval(input_specs_str)
        except Exception:
            raise RuntimeError(
                f"Unable to parse input_specs as dictionary: {input_specs_str}"
            )
    return input_specs


def _extract_attrs(key: str, attrs: Union[str, List[str]]) -> str:
    if isinstance(attrs, str):
        return attrs

    extracted = []
    for attr in attrs:
        if attr.startswith(key + ":"):
            extracted.append(attr.split(":")[1])
    return ", ".join(extracted)


def list_devices(device: DeviceParams) -> None:
    devices = hub.get_devices(
        name=device.name,
        os=device.os,
        attributes=device.attrs,
    )
    table = PrettyTable()
    table.field_names = [
        "Device",
        "OS",
        "Vendor",
        "Type",
        "Chipset",
        "CLI Invocation",
    ]
    for d in devices:
        attr_dict = dict([i.split(":") for i in d.attributes])
        table.add_row(
            [
                d.name,
                f"{attr_dict.get('os', '').title()} {d.os}",
                f"{attr_dict.get('vendor', '').title()}",
                _extract_attrs("format", d.attributes).title(),
                _extract_attrs("chipset", d.attributes),
                f'--device "{d.name}" --device-os {d.os}',
            ]
        )
    print(table)


def list_frameworks(output_json: bool) -> None:
    frameworks = hub.get_frameworks()
    if output_json:
        data = []
        for fw in frameworks:
            data.append(
                {
                    "framework": fw.name,
                    "api_version": fw.api_version,
                    "api_tags": [x for x in fw.api_tags],
                    "full_version": fw.full_version,
                }
            )
        print(json.dumps(data))
    else:
        table = PrettyTable()
        table.field_names = [
            "Framework",
            "API Version",
            "API Tags",
            "Full Version",
        ]
        for fw in frameworks:
            table.add_row(
                [
                    fw.name,
                    fw.api_version,
                    fw.api_tags,
                    fw.full_version,
                ]
            )
        print(table)


def get_device(device: DeviceParams) -> hub.Device:
    return hub.Device(name=device.name, os=device.os, attributes=device.attrs)


def run_cli(args: argparse.Namespace) -> None:
    if args.profile:
        set_config_path(args.profile)

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logger = logging.getLogger("qai-hub")
        logger.info("Enabling verbose logging.")

        if args.command != "configure":
            hub.set_verbose(True)

    clone_job: Optional[hub.Job] = None
    jobs: List[Optional[hub.Job]] = []
    compile_options: str = ""
    profile_options: str = ""
    link_options: str = ""
    calibration_data: Optional[hub.Dataset] = None
    name: Optional[str] = None
    model: Union[hub.Model, str] = ""
    input_specs: Optional[hub.InputSpecs] = None

    if args.command == "configure":
        # Data to write to the configuration file
        if args.api_token is None:
            if not args.email:
                args.email = input("Qualcomm AI Hub account email address: ")
            if not args.password:
                args.password = getpass()
            args.api_token = get_token(args.api_url, args.email, args.password)

        config_data: dict = {
            "api": {
                "api_token": args.api_token,
                "api_url": args.api_url,
                "web_url": args.web_url,
                "verbose": str(args.verbose),
            }
        }

        # Location for the config file
        config_path: str = get_config_path()

        # Configure
        configure(config_data, config_path)

    elif args.command == "list-devices":
        list_devices(parse_device(args))

    elif args.command == "list-frameworks":
        list_frameworks(args.json)

    elif args.command == "upload-model":
        if not os.path.exists(args.model):
            raise ValueError(f"File {args.model} does not exist.")

        model = hub.upload_model(
            model=args.model,
            name=args.name,
        )
        print(repr(model))

    elif args.command == "submit-compile-and-profile-jobs":
        if args.clone is not None:
            raise ValueError("Cloned job has to be a compile or profile job")
        if args.compile_options is not None:
            compile_options = args.compile_options
        if args.calibration_data is not None:
            calibration_data = _get_maybe_dataset(args.calibration_data)
        if args.profile_options is not None:
            profile_options = args.profile_options
        if args.name:
            name = args.name

        device_params = parse_device(args)
        device = get_device(device_params)

        if args.input_specs:
            input_specs = parse_input_specs(args.input_specs)

        if args.model:
            model = parse_model(args.model)
        else:
            raise ValueError("--model must be specified.")

        job_pair_list = hub.submit_compile_and_profile_jobs(
            model=model,
            name=name,
            input_specs=input_specs,
            device=device,
            compile_options=compile_options,
            profile_options=profile_options,
            calibration_data=calibration_data,
        )
        if isinstance(job_pair_list, list):
            jobs += [job for job_pair in job_pair_list for job in job_pair]

    elif args.command == "submit-profile-job":
        if args.clone is not None:
            maybe_clone_job = hub.get_job(args.clone)
            if isinstance(maybe_clone_job, hub.ProfileJob):
                clone_job = maybe_clone_job
            else:
                raise ValueError("Cloned job has to be a profile job")

        if args.profile_options is not None:
            profile_options = args.profile_options
        elif clone_job is not None:
            profile_options = clone_job.options
        if args.name:
            name = args.name
        elif clone_job is not None:
            name = clone_job.name

        device_params = parse_device(args)
        # Only fall-back to clone job device if no device info is provided
        if device_params.is_default() and clone_job is not None:
            assert isinstance(
                clone_job, (hub.CompileJob, hub.ProfileJob, hub.InferenceJob)
            )
            device = clone_job.device
        else:
            device = get_device(device_params)

        if args.model:
            model = parse_model(args.model)
        elif clone_job is not None:
            assert isinstance(
                clone_job, (hub.CompileJob, hub.ProfileJob, hub.InferenceJob)
            )
            model = clone_job.model
        else:
            raise ValueError("--model (or --clone) must be specified.")

        profile_job = hub.submit_profile_job(
            model=model,
            name=name,
            device=device,
            options=profile_options,
        )
        if isinstance(profile_job, list):
            jobs += profile_job
        elif isinstance(profile_job, hub.Job):
            jobs.append(profile_job)

    elif args.command == "submit-compile-job":
        if args.clone is not None:
            maybe_clone_job = hub.get_job(args.clone)
            if isinstance(maybe_clone_job, hub.CompileJob):
                clone_job = maybe_clone_job
            else:
                raise ValueError("Cloned job has to be a compile job")

        if args.calibration_data is not None:
            calibration_data = _get_maybe_dataset(args.calibration_data)
        elif clone_job is not None:
            assert isinstance(clone_job, hub.CompileJob)
            calibration_data = clone_job.calibration_dataset

        if args.compile_options is not None:
            compile_options = args.compile_options
        elif clone_job is not None:
            compile_options = clone_job.options

        if args.name:
            name = args.name
        elif clone_job is not None:
            name = clone_job.name

        device_params = parse_device(args)
        # Only fall-back to clone job device if no device info is provided
        if device_params.is_default() and clone_job is not None:
            assert isinstance(
                clone_job, (hub.CompileJob, hub.ProfileJob, hub.InferenceJob)
            )
            device = clone_job.device
        else:
            device = get_device(device_params)

        if args.input_specs:
            input_specs = parse_input_specs(args.input_specs)
        elif clone_job is not None:
            assert isinstance(clone_job, hub.CompileJob)
            input_specs = clone_job.shapes

        if args.model:
            model = parse_model(args.model)
        elif clone_job is not None:
            assert isinstance(
                clone_job, (hub.CompileJob, hub.ProfileJob, hub.InferenceJob)
            )
            model = clone_job.model
        else:
            raise ValueError("--model (or --clone) must be specified.")

        compile_job = hub.submit_compile_job(
            model=model,
            name=name,
            device=device,
            options=compile_options,
            input_specs=input_specs,
            calibration_data=calibration_data,
        )
        if isinstance(compile_job, list):
            jobs += compile_job
        elif isinstance(compile_job, hub.Job):
            jobs.append(compile_job)

    elif args.command == "submit-link-job":
        if args.clone is not None:
            maybe_clone_job = hub.get_job(args.clone)
            if isinstance(maybe_clone_job, hub.LinkJob):
                clone_job = maybe_clone_job
            else:
                raise ValueError("Cloned job has to be a link job")

        models: List[hub.Model] = []
        if args.models is not None:
            for model_str in args.models:
                model = parse_model(model_str)
                if isinstance(model, str):
                    raise ValueError(
                        "Cannot enter local model into --models: Link job inputs must be AI Hub-compiled models."
                    )
                else:
                    models.append(model)
        elif clone_job is not None:
            assert isinstance(clone_job, hub.LinkJob)
            for model in clone_job.models:
                assert isinstance(model, hub.Model)
                models.append(model)
        else:
            raise ValueError("Either --models or --clone are required.")

        if args.name:
            name = args.name
        elif clone_job is not None:
            name = clone_job.name

        if args.link_options is not None:
            link_options = args.link_options
        elif clone_job is not None:
            link_options = clone_job.options

        link_job = hub.submit_link_job(
            models=models,
            name=name,
            options=link_options,
        )
        if isinstance(link_job, list):
            jobs += link_job
        elif isinstance(link_job, hub.Job):
            jobs.append(link_job)

    else:
        get_cli_parser().print_help()

    if jobs and args.wait:
        for job in jobs:
            if job is not None:
                job.wait()


def main() -> None:
    # Parse command line arguments
    main_parser = get_cli_parser()
    args = main_parser.parse_args()
    run_cli(args)
