from qtpy.QtWidgets import QVBoxLayout
from napari_data_inspection import DataInspectionWidget
from napari_toolkit.widgets import (
    setup_acknowledgements,
    setup_lineedit,
    setup_togglebutton,
    setup_pushbutton,
    setup_label,
)
from napari_toolkit.containers import setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import get_value
from pathlib import Path
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QShortcut
import numpy as np

from vidata.io import save_sitk


class DataInspectionWidgetBYU(DataInspectionWidget):

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

        def toggle_add():
            self.add_btn.setChecked(not self.add_btn.isChecked())
            self.on_add_instance(self.add_btn.isChecked())

        key_e = QShortcut(QKeySequence("e"), self)
        key_e.activated.connect(toggle_add)

        def toggle_rem():
            self.rem_btn.setChecked(not self.rem_btn.isChecked())
            self.on_remove_instance(self.rem_btn.isChecked())

        key_r = QShortcut(QKeySequence("r"), self)
        key_r.activated.connect(toggle_rem)

    def build_gui(self):
        main_layout = QVBoxLayout()

        self.build_gui_header(main_layout)
        self.build_gui_byu(main_layout)
        self.build_gui_navigation(main_layout)
        self.build_gui_prefetching(main_layout)
        self.build_gui_layers(main_layout)

        setup_acknowledgements(main_layout)

        self.setLayout(main_layout)

    def build_gui_byu(self, main_layout):
        # Project Kaggle2025_BYU
        _container, _layout = setup_vgroupbox(main_layout, "Kaggle2025_BYU")
        self.add_btn = setup_togglebutton(None, "Add Instance", function=self.on_add_instance)
        self.rem_btn = setup_togglebutton(None, "Remove Instance", function=self.on_remove_instance)
        hstack(_layout, [self.add_btn, self.rem_btn])
        btn3 = setup_pushbutton(None, "Save", function=self.on_save_correction, shortcut="S")
        self.output_dir = setup_lineedit(
            None,
            placeholder="Output Directory",
        )
        hstack(_layout, [self.output_dir, btn3])
        self.num_gt = setup_label(_layout, "Instances in GT:")
        self.num_pred = setup_label(_layout, "Instances in Prediction:")

    def load_data(self, layer_block, index):
        super().load_data(layer_block, index)

        if layer_block.name in ["GT", "Prediction"]:
            file = layer_block[index]
            file_name = str(Path(file).relative_to(layer_block.path)).replace(
                layer_block.file_type, ""
            )
            layer_name = f"{layer_block.name} - {index} - {file_name}"

            data = self.viewer.layers[layer_name].data
            max_i = np.max(data)
            if layer_block.name == "GT":
                self.num_gt.setText(f"Instances in GT: {max_i}")
            elif layer_block.name == "Prediction":
                self.num_pred.setText(f"Instances in Pred: {max_i}")

    def get_layerblock_by_name(self, blockname):
        layer_block = [block for block in self.layer_blocks if block.name == blockname]
        if layer_block == []:
            raise ValueError(f"You need a layer named {blockname}")
        else:
            return layer_block[0]

    def get_names(self, layer_block):
        index = get_value(self.progressbar)
        file = layer_block[index]
        file_name = str(Path(file).name).replace(layer_block.file_type, "")
        layer_name = f"{layer_block.name} - {index} - {file_name}"
        return file, file_name, layer_name

    def maybe_copy_layer(self, layer_name, layer_copy_name):
        if layer_copy_name not in self.viewer.layers:
            layer = self.viewer.layers[layer_name]
            layer_copy = layer.__class__(**layer._get_state().copy())
            layer_copy.name = layer_copy_name
            self.viewer.add_layer(layer_copy)
            layer_copy.brush_size = 10
            layer_copy.n_edit_dimensions = 3
        layer_copy = self.viewer.layers[layer_copy_name]
        return layer_copy

    def on_add_instance(self, activate):
        try:
            layer_block = self.get_layerblock_by_name("GT")
        except ValueError:
            self.add_btn.setChecked(False)
            self.add_btn.toggle_button()
            return

        file, file_name, layer_name = self.get_names(layer_block)
        layer_copy_name = layer_name.replace("GT", "GT_corrected")

        if activate:

            if layer_name not in self.viewer.layers:
                self.add_btn.setChecked(False)
                raise ValueError(f"no layer: {layer_name}")

            layer_copy = self.maybe_copy_layer(layer_name, layer_copy_name)
            layer_copy.selected_label = np.max(layer_copy.data) + 1
            layer_copy.mode = "paint"
            self.viewer.layers.selection.active = layer_copy
            layer_copy.mouse_drag_callbacks.append(self.mouse_add_callback)

        else:
            if layer_copy_name in self.viewer.layers:
                layer_copy = self.viewer.layers[layer_copy_name]
                layer_copy.mode = "pan_zoom"
                layer_copy.mouse_drag_callbacks.remove(self.mouse_add_callback)

    def mouse_add_callback(self, layer, event):
        if layer.mode == "paint" and event.type == "mouse_press":
            self.add_btn.setChecked(False)
            self.add_btn.toggle_button()
            layer.mode = "pan_zoom"
            layer.mouse_drag_callbacks.remove(self.mouse_add_callback)

    def on_remove_instance(self, activate):
        try:
            layer_block = self.get_layerblock_by_name("GT")
        except ValueError:
            self.rem_btn.setChecked(False)
            self.rem_btn.toggle_button()
            return

        file, file_name, layer_name = self.get_names(layer_block)
        layer_copy_name = layer_name.replace("GT", "GT_corrected")

        if activate:

            if layer_name not in self.viewer.layers:
                self.add_btn.setChecked(False)
                raise ValueError(f"no layer: {layer_name}")

            layer_copy = self.maybe_copy_layer(layer_name, layer_copy_name)
            layer_copy.selected_label = np.max(layer_copy.data) + 1
            layer_copy.mode = "pick"
            self.viewer.layers.selection.active = layer_copy
            layer_copy.mouse_drag_callbacks.append(self.mouse_rem_callback)

        else:
            if layer_copy_name in self.viewer.layers:
                layer_copy = self.viewer.layers[layer_copy_name]
                layer_copy.mode = "pan_zoom"
                layer_copy.mouse_drag_callbacks.remove(self.mouse_rem_callback)

    def mouse_rem_callback(self, layer, event):
        if layer.mode == "pick" and event.type == "mouse_press":
            self.rem_btn.setChecked(False)
            self.rem_btn.toggle_button()
            layer.mode = "pan_zoom"
            layer.mouse_drag_callbacks.remove(self.mouse_rem_callback)
            coords = tuple(int(round(c)) for c in event.position)
            arr = layer.data
            value = arr[coords]
            if value != 0:
                arr[arr == value] = 0
                arr[arr > value] -= 1
                layer.data = arr

    def refresh(self):
        super().refresh()
        for layer in list(self.viewer.layers):
            if layer.name.startswith("GT_corrected"):
                self.viewer.layers.remove(layer)

    def on_save_correction(self):
        layer_block = self.get_layerblock_by_name("GT")

        file, file_name, layer_name = self.get_names(layer_block)

        layer_copy_name = layer_name.replace("GT", "GT_corrected")
        if layer_copy_name not in self.viewer.layers:
            raise ValueError(f"no layer: {layer_copy_name}")

        output_dir = get_value(self.output_dir)
        if output_dir == "":
            raise ValueError("You need to define a Output directory")

        layer = self.viewer.layers[layer_copy_name]
        data = layer.data
        metadata = {
            "spacing": layer.affine.scale,
            "origin": layer.affine.translate,
            "direction": layer.affine.rotate,
        }

        output_file = Path(output_dir).joinpath(file.name)
        save_sitk(data, output_file, metadata)
