from pathlib import Path

from napari_toolkit.utils import get_value, set_value
from omegaconf import OmegaConf
from qtpy.QtWidgets import QFileDialog
from vidata.config_manager import ConfigManager

from napari_data_inspection.data_inspection._widget_navigation import DataInspectionWidget_LC


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
                "name": get_value(self.project_name),
                "layers": layer_configs,
                "data_inspection": {
                    "keep_camera": get_value(self.keep_camera),
                    "prefetch_prev": get_value(self.prefetch_prev),
                    "prefetch_next": get_value(self.prefetch_next),
                    "prefetch_radius": get_value(self.radius),
                },
            }

            config.update(self.meta_config)

            OmegaConf.save(config, config_path)
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
            self._load_yaml_cfg(config_path)
        else:
            print("No Valid File Selected")

    def _load_yaml_cfg(self, config_path, split=None, fold=None):
        self.clear_project()

        global_config = OmegaConf.load(config_path)

        set_value(self.project_name, global_config["name"])

        data_inspection_config = global_config.get("data_inspection", None)
        data_inspection_config = data_inspection_config or {}

        set_value(self.keep_camera, data_inspection_config.get("keep_camera", False))
        set_value(self.prefetch_prev, data_inspection_config.get("prefetch_prev", True))
        set_value(self.prefetch_next, data_inspection_config.get("prefetch_next", True))
        set_value(self.radius, data_inspection_config.get("prefetch_radius", 1))

        exclude_layers = data_inspection_config.get("exclude_layers", [])
        exclude_layers = exclude_layers if isinstance(exclude_layers, list) else [exclude_layers]
        config_manager = ConfigManager(global_config, strict=False)
        for layer in config_manager.layers:
            if layer.name not in exclude_layers:
                self.add_layer(layer.config(split=split, fold=fold))

        self.update_max_len()

        self.meta_config = {
            k: v for k, v in global_config.items() if k not in ["name", "layers", "data_inspection"]
        }
