from pathlib import Path
from typing import TYPE_CHECKING

from napari.layers import Image, Labels
from napari_toolkit.utils import get_value

from napari_data_inspection._widget_io import DataInspectionWidget_IO
from napari_data_inspection.utils.data_loading import load_data

if TYPE_CHECKING:
    import napari

class DataInspectionWidget(DataInspectionWidget_IO):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

        self.cache_data = {}
        self.cache_meta = {}

    def get_layer_cmap(self, layer):
        return layer.colormap.copy()

    def set_layer_cmap(self, layer, cmap):
        if cmap is not None:
            layer.colormap = cmap

    def get_layer_properties(self, layer):
        if isinstance(layer, Image):
            props = {
                "opacity": layer.opacity,
                "blending": layer.blending,
                "contrast_limits": layer.contrast_limits,
                "gamma": layer.gamma,
                "colormap": layer.colormap,
                "interpolation2d": layer.interpolation2d,
                "interpolation3d": layer.interpolation3d,
                "depiction": layer.depiction,
                "rendering": layer.rendering,
            }

        elif isinstance(layer, Labels):
            props = {
                "opacity": layer.opacity,
                "blending": layer.blending,
                "selected_label": layer.selected_label,
                "brush_size": layer.brush_size,
                "rendering": layer.rendering,
                "_color_mode": layer._color_mode,
                "contour": layer.contour,
                "n_edit_dimensions": layer.n_edit_dimensions,
                "contiguous": layer.contiguous,
                "preserve_labels": layer.preserve_labels,
                "show_selected_label": layer.show_selected_label,
            }
        else:
            props = {}
        return props

    def set_layer_properties(self, layer, properties):
        for key, value in properties.items():
            setattr(layer, key, value)

    def get_camera(self, viewer):
        return {
            "camera_zoom": viewer.camera.zoom,
            "camera_center": viewer.camera.center,
            "camera_angle": viewer.camera.angles,
            "camera_perspective": viewer.camera.perspective,
        }

    def set_camera(self, viewer, camera):
        if camera is not None:
            self.viewer.camera.zoom = camera["camera_zoom"]
            self.viewer.camera.center = camera["camera_center"]
            self.viewer.camera.angles = camera["camera_angle"]
            self.viewer.camera.perspective = camera["camera_perspective"]

    def load_data(self, layer_block, index):
        cmap = None
        props = {}
        camera = None

        file = layer_block[index]
        file_name = str(Path(file).name).replace(layer_block.dtype, "")
        layer_name = f"{layer_block.name} - {index} - {file_name}"

        # Remove previous layer, skip if layer_name already exists
        for layer in self.viewer.layers:
            if layer.name == layer_name:
                return

            elif layer.name.startswith(f"{layer_block.name} - "):
                if get_value(self.keep_camera):
                    camera = self.get_camera(self.viewer)
                if get_value(self.keep_color):
                    cmap = self.get_layer_cmap(layer)
                if get_value(self.keep_properties):
                    props = self.get_layer_properties(layer)

                self.viewer.layers.remove(layer)

        if layer_block.name in self.cache_data and str(index) in self.cache_data[layer_block.name]:
            data = self.cache_data[layer_block.name].pop(str(index))
            affine = self.cache_meta[layer_block.name].pop(str(index))
        else:
            data, affine = load_data(file, layer_block.dtype)

        if layer_block.ltype == "Image":
            layer = Image(data=data, affine=affine, name=layer_name)
        elif layer_block.ltype == "Labels":
            layer = Labels(data=data, affine=affine, name=layer_name)
            if get_value(self.keep_color):
                self.set_layer_cmap(layer, cmap)
        else:
            return
        self.set_layer_properties(layer, props)
        self.viewer.add_layer(layer)

        if get_value(self.keep_camera):
            self.set_camera(self.viewer, camera)
        else:
            self.viewer.reset_view()

    def clear_cache(self):
        def filter_by_layer_and_index(cache, valid_keys, current_index):
            return {
                layer_name: {i: data for i, data in items.items() if i == current_index}
                for layer_name, items in cache.items()
                if layer_name in valid_keys
            }

        valid_keys = {block.name for block in self.layer_blocks}
        current_index = str(self.index)
        self.cache_data = filter_by_layer_and_index(self.cache_data, valid_keys, current_index)
        self.cache_meta = filter_by_layer_and_index(self.cache_meta, valid_keys, current_index)


# class DataInspectionWidget_(DataInspectionWidget_GUI):
#
#     def run(self):
#
#         self.index = get_value(self.progressbar)
#
#         if get_value(self.keep_camera):
#
#             camera_zoom = self.viewer.camera.zoom
#             camera_center = self.viewer.camera.center
#             camera_angle = self.viewer.camera.angles
#             camera_perspective = self.viewer.camera.perspective
#
#         for layer_block in self.layer_blocks:
#             if len(layer_block) != 0:
#                 self.maybe_load_data(layer_block)
#
#             else:
#                 print(f"Something went wrong with Layer {layer_block.name}")
#
#         if get_value(self.keep_camera):
#
#             self.viewer.camera.zoom = camera_zoom
#             self.viewer.camera.center = camera_center
#             self.viewer.camera.angles = camera_angle
#             self.viewer.camera.perspective = camera_perspective
#
#     def maybe_load_data(self, layer_block):
#         cmap = None
#         props = {}
#
#         file = layer_block[self.index]
#         file_name = str(Path(file).name).replace(layer_block.dtype, "")
#         layer_name = f"{layer_block.name} - {self.index} - {file_name}"
#
#         # Remove previous layer, skip if layer_name already exists
#         for layer in self.viewer.layers:
#             if layer.name == layer_name:
#                 return
#             elif layer.name.startswith(f"{layer_block.name} - "):
#                 if get_value(self.keep_color):
#                     cmap = layer.colormap.copy()
#                 if get_value(self.keep_properties) and isinstance(layer, Image):
#                     props = {
#                         "opacity": layer.opacity,
#                         "blending": layer.blending,
#                         "contrast_limits": layer.contrast_limits,
#                         "gamma": layer.gamma,
#                         "colormap": layer.colormap,
#                         "interpolation2d": layer.interpolation2d,
#                         "interpolation3d": layer.interpolation3d,
#                         "depiction":layer.depiction,
#                         "rendering": layer.rendering,
#                     }
#                 elif get_value(self.keep_color) and isinstance(layer, Labels):
#                     props = {
#                         "opacity": layer.opacity,
#                         "blending": layer.blending,
#                         "selected_label": layer.selected_label,
#                         "brush_size": layer.brush_size,
#                         "rendering": layer.rendering,
#                         "_color_mode": layer._color_mode,
#                         "contour": layer.contour,
#                         "n_edit_dimensions": layer.n_edit_dimensions,
#                         "contiguous": layer.contiguous,
#                         "preserve_labels": layer.preserve_labels,
#                         "show_selected_label": layer.show_selected_label,
#                     }
#                     # ,"contrast_limits": layer.contrast_limits
#                 self.viewer.layers.remove(layer)
#
#         data, affine = load_data(file, layer_block.dtype)
#
#         if layer_block.ltype == "Image":
#             layer = Image(data=data, affine=affine, name=layer_name)
#             for key, value in props.items():
#                 setattr(layer, key, value)
#
#             self.viewer.add_layer(layer)
#         elif layer_block.ltype == "Labels":
#             layer = Labels(data=data, affine=affine, name=layer_name)
#             for key, value in props.items():
#                 setattr(layer, key, value)
#             if get_value(self.keep_color) and cmap is not None:
#                 layer.colormap = cmap
#             self.viewer.add_layer(layer)
#
