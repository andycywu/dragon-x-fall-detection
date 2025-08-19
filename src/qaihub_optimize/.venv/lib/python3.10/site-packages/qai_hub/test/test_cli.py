import configparser
import os
import tempfile
from datetime import datetime
from unittest import mock

import pytest

import qai_hub
from qai_hub._cli import configure, get_cli_parser, parse_input_specs, run_cli


@pytest.fixture
def config_data():
    config_data = {
        "api": {
            "api_token": "API_TOKEN_fbajc",
            "api_url": "https://staging.tetra.ai",
            "web_url": "https://staging.tetra.ai",
        }
    }
    return config_data


def validate_good_configuration(config):
    assert config.sections() == ["api"]
    assert config.get("api", "api_url") == "https://staging.tetra.ai"
    assert config.get("api", "web_url") == "https://staging.tetra.ai"
    assert config.get("api", "api_token") == "API_TOKEN_fbajc"
    assert set(config["api"].keys()) == set(["api_url", "web_url", "api_token"])


def test_good_configuration(config_data):
    ini_path = tempfile.NamedTemporaryFile(suffix="config.ini").name
    configure(config_data, ini_path)

    # Now read the configuration back
    config = configparser.ConfigParser()
    config.read(ini_path)

    # Validate
    validate_good_configuration(config)


def test_backup_config(config_data):
    ini_path = tempfile.NamedTemporaryFile(suffix="config.ini").name
    configure(config_data, ini_path)
    config_data["api"]["api_token"] = "NEW_API_TOKEN_fbajc"
    configure(config_data, ini_path)

    # Now read the configuration back
    config_bak = configparser.ConfigParser()
    config_bak.read(f"{ini_path}.bak")
    validate_good_configuration(config_bak)

    # Validate
    config = configparser.ConfigParser()
    config.read(ini_path)
    assert config.get("api", "api_token") == "NEW_API_TOKEN_fbajc"


@mock.patch.dict(os.environ, {"QAIHUB_CLIENT_INI": ""}, clear=True)
def test_named_profile():
    args = get_cli_parser().parse_args(["--profile", "dummy"])
    run_cli(args)
    assert os.environ["QAIHUB_CLIENT_INI"] == "~/.qai_hub/dummy.ini"


@pytest.mark.parametrize(
    "input_args, expected_args",
    [
        ([], dict(name="", os="", attributes=[])),
        (
            ["--device", "Apple iPhone 14"],
            dict(name="Apple iPhone 14", os="", attributes=[]),
        ),
        (
            ["--device-os", "ios"],
            dict(name="", os="ios", attributes=[]),
        ),
        (
            ["--device-attr", "chipset:apple-a15"],
            dict(name="", os="", attributes=["chipset:apple-a15"]),
        ),
        (
            ["--device-attr", "chipset:apple-a15", "--device-attr", "framework:coreml"],
            dict(name="", os="", attributes=["chipset:apple-a15", "framework:coreml"]),
        ),
    ],
)
def test_list_devices(input_args, expected_args):
    devices = [
        qai_hub.Device(
            name="Apple iPhone 14",
            os="16.1",
            attributes=[
                "vendor:apple",
                "os:ios",
                "framework:coreml",
                "chipset:apple-a15",
                "format:phone",
            ],
        ),
        qai_hub.Device(
            name="Apple iPhone 14 Plus",
            os="16.1",
            attributes=[
                "vendor:apple",
                "os:ios",
                "framework:coreml",
                "chipset:apple-a15",
                "format:phone",
            ],
        ),
    ]
    mock_get_devices = mock.create_autospec(qai_hub.get_devices, return_value=devices)
    with mock.patch("qai_hub.get_devices", mock_get_devices):
        args = get_cli_parser().parse_args(["list-devices"] + input_args)
        run_cli(args)
        mock_get_devices.assert_called_once_with(**expected_args)


