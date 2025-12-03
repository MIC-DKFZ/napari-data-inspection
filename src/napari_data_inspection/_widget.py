from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from napari.layers import Image, Labels
from napari_toolkit.utils import get_value

from napari_data_inspection._widget_io import DataInspectionWidget_IO

if TYPE_CHECKING:
    import napari


class DataInspectionWidget(DataInspectionWidget_IO):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

        self.cache_data = {}
        self.cache_meta = {}

    def load_data(self, layer_block, index):
        file = layer_block[index]
        file_name = str(Path(file).relative_to(layer_block.path)).replace(layer_block.file_type, "")
        layer_name = f"{layer_block.name} - {index} - {file_name}"

        if layer_block.name in self.cache_data and str(index) in self.cache_data[layer_block.name]:
            data = self.cache_data[layer_block.name].pop(str(index))
            meta = self.cache_meta[layer_block.name].pop(str(index))
        else:
            data, meta = layer_block.load_data(file)
        affine = meta.get("affine")

        target_layer = [
            layer for layer in self.viewer.layers if layer.name.startswith(f"{layer_block.name} - ")
        ]
        if len(target_layer) == 0:
            if layer_block.ltype == "Image":
                layer = Image(data=data, affine=affine, name=layer_name)
            elif layer_block.ltype == "Labels":
                if not np.issubdtype(data.dtype, np.integer):
                    data = data.astype(int)
                layer = Labels(data=data, affine=affine, name=layer_name)
            else:
                return
            self.viewer.add_layer(layer)
        else:
            target_layer = target_layer[0]
            target_layer.name = layer_name
            target_layer.data = data
            target_layer.affine = affine

        if not get_value(self.keep_camera):
            self.viewer.reset_view()
            if self.viewer.layers[layer_name].ndim == 3:  # and viewer.dims.ndisplay == 2:
                mid = self.viewer.layers[layer_name].data.shape[0] // 2
                self.viewer.dims.set_point(0, mid)
