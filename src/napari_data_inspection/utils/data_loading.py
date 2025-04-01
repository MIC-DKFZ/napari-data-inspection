from typing import Optional, Tuple

import blosc2
import numpy as np
import SimpleITK as sitk
import tifffile as tiff
from napari.utils.transforms import Affine
from skimage import io


def load_data(file: str, dtype: str) -> Tuple[np.ndarray, Optional[np.ndarray]]:
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
    if dtype == ".nii.gz" or dtype == ".nrrd" or dtype == ".mha":
        return open_sitk(file)
    elif dtype == ".png" or dtype == ".jpg":
        return open_skimage(file)
    elif dtype == ".tif" or dtype == ".tiff":
        return open_tiff(file)
    elif dtype == ".b2nd":
        return open_blosc2(file)
    else:
        raise ValueError(f"Unsupported dtype '{dtype}'. Your may need to implement a loader by yourself")


def open_sitk(file: str) -> Tuple[np.ndarray, np.ndarray]:
    """Opens a medical image file (e.g., .nii.gz, .nrrd, .mha) using SimpleITK and returns the data and affine transformation matrix."""
    image = sitk.ReadImage(file)
    array = sitk.GetArrayFromImage(image)
    ndims = len(array.shape)

    spacing = np.array(image.GetSpacing()[::-1])
    origin = np.array(image.GetOrigin()[::-1])
    direction = np.array(image.GetDirection()[::-1]).reshape(ndims, ndims)

    affine=Affine(
        scale=spacing,
        translate=origin,
        rotate=direction,
    )


    return array, affine


def open_skimage(file: str) -> Tuple[np.ndarray, None]:
    """Opens a 2D image file (e.g., .png, .jpg) using scikit-image and returns the data."""
    return io.imread(file), Affine()


def open_tiff(file: str) -> Tuple[np.ndarray, None]:
    """Opens a TIFF image file (e.g., .tif, .tiff) using tifffile and returns the data."""
    return tiff.imread(file), None


def open_blosc2(file: str) -> Tuple[np.ndarray, None]:
    """Opens a Blosc2 compressed image file (.b2nd) and returns the data."""
    image = blosc2.open(urlpath=file, mode="r", dparams={"nthreads": 1}, mmap_mode="r")
    return image[...], None