def test_list_frameworks():
    frameworks = [
        qai_hub.Framework(
            name="QAIRT",
            api_version="1.2",
            api_tags=[
                "default",
                "latest",
            ],
            full_version="1.2.3",
        ),
    ]

    mock_get_frameworks = mock.create_autospec(
        qai_hub.get_frameworks, return_value=frameworks
    )
    with mock.patch("qai_hub.get_frameworks", mock_get_frameworks):
        args = get_cli_parser().parse_args(["list-frameworks"])
        run_cli(args)

        mock_get_frameworks.assert_called_once_with()


@pytest.mark.parametrize(
    "extra_args,expected_results,raises_message",
    [
        (["--model", "does_not_exist.txt"], {}, ".*does not exist.*"),
        (["--model", "FILE"], {"model": "FILE", "name": None}, None),
        (
            ["--model", "FILE", "--name", "model_name"],
            {"model": "FILE", "name": "model_name"},
            None,
        ),
    ],
)
def test_upload_model(extra_args, expected_results, raises_message):
    with tempfile.NamedTemporaryFile(suffix=".tflite") as fp:
        model_file_path = fp.name
        mock_upload_model = mock.create_autospec(
            qai_hub.upload_model, return_value=None
        )
        with mock.patch("qai_hub.upload_model", mock_upload_model):
            extra_args = [v if v != "FILE" else model_file_path for v in extra_args]
            args = get_cli_parser().parse_args(
                ["upload-model", "--model", model_file_path] + extra_args
            )
            if raises_message is None:
                run_cli(args)
                mock_upload_model.assert_called_once_with(
                    **{
                        k: v if v != "FILE" else model_file_path
                        for k, v in expected_results.items()
                    }
                )
            else:
                with pytest.raises(ValueError, match=raises_message):
                    run_cli(args)


@pytest.fixture
def mock_dataset():
    return mock.Mock(
        spec=qai_hub.Dataset,
        dataset_id="dabcd1234",
    )


