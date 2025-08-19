import os
import tempfile
from pathlib import Path
from shutil import make_archive
from zipfile import ZipFile

import pytest

from qai_hub.util.zipped_model import (
    SUPPORTED_ZIPPED_MODEL_ASSETS,
    make_zipped_model_compatible,
    unzip_model,
    zip_model,
)


def test_zip_model_file():
    with tempfile.TemporaryDirectory() as tempdir:
        package_file = os.path.join(tempdir, "model1.txt")
        Path(package_file).touch()
        archived_path = zip_model(tempdir, package_file)

        assert os.path.exists(archived_path)
        assert archived_path.endswith(".txt.zip")
        with ZipFile(archived_path, "r") as archive_file:
            assert archive_file.namelist()[0] == os.path.basename("model1.txt")


@pytest.mark.parametrize("suffix", [".xyz.mlmodelc", ""])
def test_zip_model_dir(suffix):
    with tempfile.TemporaryDirectory() as tempdir:
        package_dir = os.path.join(tempdir, "model1" + suffix)
        os.makedirs(package_dir)
        archived_path = zip_model(tempdir, package_dir)

        assert os.path.exists(archived_path)
        assert archived_path.endswith(suffix + ".zip")
        with ZipFile(archived_path, "r") as archive_file:
            assert archive_file.namelist() == [
                os.path.join(os.path.basename(package_dir), "")
            ]


def test_zip_model_file_with_filename_from_cur_dir():
    with tempfile.TemporaryDirectory() as tempdir:
        filename = "model1.txt"
        package_file = os.path.join(tempdir, filename)
        Path(package_file).touch()
        cur_path = os.getcwd()

        os.chdir(tempdir)
        archived_path = zip_model(tempdir, filename)
        os.chdir(cur_path)

        assert os.path.exists(archived_path)
        assert archived_path.endswith(".txt.zip")
        with ZipFile(archived_path, "r") as archive_file:
            assert archive_file.namelist()[0] == os.path.basename("model1.txt")


@pytest.mark.parametrize("asset_suffix", sorted(list(SUPPORTED_ZIPPED_MODEL_ASSETS)))
def test_unzip_model(asset_suffix):
    with tempfile.TemporaryDirectory() as tempdir:
        model_name = str(Path("model1").with_suffix(asset_suffix))
        package_dir = os.path.join(tempdir, model_name)
        os.makedirs(package_dir)

        zip_path = os.path.join(tempdir, "input_zipped_model")
        zipped_model_path = make_archive(
            zip_path, "zip", os.path.dirname(package_dir), os.path.basename(package_dir)
        )

        # Create output directory
        output_model_path = os.path.join(tempdir, "output_zipped_path")
        output_model_path = unzip_model(zipped_model_path, output_model_path)
        assert os.path.basename(output_model_path) == model_name


def test_unzip_model_raises_one_asset_expected():
    with tempfile.TemporaryDirectory() as tempdir:
        model_name = "model1.mlmodelc"
        package_dir = os.path.join(tempdir, model_name)
        os.makedirs(package_dir)
        Path(tempdir, "model2.mlmodelc").touch()

        zip_path = os.path.join(tempdir, "input_zipped_model")
        zipped_model_path = make_archive(zip_path, "zip", tempdir)

        # Create output directory
        output_model_path = os.path.join(tempdir, "output_zipped_path")
        with pytest.raises(
            ValueError, match=r".*Expecting only one model asset at base path.*"
        ):
            unzip_model(zipped_model_path, output_model_path)


@pytest.mark.parametrize("asset_suffix", sorted(list(SUPPORTED_ZIPPED_MODEL_ASSETS)))
def test_make_zipped_model_compatible(asset_suffix):
    with tempfile.TemporaryDirectory() as tempdir:
        model_name = str(Path("model1").with_suffix(asset_suffix))
        package_dir = os.path.join(tempdir, "tmp_model", model_name)
        os.makedirs(package_dir)
        Path(tempdir, "tmp_model", "xyz").touch()

        zip_path = os.path.join(tempdir, "input_zipped_model")
        zipped_model_path = make_archive(zip_path, "zip", os.path.dirname(package_dir))

        with ZipFile(zipped_model_path) as zipped_file:
            names = zipped_file.namelist()
            assert model_name + "/" in names
            assert "xyz" in names

        output_zip_path = os.path.join(tempdir, "output_model.zip")
        output_zip_path = make_zipped_model_compatible(
            zipped_model_path, output_zip_path
        )

        with ZipFile(output_zip_path) as zipped_file:
            names = zipped_file.namelist()
            assert model_name + "/" in names
            # "xyz" is removed from zipped file
            assert "xyz" not in names


def test_make_zipped_model_compatible_raises_one_asset_expected():
    # Ensure at least two assets are supported as zipped model
    assert len(SUPPORTED_ZIPPED_MODEL_ASSETS) > 1

    supported_assets = sorted(list(SUPPORTED_ZIPPED_MODEL_ASSETS))
    with tempfile.TemporaryDirectory() as tempdir:
        package_dir = os.path.join(tempdir, "model1" + supported_assets[0])
        os.makedirs(package_dir)
        package_dir = os.path.join(tempdir, "model2" + supported_assets[1])
        os.makedirs(package_dir)
        Path(tempdir, "xyz").touch()

        zip_path = os.path.join(tempdir, "input_zipped_model")
        # NOTE: not providing base path, so that both model1 and model2 are included in zipped
        # model
        zipped_model_path = make_archive(zip_path, "zip", os.path.dirname(package_dir))

        # Create output directory
        output_model_path = os.path.join(tempdir, "output_zipped_path.zip")
        with pytest.raises(
            ValueError, match=r".*Archived model must have only one base level.*"
        ):
            make_zipped_model_compatible(zipped_model_path, output_model_path)
