import threading
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from napari_toolkit.utils import get_value, set_value
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QShortcut

from napari_data_inspection._widget_gui import DataInspectionWidget_GUI
from napari_data_inspection.utils.data_loading import load_data

if TYPE_CHECKING:
    import napari


class DataInspectionWidget_LC(DataInspectionWidget_GUI):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)
        # Cache
        self.cache_data = {}
        self.cache_meta = {}

        self.running_threads = []

        # Key Bindings
        key_d = QShortcut(QKeySequence("d"), self)
        key_d.activated.connect(self.progressbar.increment_value)
        self.progressbar.next_button.setToolTip("Press [d] for next")

        key_a = QShortcut(QKeySequence("a"), self)
        key_a.activated.connect(self.progressbar.decrement_value)
        self.progressbar.prev_button.setToolTip("Press [a] for previous")

    # GUI Events

    def on_index_changed(self):
        self.refresh()

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

    ###########################################################################################

    def on_load_all(self):

        for layer_block in self.layer_blocks:
            layer_block.refresh()

        # self.update_max_len()
        # self.refresh()

    # Layer Events
    def on_layer_loaded(self, layer_block):

        if self.index < len(layer_block) and len(layer_block) != 0:
            self.update_max_len()
            self.refresh_layer(layer_block, self.index)

            if get_value(self.prefetch_next):
                threading.Thread(
                    target=self.fill_cache,
                    args=(
                        layer_block,
                        self.index + 1,
                    ),
                    daemon=True,
                ).start()
            if get_value(self.prefetch_prev):
                threading.Thread(
                    target=self.fill_cache,
                    args=(
                        layer_block,
                        self.index - 1,
                    ),
                    daemon=True,
                ).start()

            # self.fill_cache(layer_block, self.index + 1)
            # self.fill_cache(layer_block, self.index - 1)

    def on_layer_removed(self, block):
        super().on_layer_removed(block)

        self.update_max_len()

    def on_layer_updated(self, layer_block):
        self.update_max_len()

    # Functions
    def update_max_len(self):
        layer_legths = [len(block) for block in self.layer_blocks]

        if any(x != layer_legths[0] and x != 0 for x in layer_legths):
            print("Layer lengths do not match")

        if len(layer_legths) == 0 or np.max(layer_legths) < 1:
            self.progressbar.index_changed.disconnect(self.on_index_changed)
            self.progressbar.setMaximum(1)
            self.index = get_value(self.progressbar)
            self.progressbar.index_changed.connect(self.on_index_changed)
            return

        min_length = np.min([_len for _len in layer_legths if _len > 0])
        if min_length != self.progressbar.max_value:
            self.progressbar.index_changed.disconnect(self.on_index_changed)
            self.progressbar.setMaximum(min_length)
            self.index = get_value(self.progressbar)
            self.progressbar.index_changed.connect(self.on_index_changed)

    # Data Loading
    def refresh(self):

        if self.running_threads != []:
            print("Caching is running for file and index:", self.running_threads)
            print("Retry when finished...")
            self.progressbar.index_changed.disconnect(self.on_index_changed)
            set_value(self.progressbar, self.index)
            self.progressbar.index_changed.connect(self.on_index_changed)
            return

        index_new = get_value(self.progressbar)
        self.empty_cache(index_new)

        for layer_block in self.layer_blocks:
            if len(layer_block) != 0:
                self.refresh_layer(layer_block, index_new)

        for layer_block in self.layer_blocks:
            if len(layer_block) != 0:

                if get_value(self.prefetch_next):
                    threading.Thread(
                        target=self.fill_cache,
                        args=(
                            layer_block,
                            index_new + 1,
                        ),
                        daemon=True,
                    ).start()
                if get_value(self.prefetch_prev):
                    threading.Thread(
                        target=self.fill_cache,
                        args=(
                            layer_block,
                            index_new - 1,
                        ),
                        daemon=True,
                    ).start()

        self.index = index_new

    def refresh_layer(self, layer_block, index):
        if index + 1 == self.index or index - 1 == self.index:
            self.push_data_to_cache(layer_block, self.index)

        if len(layer_block) != 0:
            self.load_data(layer_block, index)

    def load_data(self, layer_block, index):
        print(f"Refresh Layer {layer_block.name} at Index {index}")

    # Cache
    def empty_cache(self, index):
        # print("Empty cache")

        def filter_by_layer_and_index(cache, valid_keys, current_index):
            return {
                layer_name: {i: data for i, data in items.items() if i == current_index}
                for layer_name, items in cache.items()
                if layer_name in valid_keys
            }

        valid_keys = {block.name for block in self.layer_blocks}

        self.cache_data = filter_by_layer_and_index(self.cache_data, valid_keys, str(index))
        self.cache_meta = filter_by_layer_and_index(self.cache_meta, valid_keys, str(index))

        # for k, v in self.cache_data.items():
        #     print(k, list(v.keys()))

    def push_data_to_cache(self, layer_block, index):
        if layer_block.name not in self.cache_data:
            self.cache_data[layer_block.name] = {}
            self.cache_meta[layer_block.name] = {}

        if str(index) not in self.cache_data[layer_block.name]:
            file = layer_block[index]
            file_name = str(Path(file).name).replace(layer_block.dtype, "")
            layer_name = f"{layer_block.name} - {index} - {file_name}"

            self.cache_data[layer_block.name][str(index)] = self.viewer.layers[layer_name].data
            self.cache_meta[layer_block.name][str(index)] = self.viewer.layers[layer_name].affine

        # print(f"Push Data {layer_block.name} at Index {index}")
        # for k,v in self.cache_data.items():
        #     print(k, list(v.keys()))

    def fill_cache(self, layer_block, index):

        if index < 0 or index >= len(layer_block):
            return

        t_name = f"{layer_block.name} - {index}"
        self.running_threads.append(t_name)

        if layer_block.name not in self.cache_data:
            self.cache_data[layer_block.name] = {}
            self.cache_meta[layer_block.name] = {}

        if str(index) not in self.cache_data[layer_block.name]:
            file = layer_block[index]
            data, affine = load_data(file, layer_block.dtype)
            self.cache_data[layer_block.name][str(index)] = data
            self.cache_meta[layer_block.name][str(index)] = affine

        # print(f"Fill Cache {layer_block.name} at Index {index}")
        # for k, v in self.cache_data.items():
        #     print(k, list(v.keys()))

        self.running_threads.remove(t_name)
