import concurrent.futures
from concurrent.futures import CancelledError
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
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

        # how many items on each side to cache
        self.cache_radius = 1

        self.cache_data = {}
        self.cache_meta = {}

        self._cache_futures = {}
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

        # Key bindings …
        key_d = QShortcut(QKeySequence("d"), self)
        key_d.activated.connect(self.progressbar.increment_value)
        self.progressbar.next_button.setToolTip("Press [d] for next")
        key_a = QShortcut(QKeySequence("a"), self)
        key_a.activated.connect(self.progressbar.decrement_value)
        self.progressbar.prev_button.setToolTip("Press [a] for previous")

    def on_index_changed(self):
        self.refresh()

    def on_name_entered(self):
        _name = get_value(self.search_name)
        for layer_block in self.layer_blocks:
            files = [str(_file).replace(layer_block.path, "") for _file in layer_block.files]
            idx = next((i for i, f in enumerate(files) if _name in f), None)
            if idx is not None:
                set_value(self.progressbar, idx)
                set_value(self.search_name, "")
                break

    ###########################################################################################

    def on_load_all(self):
        for layer_block in self.layer_blocks:
            layer_block.refresh()

    # Layer Events
    def on_layer_loaded(self, layer_block):
        if self.index < len(layer_block) and len(layer_block) != 0:
            self.update_max_len()
            self.refresh_layer(layer_block, self.index)

            if get_value(self.prefetch_next):
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(layer_block, self.index + offset)
            if get_value(self.prefetch_prev):
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(layer_block, self.index - offset)

    def on_layer_removed(self, block):
        super().on_layer_removed(block)
        self.update_max_len()

    def on_layer_updated(self, layer_block):
        self.update_max_len()

    # Functions
    def update_max_len(self):
        layer_lengths = [len(b) for b in self.layer_blocks]
        if any(x != layer_lengths[0] and x != 0 for x in layer_lengths):
            print("Layer lengths do not match")

        if not layer_lengths or np.max(layer_lengths) < 1:
            self.progressbar.index_changed.disconnect(self.on_index_changed)
            self.progressbar.setMaximum(1)
            self.index = get_value(self.progressbar)
            self.progressbar.index_changed.connect(self.on_index_changed)
            return

        min_len = np.min([_l for _l in layer_lengths if _l > 0])
        if min_len != self.progressbar.max_value:
            self.progressbar.index_changed.disconnect(self.on_index_changed)
            self.progressbar.setMaximum(min_len - 1)
            self.index = get_value(self.progressbar)
            self.progressbar.index_changed.connect(self.on_index_changed)

    # Data Loading
    def refresh(self):
        idx = get_value(self.progressbar)
        self._prune_caches_and_futures(idx)

        for lb in self.layer_blocks:
            if len(lb):
                self.refresh_layer(lb, idx)

        if get_value(self.prefetch_next):
            for lb in self.layer_blocks:
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(lb, idx + offset)
        if get_value(self.prefetch_prev):
            for lb in self.layer_blocks:
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(lb, idx - offset)

        self.index = idx

    def refresh_layer(self, layer_block, index):
        # if we came straight from adjacent index, push that into cache
        if (
            index + 1 == self.index
            and get_value(self.prefetch_next)
            or index - 1 == self.index
            and get_value(self.prefetch_prev)
        ):
            self.push_data_to_cache(layer_block, self.index)

        if len(layer_block):
            self.load_data(layer_block, index)

    def load_data(self, layer_block, index):
        print(f"Refresh Layer {layer_block.name} at Index {index}")
        # … your existing loading logic …

    def push_data_to_cache(self, layer_block, index):
        name = layer_block.name
        idx = str(index)
        if name not in self.cache_data:
            self.cache_data[name] = {}
            self.cache_meta[name] = {}

        if idx not in self.cache_data[name]:
            file = layer_block[index]
            #fname = Path(file).name.replace(layer_block.dtype, "")
            file_name = str(Path(file).relative_to(layer_block.path)).replace(layer_block.dtype, "")
            layer_name = f"{name} - {index} - {file_name}"
            self.cache_data[name][idx] = self.viewer.layers[layer_name].data
            self.cache_meta[name][idx] = self.viewer.layers[layer_name].affine

    # New: schedules via Future instead of raw Thread
    def fill_cache(self, layer_block, index):
        name = layer_block.name
        idx = str(index)
        if index < 0 or index >= len(layer_block):
            return

        # initialize our caches if this is the first time we see this layer
        if name not in self.cache_data:
            self.cache_data[name] = {}
            self.cache_meta[name] = {}
        if name not in self._cache_futures:
            self._cache_futures[name] = {}

        # schedule the load
        file = layer_block[index]
        future = self._executor.submit(load_data, file, layer_block.dtype)
        self._cache_futures[name][idx] = future

        def _on_done(fut, layer=name, key=idx):
            try:
                if fut.cancelled():
                    return
                data, affine = fut.result()
                self.cache_data[layer][key] = data
                self.cache_meta[layer][key] = affine
            except CancelledError:
                pass
            except Exception as e:  # noqa: BLE001
                print(f"Prefetch callback error for {layer}[{key}]: {e}")
            finally:
                self._cache_futures[layer].pop(key, None)

        future.add_done_callback(_on_done)

    def _prune_caches_and_futures(self, current_idx):

        keep_indices = {str(current_idx)}
        if get_value(self.prefetch_prev):
            keep_indices.update(str(i) for i in range(current_idx - self.cache_radius, current_idx))

        if get_value(self.prefetch_next):
            keep_indices.update(
                str(i) for i in range(current_idx + 1, current_idx + self.cache_radius + 1)
            )

        valid_layers = {b.name for b in self.layer_blocks}

        # prune cache_data & cache_meta
        def prune_dict(d):
            return {
                ln: {k: v for k, v in m.items() if k in keep_indices}
                for ln, m in d.items()
                if ln in valid_layers
            }

        self.cache_data = prune_dict(self.cache_data)
        self.cache_meta = prune_dict(self.cache_meta)
        # cancel & prune futures
        for layer, fmap in list(self._cache_futures.items()):
            if layer not in valid_layers:
                for fut in fmap.values():
                    fut.cancel()
                self._cache_futures.pop(layer, None)
                continue

            # only keep those within keep_indices
            to_delete = [k for k in fmap if k not in keep_indices]
            for k in to_delete:
                fut = self._cache_futures[layer].pop(k, None)
                if fut:
                    fut.cancel()

    def closeEvent(self, event):
        self._executor.shutdown(wait=False)
        super().closeEvent(event)

    def on_prefetch_prev_changed(self, state):
        idx = get_value(self.progressbar)
        if state:
            for lb in self.layer_blocks:
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(lb, idx - offset)
        else:
            self._prune_caches_and_futures(idx)

    def on_prefetch_next_changed(self, state):
        idx = get_value(self.progressbar)
        if state:
            for lb in self.layer_blocks:
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(lb, idx + offset)
        else:
            self._prune_caches_and_futures(idx)

    def on_radius_changed(self, value):
        self.cache_radius = value
        idx = get_value(self.progressbar)
        self._prune_caches_and_futures(idx)

        if get_value(self.prefetch_next):
            for lb in self.layer_blocks:
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(lb, idx + offset)
        if get_value(self.prefetch_prev):
            for lb in self.layer_blocks:
                for offset in range(1, self.cache_radius + 1):
                    self.fill_cache(lb, idx - offset)

    def clear_project(self):
        for layer_block in self.layer_blocks:

            file = layer_block[self.index]
            #file_name = str(Path(file).name).replace(layer_block.dtype, "")
            file_name = str(Path(file).relative_to(layer_block.path)).replace(layer_block.dtype, "")
            layer_name = f"{layer_block.name} - {self.index} - {file_name}"
            if layer_name in self.viewer.layers:
                del self.viewer.layers[layer_name]

            self.layer_layout.removeWidget(layer_block)
            del layer_block

        self.layer_blocks = []
        self.scroll_area.setWidget(self.layer_container)
        self.index = 0

        self.update_max_len()
        self._prune_caches_and_futures(self.index)

        super().clear_project()
