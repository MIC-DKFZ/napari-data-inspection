import json
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from napari.layers import Image, Labels
from napari_toolkit.containers import setup_scrollarea, setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import get_value, set_value
from napari_toolkit.widgets import (
    setup_checkbox,
    setup_iconbutton,
    setup_lineedit,
    setup_progressbaredit,
    setup_pushbutton,
)
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QFileDialog, QShortcut, QSizePolicy, QVBoxLayout, QWidget

from napari_data_inspection.utils.data_loading import load_data
from napari_data_inspection.widgets.layers_block_widget import setup_layerblock

if TYPE_CHECKING:
    import napari


def collect_files(config):
    folder_path = Path(config["path"])
    file_type = config["dtype"]
    if file_type == "" or folder_path == "":
        return []

    if "*" not in file_type:
        file_type = "*" + file_type
    files = sorted(folder_path.glob(file_type))
    return files


class DataInspectionWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.file_ending = ".nproj"
        self.index = 0
        self.layer_blocks = []

        # Build Gui
        self.build_gui()

        # Key Bindings
        key_d = QShortcut(QKeySequence("d"), self)
        key_d.activated.connect(self.progressbar.increment_value)
        self.progressbar.next_button.setToolTip("Press [d] for next")

        key_a = QShortcut(QKeySequence("a"), self)
        key_a.activated.connect(self.progressbar.decrement_value)
        self.progressbar.prev_button.setToolTip("Press [a] for previous")

    def build_gui(self):
        main_layout = QVBoxLayout()

        # Header
        _container, _layout = setup_vgroupbox(main_layout, "Project")
        self.project_name = setup_lineedit(_layout, placeholder="Project Name")

        # IO
        lbtn = setup_pushbutton(None, "Load", function=self.load)
        sbtn = setup_pushbutton(None, "Save", function=self.save)
        hstack(_layout, [lbtn, sbtn])

        # Progressbar
        _container, _layout = setup_vgroupbox(main_layout, "Navigation")
        self.progressbar = setup_progressbaredit(_layout, 0, 1, self.index, function=self.run)
        self.progressbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.search_name = setup_lineedit(
            _layout, placeholder="Enter Filename ...", function=self.on_name_entered
        )

        self.keep_camera = setup_checkbox(None, "Keep Camera", False)
        self.keep_color = setup_checkbox(None, "Keep ColorMap", True)
        _ = hstack(_layout, [self.keep_camera, self.keep_color])
        # _ = setup_iconbutton(_layout, "Load", "right_arrow", function=self.run)

        # Add Layer
        new_btn = setup_iconbutton(None, "New Layer", "add", function=self.on_layer_added)
        add_btn = setup_iconbutton(None, "Load All", "right_arrow", function=self.load_all)
        _ = hstack(main_layout, [new_btn, add_btn])

        # Scroll Area
        self.scroll_area = setup_scrollarea(main_layout)
        self.scroll_area.setWidgetResizable(True)

        # Layers
        self.layer_container, self.layer_layout = setup_vgroupbox(None, "Layers")
        self.layer_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layer_container.setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.layer_container)

        self.setLayout(main_layout)

    def add_layer(self, config):

        layer_block = setup_layerblock(self.layer_layout)
        layer_block.set_config(config)

        layer_block.deleted.connect(self.on_layer_removed)
        layer_block.updated.connect(self.on_layer_updated)

        self.layer_blocks.append(layer_block)

        self.scroll_area.setWidget(self.layer_container)

        vertical_scrollbar = self.scroll_area.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

    def on_add_all(self):
        for layer_block in self.layer_blocks:
            layer_block.refresh()

    def on_name_entered(self):
        _name = get_value(self.search_name)

        for layer_block in self.layer_blocks:
            files = layer_block.files
            path = layer_block.path

            files = [str(_file).replace(path, "") for _file in files]
            index = next((i for i, _file in enumerate(files) if _name in _file), None)

            if index is not None:
                set_value(self.progressbar, index)
                set_value(self.search_name, "")
                break

    def on_layer_added(self):
        config = {"name": "", "path": "", "dtype": "", "ltype": "Image"}
        self.add_layer(config)

    def on_layer_removed(self, block):

        index = self.layer_blocks.index(block)
        if 0 <= index < len(self.layer_blocks):
            del self.layer_blocks[index]

        self.update_max_len()

    def on_layer_updated(self, layer_block):
        self.update_max_len()
        self.maybe_load_data(layer_block)

    def update_max_len(self):
        layer_legths = [len(block) for block in self.layer_blocks]

        if any(x != layer_legths[0] for x in layer_legths):
            print("Layer lengths do not match")

        if len(layer_legths) == 0 or np.max(layer_legths) < 1:
            self.progressbar.index_changed.disconnect(self.run)
            self.progressbar.setMaximum(1)
            self.index = get_value(self.progressbar)
            self.progressbar.index_changed.connect(self.run)
            return

        min_length = np.min([_len for _len in layer_legths if _len > 0])
        if min_length != self.progressbar.max_value:
            self.progressbar.index_changed.disconnect(self.run)
            self.progressbar.setMaximum(min_length)
            self.index = get_value(self.progressbar)
            self.progressbar.index_changed.connect(self.run)

    def clear(self):

        for layer_block in self.layer_blocks:
            self.layer_layout.removeWidget(layer_block)
            del layer_block
        self.layer_blocks = []

        self.scroll_area.setWidget(self.layer_container)

    def load_all(self):
        for layer_block in self.layer_blocks:
            layer_block.refresh()
        self.run()

    def run(self):

        self.index = get_value(self.progressbar)

        if get_value(self.keep_camera):

            camera_zoom = self.viewer.camera.zoom
            camera_center = self.viewer.camera.center
            camera_angle = self.viewer.camera.angles
            camera_perspective = self.viewer.camera.perspective

        for layer_block in self.layer_blocks:
            if len(layer_block) != 0:
                self.maybe_load_data(layer_block)

            else:
                print(f"Something went wrong with Layer {layer_block.name}")

        if get_value(self.keep_camera):

            self.viewer.camera.zoom = camera_zoom
            self.viewer.camera.center = camera_center
            self.viewer.camera.angles = camera_angle
            self.viewer.camera.perspective = camera_perspective

    def maybe_load_data(self, layer_block):
        cmap = None

        file = layer_block[self.index]
        file_name = str(Path(file).name).replace(layer_block.dtype, "")
        layer_name = f"{layer_block.name} - {self.index} - {file_name}"

        # Remove previous layer, skip if layer_name already exists
        for layer in self.viewer.layers:
            if layer.name == layer_name:
                return
            elif layer.name.startswith(f"{layer_block.name} - "):
                if get_value(self.keep_color):
                    cmap = layer.colormap.copy()
                self.viewer.layers.remove(layer)

        data, affine = load_data(file, layer_block.dtype)

        if layer_block.ltype == "Image":
            layer = Image(data=data, affine=affine, name=layer_name)
            self.viewer.add_layer(layer)
        elif layer_block.ltype == "Labels":
            layer = Labels(data=data, affine=affine, name=layer_name)
            if get_value(self.keep_color) and cmap is not None:
                layer.colormap = cmap
            self.viewer.add_layer(layer)

    def save(self):
        if get_value(self.project_name) == "":
            print("Project name not set")
            return
        _dialog = QFileDialog(self)
        _dialog.setDirectory(str(Path.cwd()))
        config_path, _ = _dialog.getSaveFileName(
            self,
            "Select File",
            f"{get_value(self.project_name)}{self.file_ending}",
            filter=f"*{self.file_ending}",
            options=QFileDialog.DontUseNativeDialog,
        )
        if config_path is not None and config_path.endswith(self.file_ending):
            config_path = Path(config_path)

            layer_configs = [layer_block.get_config() for layer_block in self.layer_blocks]

            config = {
                "project_name": get_value(self.project_name),
                "keep_camera": get_value(self.keep_camera),
                "keep_color": get_value(self.keep_color),
                "layers": layer_configs,
            }

            with Path(config_path).open("w") as f:
                json.dump(config, f, indent=4)
        else:
            print("No Valid File Selected")

    def load(self):
        _dialog = QFileDialog(self)
        _dialog.setDirectory(str(Path.cwd()))
        config_path, _ = _dialog.getOpenFileName(
            self,
            "Select File",
            filter=f"*{self.file_ending}",
            options=QFileDialog.DontUseNativeDialog,
        )
        if config_path is not None and config_path.endswith(self.file_ending):
            self.clear()

            with Path(config_path).open("r") as f:
                global_config = json.load(f)

            set_value(self.project_name, global_config["project_name"])
            set_value(self.keep_camera, global_config["keep_camera"])
            set_value(self.keep_color, global_config["keep_color"])

            for config in global_config["layers"]:
                self.add_layer(config)
            self.update_max_len()
        else:
            print("No Valid File Selected")
