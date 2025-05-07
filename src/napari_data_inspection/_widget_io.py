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

from napari_data_inspection._widget_gui import DataInspectionWidget_GUI
from napari_data_inspection.utils.data_loading import load_data
from napari_data_inspection.widgets.layers_block_widget import setup_layerblock

if TYPE_CHECKING:
    import napari

from napari_data_inspection._widget_navigation import DataInspectionWidget_LC


class DataInspectionWidget_IO(DataInspectionWidget_LC):
    def clear(self):

        for layer_block in self.layer_blocks:
            self.layer_layout.removeWidget(layer_block)
            del layer_block
        self.layer_blocks = []

        self.scroll_area.setWidget(self.layer_container)

    def save_project(self):
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
                "keep_properties": get_value(self.keep_properties),
                "prefetch_prev": get_value(self.prefetch_prev),
                "prefetch_next": get_value(self.prefetch_next),
                "layers": layer_configs,
            }

            with Path(config_path).open("w") as f:
                json.dump(config, f, indent=4)
        else:
            print("No Valid File Selected")

    def load_project(self):
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
            set_value(self.keep_camera, global_config.get("keep_camera", False))
            set_value(self.keep_color, global_config.get("keep_color", True))
            set_value(self.keep_properties, global_config.get("keep_properties", True))
            set_value(self.prefetch_prev, global_config.get("prefetch_prev", True))
            set_value(self.prefetch_next, global_config.get("prefetch_next", True))

            for config in global_config["layers"]:
                self.add_layer(config)
            self.update_max_len()
        else:
            print("No Valid File Selected")
