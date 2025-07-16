from pathlib import Path
from typing import TYPE_CHECKING

from napari_toolkit.containers import setup_scrollarea, setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import set_value
from napari_toolkit.widgets import (
    setup_acknowledgements,
    setup_checkbox,
    setup_iconbutton,
    setup_label,
    setup_lineedit,
    setup_progressbaredit,
    setup_pushbutton,
    setup_spinbox,
)
from qtpy.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from napari_data_inspection.widgets.layers_block_widget import setup_layerblock

if TYPE_CHECKING:
    import napari


class DataInspectionWidget_GUI(QWidget):
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

    def build_gui(self):
        main_layout = QVBoxLayout()

        # Header
        _container, _layout = setup_vgroupbox(main_layout, "Project")
        self.project_name = setup_lineedit(_layout, placeholder="Project Name")

        # IO
        lbtn = setup_pushbutton(None, "Load", function=self.load_project)
        sbtn = setup_pushbutton(None, "Save", function=self.save_project)
        hstack(_layout, [lbtn, sbtn])
        cln = setup_pushbutton(None, "Clear", function=self.clear_project)
        lbl = setup_label(None, "")
        hstack(_layout, [cln, lbl])

        # Progressbar
        _container, _layout = setup_vgroupbox(main_layout, "Navigation")
        self.progressbar = setup_progressbaredit(
            _layout, 0, 1, self.index, function=self.on_index_changed
        )
        self.progressbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.search_name = setup_lineedit(
            _layout, placeholder="Enter Filename ...", function=self.on_name_entered
        )

        self.keep_properties = setup_checkbox(_layout, "Keep Layer Properties", True)
        self.keep_camera = setup_checkbox(_layout, "Keep Camera", False)

        _container, _layout = setup_vgroupbox(main_layout, "Prefetching")
        self.prefetch_prev = setup_checkbox(
            None, "Previous", True, function=self.on_prefetch_prev_changed
        )
        self.prefetch_next = setup_checkbox(
            None, "Next", True, function=self.on_prefetch_next_changed
        )
        hstack(_layout, [self.prefetch_prev, self.prefetch_next])
        label = setup_label(None, "Prefetch Radius")
        self.radius = setup_spinbox(None, 1, function=self.on_radius_changed)
        hstack(_layout, [label, self.radius])

        # Add Layer
        new_btn = setup_iconbutton(None, "New Layer", "add", function=self.on_new_layer)
        add_btn = setup_iconbutton(None, "Load All", "right_arrow", function=self.on_load_all)
        _ = hstack(main_layout, [new_btn, add_btn])

        # Scroll Area
        self.scroll_area = setup_scrollarea(main_layout)
        self.scroll_area.setWidgetResizable(True)

        # Layers
        self.layer_container, self.layer_layout = setup_vgroupbox(None, "Layers")
        self.layer_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layer_container.setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.layer_container)

        setup_acknowledgements(main_layout)

        self.setLayout(main_layout)

    def add_layer(self, config):

        layer_block = setup_layerblock(self.layer_layout)
        layer_block.set_config(config)

        layer_block.deleted.connect(self.on_layer_removed)
        layer_block.updated.connect(self.on_layer_updated)
        layer_block.loaded.connect(self.on_layer_loaded)

        self.layer_blocks.append(layer_block)

        self.scroll_area.setWidget(self.layer_container)

        vertical_scrollbar = self.scroll_area.verticalScrollBar()
        vertical_scrollbar.setValue(vertical_scrollbar.maximum())

    # GUI Events
    def on_index_changed(self):
        pass

    def on_name_entered(self):
        pass

    def on_load_all(self):
        pass

    def on_new_layer(self):
        config = {"name": "", "path": "", "dtype": "", "ltype": "Image"}
        self.add_layer(config)

    # Layer Events
    def on_layer_loaded(self):
        pass

    def on_layer_removed(self, block):
        index = self.layer_blocks.index(block)
        if 0 <= index < len(self.layer_blocks):

            file = block[self.index]
            if file is not None:
                #file_name = str(Path(file).name).replace(block.dtype, "")
                file_name = str(Path(file).relative_to(block.path)).replace(block.dtype,
                                                                                  "")
                layer_name = f"{block.name} - {self.index} - {file_name}"
                if layer_name in self.viewer.layers:
                    del self.viewer.layers[layer_name]
            del self.layer_blocks[index]

    def on_layer_updated(self):
        pass

    # IO Events
    def load_project(self):
        pass

    def save_project(self):
        pass

    def clear_project(self):
        self.index = 0
        set_value(self.progressbar, self.index)
        set_value(self.project_name, "")
        set_value(self.search_name, "")
        set_value(self.keep_properties, True)
        set_value(self.keep_camera, False)
        set_value(self.prefetch_prev, True)
        set_value(self.prefetch_next, True)
        set_value(self.radius, 1)

    def on_prefetch_prev_changed(self, state):
        pass

    def on_prefetch_next_changed(self, state):
        pass

    def on_radius_changed(self, value):
        pass
