from copy import copy

from kedro.io import DataCatalog


def add_dataset_copy_with_suffix_filepath(
    catalog,
    dataset_name,
    suffix,
    dataset_suffix_sep: str = "__",
    filepath_suffix_sep: str = "__",
) -> DataCatalog:
    dataset = copy(catalog._data_sets[dataset_name])
    filepath = dataset._filepath.as_posix()
    filepath_type = type(dataset._filepath)
    filename = dataset._filepath.name
    file_basename, file_extension = filename.split(".")
    new_filename = f"{file_basename}{filepath_suffix_sep}{suffix}.{file_extension}"
    new_filepath = filepath.replace(filename, new_filename)

    dataset._filepath = filepath_type(new_filepath)
    catalog.add(data_set_name=f"{dataset_name}{dataset_suffix_sep}{suffix}", data_set=dataset)
    return catalog
