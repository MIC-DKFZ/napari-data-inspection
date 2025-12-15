from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from napari.layers import Image, Labels
from napari_toolkit.utils import get_value

from napari_data_inspection.data_inspection._widget_io import DataInspectionWidget_IO

if TYPE_CHECKING:
    import napari


class DataInspectionWidget(DataInspectionWidget_IO):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

        self.cache_data = {}
        self.cache_meta = {}

    def load_data(self, layer_block, index):

        file = layer_block[index]

        file_name = layer_block.fm.name_from_path(file)
        layer_name = f"{layer_block.name} - {index} - {file_name}"

        if layer_block.name in self.cache_data and str(index) in self.cache_data[layer_block.name]:
            data = self.cache_data[layer_block.name].pop(str(index))
            meta = self.cache_meta[layer_block.name].pop(str(index))
        else:
            data, meta = layer_block.load_data(file)
        affine = meta.get(
            "affine"
        )  # if not get_value(self.ignore_affine) else np.eye(data.ndim + 1)
        affine_to_use = (
            affine
            if affine is not None and not get_value(self.ignore_affine)
            else np.eye(data.ndim + 1)
        )

        if layer_block.ltype == "Labels" and not np.issubdtype(data.dtype, np.integer):
            data = data.astype(int)

        target_layer = [
            layer for layer in self.viewer.layers if layer.name.startswith(f"{layer_block.name} - ")
        ]
        if len(target_layer) == 0:
            if layer_block.ltype == "Image":
                layer = Image(
                    data=data, affine=affine_to_use, name=layer_name, metadata={"affine": affine}
                )
            elif layer_block.ltype == "Labels":
                layer = Labels(
                    data=data, affine=affine_to_use, name=layer_name, metadata={"affine": affine}
                )
            else:
                return
            self.viewer.add_layer(layer)
        else:
            target_layer = target_layer[0]
            target_layer._keep_auto_contrast = get_value(self.auto_contrast)
            target_layer.name = layer_name
            target_layer.data = data
            target_layer.affine = affine_to_use
            target_layer.metadata = {"affine": affine}

        if not get_value(self.keep_camera):
            self.viewer.reset_view()
            if self.viewer.layers[layer_name].ndim == 3:
                slice_axis = self.viewer.dims.order[0]
                mid = self.viewer.layers[layer_name].data.shape[slice_axis] // 2
                current_step = list(self.viewer.dims.current_step)
                current_step[slice_axis] = mid
                self.viewer.dims.current_step = current_step
