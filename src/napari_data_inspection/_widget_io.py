import json
from pathlib import Path

from napari_toolkit.utils import get_value, set_value
from qtpy.QtWidgets import QFileDialog

from napari_data_inspection._widget_navigation import DataInspectionWidget_LC


class DataInspectionWidget_IO(DataInspectionWidget_LC):
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
                "keep_properties": get_value(self.keep_properties),
                "prefetch_prev": get_value(self.prefetch_prev),
                "prefetch_next": get_value(self.prefetch_next),
                "prefetch_radius": get_value(self.radius),
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
            self.clear_project()

            with Path(config_path).open("r") as f:
                global_config = json.load(f)

            set_value(self.project_name, global_config["project_name"])
            set_value(self.keep_camera, global_config.get("keep_camera", False))
            set_value(self.keep_properties, global_config.get("keep_properties", True))
            set_value(self.prefetch_prev, global_config.get("prefetch_prev", True))
            set_value(self.prefetch_next, global_config.get("prefetch_next", True))
            set_value(self.radius, global_config.get("prefetch_radius", 1))

            for config in global_config["layers"]:
                self.add_layer(config)
            self.update_max_len()
        else:
            print("No Valid File Selected")
