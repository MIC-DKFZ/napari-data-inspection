# Napari Data Inspection

A napari plugin for fast, high-throughput inspection of 2D/3D segmentation datasets.
Select one or more images and/or labels layers; files are paired and loaded automatically so you can browse entire datasets without manual effort.

## Features

- Multi-folder pairing: any number of image/label folders
- Prefetching & caching for steamless navigation
- Supports common formats (e.g., NIfTI, TIFF, PNG, NRRD, MHA, B2ND) out of the box.
- Extensible loaders (add your own formats if needed).

## Installation

```bash
# a) Install the plugin
pip install napari-data-inspection
# b) Install the plugin and napari if necessary
pip install napari-data-inspection[all]
```

## Quickstart

```
napari -w napari-data-inspection
```

<img src="https://github.com/MIC-DKFZ/napari-data-inspection/raw/main/imgs/GUI.png">

# Data organization

- Filter files by patterns (e.g., \*\_img.nii.gz, \*\_seg.nii.gz) and/or separate folders per layer.
- Number of files must match across layers; pairs are made by sorted order.

### 1. Separate folders per layer

Put each layer’s files in its own directory.

```
/data/images/
  case001.nii.gz
  case002.nii.gz
/data/labels/
  case001.nii.gz
  case002.nii.gz
```

### 2. By Patterns

Use patterns (globs) per layer.

```
/data/
  case001_img.nii.gz
  case001_seg.nii.gz
  case002_img.nii.gz
  case002_seg.nii.gz
```

Patterns

```
Images: *_img.nii.gz
Labels: *_seg.nii.gz
```

## Supported file types

The data loading is based on the [ViData](%22https://github.com/MIC-DKFZ/ViData?tab=readme-ov-file#imaging-and-array-data%22) package.
The following Extensions and Backends are available.

| Extension(s)                       | Backend(s)  | Notes                                                              |
| ---------------------------------- | ----------- | ------------------------------------------------------------------ |
| `.png`, `.jpg`, `.jpeg`, `.bmp`    | `imageio`   | Standard 2D image formats                                          |
| `.tif`, `.tiff`                    | `tifffile`  | Multipage TIFF; high bit-depths supported                          |
| `.nii.gz`, `.nii`, `.mha`, `.nrrd` | `sitk`      | Medical image formats (3D volumes)                                 |
| `.nii.gz`, `.nii`                  | `nibabel`   | Alternative medical imaging backend                                |
| `.b2nd`                            | `blosc2`    | Compressed N-dimensional arrays                                    |
| `.b2nd`                            | `blosc2pkl` | Compressed N-dimensional arrays with metadata in a separate `.pkl` |
| `.npy`                             | `numpy`     | Single NumPy array                                                 |

### Custom Load Functions

- Register a reader with a decorator.
- Reader must return (numpy_array, metadata_dict).
- Registration happens at import time—make sure this module is imported (e.g., from your package’s __init__.py).
- See [here](https://github.com/MIC-DKFZ/ViData/blob/main/src/vidata/io/image_io.py) for an example.
- metadata should contain an "affine" if entry, if any spatial transformation should be applied

```py
# custom_io_template.py  — fill in the TODOs and import this module somewhere at startup.
import numpy as np
from typing import Tuple, Dict, List

# TODO: import your backend library (e.g., imageio, tifffile, nibabel, SimpleITK, ...)
# import imageio.v3 as iio

from vidata.registry import register_loader, register_writer

# --------------------------- READER ------------------------------------------
# Replace file extension and backend name to your custom function
@register_loader("image", ".png", ".jpg", ".jpeg", ".bmp", backend="imageio")  # To Register Image Loading
@register_loader("mask", ".png", ".bmp", backend="imageio") # To Register Label Loading
def load_custom(file: str) -> tuple[np.ndarray, dict]:
    """
    Load a file and return (data, metadata).
    metadata can be empty or include keys like: spacing, origin, direction, shear, dtype, etc.
    """
    # data = iio.imread(file)  # example for imageio
    data = ...  # TODO: replace
    meta = {}   # TODO: replace
    return data, meta
```

### Torch Dataset Inspection

- Rapid inspection of PyTorch datasets in Napari by browsing images and corresponding labels directly from any torch.utils.data.Dataset

```py
from napari_data_inspection.dataset_inspection import DatasetInspectionWidget, run_dataset_inspection
from torch.utils.data import Dataset

# Example: inspect a PyTorch dataset
dataset = MyCustomDataset(...)  # any torch Dataset
run_dataset_inspection(dataset, channel_first=True, rescale=True, no_label=False, bg_class=0)
```

# Acknowledgments

<p align="left">
  <img src="https://github.com/MIC-DKFZ/napari-data-inspection/raw/main/imgs/Logos/HI_Logo.png" width="150"> &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="https://github.com/MIC-DKFZ/napari-data-inspection/raw/main/imgs/Logos/DKFZ_Logo.png" width="500">
</p>

This repository is developed and maintained by the Applied Computer Vision Lab (ACVL)
of [Helmholtz Imaging](https://www.helmholtz-imaging.de/) and the
[Division of Medical Image Computing](https://www.dkfz.de/en/medical-image-computing) at DKFZ.

This [napari] plugin was generated with [copier] using the [napari-plugin-template].

[copier]: https://copier.readthedocs.io/en/stable/
[napari]: https://github.com/napari/napari
[napari-plugin-template]: https://github.com/napari/napari-plugin-template
