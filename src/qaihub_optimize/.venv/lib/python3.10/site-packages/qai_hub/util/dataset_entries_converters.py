from typing import List

import h5py
import numpy as np

from qai_hub.public_rest_api import DatasetEntries


def _h5_data_to_np_array(h5f_input_data) -> List[np.ndarray]:
    """
    Converts a single h5 data point to an array or list of arrays.
    """
    # Get the np array for each batch stored in the h5 file.
    curr_batches = []
    for i in range(0, h5f_input_data.attrs["batch_count"]):
        curr_batches.append(np.array(h5f_input_data[f"batch_{i}"]))

    # Attach the array (or just the first element) to the
    # name of this input.
    return curr_batches


def dataset_entries_to_h5(data: DatasetEntries, h5f: h5py.File) -> h5py.File:
    """
    Converts dataset data to an uploadable h5 file.

    Parameters
    ----------
    data: DatasetEntries
        The data to write to the h5 file.
    h5f : h5py.File
        h5 file that the data should be written to

    Returns
    -------
    : h5py.File
        The same file passed to this function as h5f.
    """
    for data_index, (key, data_list) in enumerate(data.items()):
        # Single datapoint was provided for validation
        if not isinstance(data_list, list):
            data_list = [data_list]

        # Populate h5 file for each input
        # TODO(#2017): Add a test for the formatting the client produces.
        for arr_index, arr in enumerate(data_list):
            h5f.create_dataset(
                name=f"data/{data_index}/batch_{arr_index}",
                data=arr,
                compression="gzip",
            )

        # If the dict is not ordered, the input order is not meaningful.
        if isinstance(data, dict):
            h5f[f"data/{data_index}"].attrs["order"] = data_index

        h5f[f"data/{data_index}"].attrs["name"] = key
        h5f[f"data/{data_index}"].attrs["batch_count"] = len(data_list)

    return h5f


def h5_to_dataset_entries(h5f: h5py.File) -> DatasetEntries:
    """
    Converts the data in the provided h5 file to DatasetEntries.

    Parameters
    ----------
    h5f : h5py.File
        h5 file that will be read to populate the dataset data.

    Returns
    -------
    : DatasetEntries
        The dataset in the h5 file converted to a python-readable format.
    """
    h5f_data = h5f["data"]
    assert isinstance(h5f_data, h5py.Group)
    input_count = len(h5f_data.items())
    if input_count == 0:
        return dict()  # type: ignore

    data: DatasetEntries
    if h5f_data["0"].attrs.get("order") is not None:
        # Inputs have an order.
        #
        # This will throw if some inputs have an order
        # and others do not.
        #
        # It will also throw if the order of inputs
        # is not continuous (eg. input 3 of 5 is missing).
        #
        data = dict()  # type: ignore

        # Loop through the input order range, so we can
        # insert the inputs in the correct order.
        for i in range(0, len(h5f_data.items())):
            found_index = False
            for _, curr_data in h5f_data.items():
                if curr_data.attrs["order"] == i:
                    # Attach data to input name.
                    data[curr_data.attrs["name"]] = _h5_data_to_np_array(curr_data)  # type: ignore

                    # Break out of the inner loop.
                    found_index = True
                    break

            if not found_index:
                raise ValueError(
                    f"Failed to parse dataset h5 file: Unable to find input with order index {i}"
                )
    else:
        # Inputs do not have an order.
        data = {}  # type: ignore

        for _, curr_data in h5f_data.items():
            # Get the np array for each batch stored in the h5 file.
            data[curr_data.attrs["name"]] = _h5_data_to_np_array(curr_data)  # type: ignore

    return data
