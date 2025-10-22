from typing import TYPE_CHECKING

import napari
import numpy as np
from napari.layers import Image, Labels
from napari_toolkit.containers import setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import get_value
from napari_toolkit.widgets import (
    setup_acknowledgements,
    setup_checkbox,
    setup_progressbaredit,
    setup_pushbutton,
    setup_spinbox,
    setup_label,
)
from qtpy.QtGui import QKeySequence
from qtpy.QtWidgets import QShortcut, QSizePolicy, QVBoxLayout, QWidget
from napari.utils.colormaps import label_colormap

if TYPE_CHECKING:
    import torch


class DatasetInspectionWidget(QWidget):

    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        dataset: "torch.utils.data.Dataset",
        channel_first: bool = True,
        rescale: bool = False,
        no_label: bool = False,
        bg_class: int = 0,
    ):
        super().__init__()
        self.viewer = viewer

        self.dataset = dataset
        self.index = 0

        self.channel_first = channel_first
        self.rescale = rescale
        self.no_label = no_label
        self.bg_class = bg_class

        self.img_layer = None
        self.label_layer = None

        # Build Gui
        self.build_gui()

        # Key bindings …
        key_d = QShortcut(QKeySequence("d"), self)
        key_d.activated.connect(self.progressbar.increment_value)
        self.progressbar.next_button.setToolTip("Press [d] for next")
        key_a = QShortcut(QKeySequence("a"), self)
        key_a.activated.connect(self.progressbar.decrement_value)
        self.progressbar.prev_button.setToolTip("Press [a] for previous")
        key_q = QShortcut(QKeySequence("q"), self)
        key_q.activated.connect(self.viewer.close)

        self.on_index_changed()

    def build_gui(self):
        main_layout = QVBoxLayout()

        self.build_gui_navigation(main_layout)
        setup_acknowledgements(main_layout)

        self.setLayout(main_layout)

    def build_gui_navigation(self, layout):
        _container, _layout = setup_vgroupbox(layout, "Navigation")
        self.progressbar = setup_progressbaredit(
            _layout, 0, len(self.dataset), self.index, function=self.on_index_changed
        )
        self.progressbar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.channel_first_ckbx = setup_checkbox(
            None, "Channel First", self.channel_first, self.reload
        )
        self.rescale_ckbx = setup_checkbox(None, "Rescale", self.rescale, self.reload)
        self.no_label_ckbx = setup_checkbox(None, "No Label", self.no_label, self.reload)
        hstack(_layout, [self.channel_first_ckbx, self.rescale_ckbx, self.no_label_ckbx])

        lbl = setup_label(None, "BG Class:")
        self.bg_spin_box = setup_spinbox(
            None, 0, 255, default=self.bg_class, function=self.change_cm
        )
        hstack(_layout, [lbl, self.bg_spin_box])

        _ = setup_pushbutton(_layout, "Refresh", self.on_index_changed)

    def on_index_changed(self):
        index = get_value(self.progressbar)
        data = self.dataset[index]

        img = data[0] if isinstance(data, tuple) else data
        lbl = data[1] if isinstance(data, tuple) and not get_value(self.no_label_ckbx) else None
        meta = data[2] if isinstance(data, tuple) and len(data) > 2 else None
        name = meta["file_name"] if isinstance(meta, dict) and "file_name" in meta else index

        img = np.array(img) if not isinstance(img, np.ndarray) else img

        if get_value(self.channel_first_ckbx):
            img = img.transpose(1, 2, 0)

        if get_value(self.rescale_ckbx):
            img = img - np.min(img)
            img = img / np.max(img)

        # --- Image ---
        if self.img_layer is not None:
            self.img_layer.data = img
            self.img_layer.name = f"Image_{name}"
        else:
            self.img_layer = Image(data=img, name=f"Image_{name}")
            self.viewer.add_layer(self.img_layer)
        # --- Label --- #
        if lbl is not None:
            if self.label_layer is not None:
                self.label_layer.data = lbl
                self.label_layer.name = f"Label_{name}"
            else:
                cm = label_colormap(
                    num_colors=49, seed=0.5, background_value=get_value(self.bg_spin_box)
                )
                self.label_layer = Labels(data=lbl, name=f"Label_{name}", colormap=cm)
                self.viewer.add_layer(self.label_layer)

    def reload(self):
        if self.label_layer in self.viewer.layers:
            self.viewer.layers.remove(self.label_layer)

        if self.img_layer in self.viewer.layers:
            self.viewer.layers.remove(self.img_layer)

        self.label_layer = None
        self.img_layer = None

        self.on_index_changed()

    def change_cm(self):
        if self.label_layer is not None:
            cm = label_colormap(
                num_colors=49, seed=0.5, background_value=get_value(self.bg_spin_box)
            )
            self.label_layer.colormap = cm


def run_dataset_inspection(dataset: "torch.utils.data.Dataset", *args, **kwargs):
    viewer = napari.Viewer()
    widget = DatasetInspectionWidget(viewer, dataset, *args, **kwargs)

    viewer.window.add_dock_widget(
        widget,
        name="Data Inspection Widget (Data Inspection)",
        area="right",  # 'right' | 'left' | 'bottom' | 'top'
        add_vertical_stretch=True,  # optional, makes layout nicer
        tabify=False,  # set True to tab with existing dock
    )

    napari.run()
