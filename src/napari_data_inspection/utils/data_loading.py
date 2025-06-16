from collections.abc import Callable
from typing import Optional

import blosc2
import numpy as np
import SimpleITK as sitk
import tifffile as tiff
from napari.utils.transforms import Affine
from skimage import io

LoaderFunc = Callable[[str], tuple[np.ndarray, Optional[Affine]]]
LOADER_REGISTRY: dict[str, LoaderFunc] = {}


def register_loader(*dtypes: str) -> Callable[[LoaderFunc], LoaderFunc]:
    def decorator(func: LoaderFunc) -> LoaderFunc:
        for dtype in dtypes:
            LOADER_REGISTRY[dtype] = func
        return func

    return decorator


def load_data(file: str, dtype: str) -> tuple[np.ndarray, Optional[Affine]]:
    """
    Opens a file and returns the data along with an optional affine transformation matrix.

    Args:
        file (str): The path to the file.
        dtype (str): The file type of the image. Supported types are ".nii.gz", ".nrrd", ".mha", ".png",
                     ".jpg", ".tif", ".tiff", and ".b2nd".

    Returns:
        Tuple[np.ndarray, Optional[np.ndarray]]: A tuple containing:
            - np.ndarray: The image data as a NumPy array.
            - Optional[np.ndarray]: The affine transformation matrix (for medical image types) or None.
    """
    try:
        loader = LOADER_REGISTRY[dtype]
        return loader(file)
    except KeyError as err:
        raise ValueError(
            f"Unsupported dtype '{dtype}'. "
            f"Supported types are: {sorted(LOADER_REGISTRY.keys())}"
        ) from err


@register_loader(".nii.gz", ".nrrd", ".mha")
def open_sitk(file: str) -> tuple[np.ndarray, Affine]:
    """Opens a medical image file (e.g., .nii.gz, .nrrd, .mha) using SimpleITK and returns the data and affine transformation matrix."""
    image = sitk.ReadImage(file)
    array = sitk.GetArrayFromImage(image)
    ndims = len(array.shape)

    spacing = np.array(image.GetSpacing()[::-1])
    origin = np.array(image.GetOrigin()[::-1])
    direction = np.array(image.GetDirection()[::-1]).reshape(ndims, ndims)

    affine = Affine(
        scale=spacing,
        translate=origin,
        rotate=direction,
    )

    return array, affine


@register_loader(".png", ".jpg")
def open_skimage(file: str) -> tuple[np.ndarray, None]:
    """Opens a 2D image file (e.g., .png, .jpg) using scikit-image and returns the data."""
    return io.imread(file), None


@register_loader(".tif", ".tiff")
def open_tiff(file: str) -> tuple[np.ndarray, None]:
    """Opens a TIFF image file (e.g., .tif, .tiff) using tifffile and returns the data."""
    return tiff.imread(file), None


@register_loader(".b2nd")
def open_blosc2(file: str) -> tuple[np.ndarray, None]:
    """Opens a Blosc2 compressed image file (.b2nd) and returns the data."""
    data = blosc2.open(urlpath=file, mode="r", dparams={"nthreads": 1}, mmap_mode="r")

    # metadata = dict(data.schunk.meta)
    # args={}
    # if "spacing" in metadata:
    #     args["scale"] = metadata["spacing"]
    # if "direction" in metadata:
    #     args["rotate"] = metadata["direction"]
    # if "origin" in metadata:
    #     args["translate"] = metadata["origin"]

    return data[...], None  # Affine(**args)


# Template
# @register_loader(".myfiletyp")
# def open_myfiletype(file: str) -> tuple[np.ndarray, Optional[Affine]]:
#     ...
#     return data, affine