@pytest.mark.parametrize(
    "input_args, expected_results",
    [
        (
            [
                "--device",
                "android",
                "--model",
                "model.tflite",
                "--compile_options",
                "blah",
                "--profile_options",
                "blah",
            ],
            dict(
                model="model.tflite",
                name=None,
                compile_options="blah",
                profile_options="blah",
                input_specs=None,
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            ["--device", "android", "--model", "model.tflite"],
            dict(
                model="model.tflite",
                name=None,
                compile_options="",
                profile_options="",
                input_specs=None,
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--device",
                "android",
                "--model",
                "model.tflite",
                "--input_specs",
                "{'a': (1, 224, 224), 'b': (20, 20)}",
            ],
            dict(
                model="model.tflite",
                name=None,
                compile_options="",
                profile_options="",
                input_specs={"a": (1, 224, 224), "b": (20, 20)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--device",
                "android",
                "--model",
                "model.tflite",
                "--input_specs",
                "{'a': (1, 224, 224)}",
            ],
            dict(
                model="model.tflite",
                name=None,
                compile_options="",
                profile_options="",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--device",
                "android",
                "--model",
                "model.tflite",
                "--name",
                "fancy_tflite",
                "--input_specs",
                "{'a': (1, 224, 224)}",
            ],
            dict(
                model="model.tflite",
                name="fancy_tflite",
                compile_options="",
                profile_options="",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
    ],
)
def test_compile_and_profile_jobs(input_args, expected_results):
    mock_submit_compile_and_profile_jobs = mock.create_autospec(
        qai_hub.submit_compile_and_profile_jobs, mock_dataset, return_value=None
    )

    def mock_get_job(job_id):
        assert job_id == "dabcd1234"
        ret = mock.Mock(
            spec=qai_hub.ProfileJob,
            job_id=job_id,
            device=qai_hub.Device("android"),
            model="model.tflite",  # string for ease of testing
            target_model=None,
            date=datetime.now(),
            options="",
            verbose=False,
            shapes={"a": (1, 224, 224)},
        )
        # Mock uses name= argument for something else
        ret.name = "fancy_tflite"
        return ret

    with mock.patch(
        "qai_hub.submit_compile_and_profile_jobs",
        mock_submit_compile_and_profile_jobs,
    ), mock.patch("qai_hub.get_job", mock_get_job), mock.patch(
        "os.path.exists", return_value=True
    ):
        args = get_cli_parser().parse_args(
            ["submit-compile-and-profile-jobs"] + input_args,
        )
        run_cli(args)
        mock_submit_compile_and_profile_jobs.assert_called_once_with(**expected_results)


@pytest.mark.parametrize(
    "input_args, expected_results",
    [
        (
            [
                "--device",
                "android",
                "--model",
                "model.pt",
                "--input_specs",
                "{'a': (1, 224, 224)}",
            ],
            dict(
                model="model.pt",
                name=None,
                options="",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--device",
                "android",
                "--model",
                "model.pt",
                "--name",
                "fancy_pt",
                "--input_specs",
                "{'a': (1, 224, 224)}",
            ],
            dict(
                model="model.pt",
                name="fancy_pt",
                options="",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--clone",
                "jabcd1234",
                "--name",
                "fancy_pt_override",
            ],
            dict(
                model="model.pt",
                name="fancy_pt_override",
                options="--target_runtime tflite",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--clone",
                "jabcd1234",
                "--compile_options",
                "",
            ],
            dict(
                model="model.pt",
                name="fancy_pt",
                options="",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android"),
                calibration_data=None,
            ),
        ),
        (
            [
                "--clone",
                "jabcd1234",
                "--model",
                "model_override.pt",
                "--compile_options",
                " --quantize_full_type int8",
                "--device",
                "android_override",
                "--calibration_data",
                "dabcd1234",
            ],
            dict(
                model="model_override.pt",
                name="fancy_pt",
                options=" --quantize_full_type int8",
                input_specs={"a": (1, 224, 224)},
                device=qai_hub.Device("android_override"),
                calibration_data=mock_dataset,
            ),
        ),
    ],
)
def test_compile_job(input_args, expected_results):
    mock_submit_compile_job = mock.create_autospec(
        qai_hub.submit_compile_job, return_value=None
    )

    job_id = "jabcd1234"
    mock_job = mock.Mock(
        spec=qai_hub.CompileJob,
        job_id=job_id,
        device=qai_hub.Device("android"),
        model="model.pt",  # string for ease of testing
        target_model=None,
        date=datetime.now(),
        options="--target_runtime tflite",
        verbose=False,
        shapes={"a": (1, 224, 224)},
        calibration_dataset=None,
    )
    # Mock uses name= argument for something else
    mock_job.name = "fancy_pt"

    def mock_get_dataset(dataset_id):
        assert dataset_id == "dabcd1234"
        return mock_dataset

    with mock.patch("qai_hub.submit_compile_job", mock_submit_compile_job), mock.patch(
        "qai_hub.get_job", return_value=mock_job
    ), mock.patch("qai_hub.get_dataset", mock_get_dataset), mock.patch(
        "os.path.exists", return_value=True
    ):
        args = get_cli_parser().parse_args(
            ["submit-compile-job"] + input_args,
        )
        run_cli(args)
        wait = expected_results.pop("wait", False)
        mock_submit_compile_job.assert_called_once_with(**expected_results)
        if wait:
            mock_job.wait.assert_called()
        else:
            mock_job.wait.assert_not_called()


@pytest.mark.parametrize(
    "input_args, expected_results",
    [
        (
            [
                "--device",
                "android",
                "--model",
                "model.tflite",
                "--profile_options",
                "blah",
            ],
            dict(
                model="model.tflite",
                name=None,
                options="blah",
                device=qai_hub.Device("android"),
            ),
        ),
        (
            ["--device", "android", "--model", "model.tflite"],
            dict(
                model="model.tflite",
                name=None,
                options="",
                device=qai_hub.Device("android"),
            ),
        ),
        (
            [
                "--clone",
                "jabcd1234",
                "--name",
                "fancy_tflite_override",
            ],
            dict(
                model="model.tflite",
                name="fancy_tflite_override",
                options="",
                device=qai_hub.Device("android"),
            ),
        ),
        (
            [
                "--clone",
                "jabcd1234",
                "--model",
                "model_override.tflite",
                "--profile_options",
                "--compute_unit cpu",
                "--device",
                "android_override",
                "--wait",
            ],
            dict(
                model="model_override.tflite",
                name="fancy_tflite",
                options="--compute_unit cpu",
                device=qai_hub.Device("android_override"),
                wait=True,
            ),
        ),
    ],
)
def test_profile_job(input_args, expected_results):
    mock_job = mock.Mock(
        spec=qai_hub.ProfileJob,
        job_id="jabcd1234",
        device=qai_hub.Device("android"),
        model="model.tflite",  # string for ease of testing
        target_model=None,
        date=datetime.now(),
        options="",
        verbose=False,
    )
    mock_job.name = "fancy_tflite"

    mock_submit_profile_job = mock.create_autospec(
        qai_hub.submit_profile_job,
        return_value=mock_job,
    )

    with mock.patch("qai_hub.submit_profile_job", mock_submit_profile_job), mock.patch(
        "qai_hub.get_job", return_value=mock_job
    ), mock.patch("os.path.exists", return_value=True):
        args = get_cli_parser().parse_args(
            ["submit-profile-job"] + input_args,
        )
        run_cli(args)
        wait = expected_results.pop("wait", False)
        mock_submit_profile_job.assert_called_once_with(**expected_results)
        if wait:
            mock_job.wait.assert_called()
        else:
            mock_job.wait.assert_not_called()


@pytest.mark.parametrize(
    "input_args, expected_results",
    [
        (
            [
                "--models",
                "m0abcd1234",
                "m1abcd1234",
            ],
            dict(
                models=[
                    mock.Mock(spec=qai_hub.Model, model_id="m0abcd1234"),
                    mock.Mock(spec=qai_hub.Model, model_id="m1abcd1234"),
                ],
                name=None,
                options="",
            ),
        ),
        (
            [
                "--models",
                "m0abcd1234",
                "m1abcd1234",
                "m2abcd1234",
                "--name",
                "mylink",
                "--link_options",
                "",
                "--wait",
            ],
            dict(
                models=[
                    mock.Mock(spec=qai_hub.Model, model_id="m0abcd1234"),
                    mock.Mock(spec=qai_hub.Model, model_id="m1abcd1234"),
                    mock.Mock(spec=qai_hub.Model, model_id="m2abcd1234"),
                ],
                name="mylink",
                options="",
                wait=True,
            ),
        ),
    ],
)
def test_link_job(input_args, expected_results):
    def mock_get_model(model_id):
        return [
            model for model in expected_results["models"] if model.model_id == model_id
        ][0]

    job_id = "jabcd1234"
    mock_job = mock.Mock(
        spec=qai_hub.LinkJob,
        job_id=job_id,
        models=expected_results["models"],
        date=datetime.now(),
        options="",
        verbose=False,
    )
    mock_job.name = "mylink"

    def mock_get_dataset(dataset_id):
        assert dataset_id == "dabcd1234"
        return mock_dataset

    mock_submit_link_job = mock.create_autospec(
        qai_hub.submit_link_job,
        return_value=mock_job,
    )

    with mock.patch("qai_hub.submit_link_job", mock_submit_link_job), mock.patch(
        "qai_hub.get_job", return_value=mock_job
    ), mock.patch("qai_hub.get_model", mock_get_model):
        args = get_cli_parser().parse_args(
            ["submit-link-job"] + input_args,
        )
        run_cli(args)
        wait = expected_results.pop("wait", False)
        mock_submit_link_job.assert_called_once_with(**expected_results)
        if wait:
            mock_job.wait.assert_called()
        else:
            mock_job.wait.assert_not_called()


@pytest.mark.parametrize(
    "input_args, exp_input_specs",
    [
        ("{'a': [1, 224, 224]}", {"a": [1, 224, 224]}),
        ("{'a': [1, 224, 224], 'b': (2, 20)}", {"a": [1, 224, 224], "b": (2, 20)}),
    ],
)
def test_parse_input_specs(input_args, exp_input_specs):
    args = get_cli_parser().parse_args(
        [
            "submit-compile-job",
            "--input_specs",
            input_args,
            "--device",
            "android",
            "--model",
            "model.tflite",
        ]
    )
    input_specs = parse_input_specs(args.input_specs)
    assert input_specs == exp_input_specs
