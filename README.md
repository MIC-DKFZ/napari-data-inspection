# napari-data-inspection

A data inspection plugin for loading image tiles from multiple folders.
With data loading and prefetching handled automatically, file navigation is streamlined to enable fast and efficient data inspection.
Any number of folders for images and labels can be specified, and files are automatically paired based on their order — manual file selection is eliminated.
Perfect for high-throughput inspection workflows and rapid dataset review, especially in semantic segmentation tasks.

## Installation

```bash
# 1. Install napari if necessary
pip install napari[all]
# 2. Install the plugin
pip install napari-data-inspection
```

## Prerequisites

### Supported File Types
The following file types are supported: `.nii.gz`, `.png`, `.b2nd`, `.nrrd`, `.mha`, `.tif`, `.tiff`.
If you want to add custom ones add a loader to `src/napari_data_inspection/utils/data_loading.py`.

### Data Organization Requirements
Your data should be organized so that different images and different labels can be clearly distinguished—either by placing them in separate folders or by using consistent filename patterns (e.g., *_img for images and *_seg for labels).
**The number of files must match across all folders, as they are paired by order.**

## How to

```
napari -w napari-data-inspection
```

<img src="https://github.com/MIC-DKFZ/napari-data-inspection/raw/main/imgs/GUI.png">

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
