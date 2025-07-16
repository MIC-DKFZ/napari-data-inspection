from pathlib import Path
from typing import Optional

from napari._qt.qt_resources import QColoredSVGIcon
from napari_toolkit.containers import setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import get_value, set_value
from napari_toolkit.utils.theme import get_theme_colors
from napari_toolkit.utils.utils import connect_widget
from napari_toolkit.widgets import setup_combobox, setup_iconbutton, setup_lineedit
from natsort import natsorted
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLayout, QSizePolicy, QVBoxLayout, QWidget

from napari_data_inspection.utils.data_loading import LOADER_REGISTRY


def collect_files(folder_path, file_type, pattern=None):

    if file_type == "" or folder_path == "":
        return []

    if pattern is None:
        pattern = "*"
    elif "*" not in pattern:
        pattern = "*" + pattern

    files = list(Path(folder_path).glob(pattern + file_type))
    files = natsorted(files, key=lambda p: str(p))

    return list(files)


class LayerBlock(QWidget):
    deleted = Signal(QWidget)
    updated = Signal(QWidget)
    loaded = Signal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = []
        self.status = None

        main_layout = QVBoxLayout()
        container, layout = setup_vgroupbox(main_layout)
        self.path_ledt = setup_lineedit(
            layout,
            placeholder="Path",
            function=self.on_change,
        )
        self.name_ledt = setup_lineedit(None, placeholder="Layer Name", function=self.on_change)
        dtype_options = list(LOADER_REGISTRY.keys())
        self.dtype_cbx = setup_combobox(None, options=dtype_options, function=self.on_change)
        self.refresh_btn = setup_iconbutton(
            None, "", "right_arrow", theme=get_theme_colors().id, function=self.refresh
        )
        self.refresh_btn.setFixedWidth(30)

        self.dtype_cbx.setFixedWidth(90)

        self.pattern_ledt = setup_lineedit(
            None,
            placeholder="File Pattern",
            function=self.on_change,
        )
        self.ltype_cbx = setup_combobox(None, options=["Image", "Labels"], function=self.on_change)
        self.delete_btn = setup_iconbutton(
            None, "", "delete", theme=get_theme_colors().id, function=self.remove_self
        )
        self.delete_btn.setFixedWidth(30)
        self.ltype_cbx.setFixedWidth(90)
        _ = hstack(
            layout, [self.name_ledt, self.ltype_cbx, self.refresh_btn]
        )  # , stretch=[1, 1, 1])
        _ = hstack(
            layout, [self.pattern_ledt, self.dtype_cbx, self.delete_btn]
        )  # , stretch=[1, 1, 1])

        self.setLayout(main_layout)
        layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    @property
    def name(self):
        return get_value(self.name_ledt)

    @property
    def path(self):
        return get_value(self.path_ledt)

    @property
    def dtype(self):
        return get_value(self.dtype_cbx)[0]

    @property
    def ltype(self):
        return get_value(self.ltype_cbx)[0]

    def get_config(self):
        return {
            "name": get_value(self.name_ledt),
            "path": get_value(self.path_ledt),
            "dtype": get_value(self.dtype_cbx)[0],
            "pattern": get_value(self.pattern_ledt),
            "ltype": get_value(self.ltype_cbx)[0],
        }

    def set_config(self, config):
        set_value(self.name_ledt, config["name"])
        set_value(self.path_ledt, config["path"])
        set_value(self.dtype_cbx, config["dtype"])
        set_value(self.pattern_ledt, config.get("pattern", ""))
        set_value(self.ltype_cbx, config["ltype"])

        # self.refresh()

    def on_change(self):
        self.files = []

        _icon = QColoredSVGIcon.from_resources("right_arrow")

        _icon = _icon.colored(theme=get_theme_colors().id)
        self.refresh_btn.setIcon(_icon)
        self.updated.emit(self)

    def refresh(self):
        self.files = collect_files(self.path, self.dtype, get_value(self.pattern_ledt))

        if len(self.files) != 0 and get_value(self.name_ledt) != "":
            _icon = QColoredSVGIcon.from_resources("check")
            _icon = _icon.colored(color="green")
            self.refresh_btn.setIcon(_icon)

            self.loaded.emit(self)

    def remove_self(self):
        self.deleted.emit(self)
        parent_layout = self.parentWidget().layout()
        if parent_layout:
            parent_layout.removeWidget(self)
        self.setParent(None)
        self.deleteLater()

    def __getitem__(self, item):
        if item < len(self.files):
            return self.files[item]

    def __len__(self):
        return len(self.files)


def setup_layerblock(
    layout: QLayout,
    tooltips: Optional[str] = None,
    stretch: int = 1,
):
    """Create a horizontal switch widget (QHSwitch), configure it, and add it to a layout.

    This function creates a `QHSwitch` widget, populates it with options, sets a default
    selection if provided, and connects an optional callback function. A shortcut key
    can be assigned to toggle between options.

    Args:
        layout (QLayout): The layout to which the QHSwitch will be added.
        tooltips (Optional[str], optional): Tooltip text for the widget. Defaults to None.
        stretch (int, optional): The stretch factor for the spinbox in the layout. Defaults to 1.

    Returns:
        QWidget: The configured QHSwitch widget added to the layout.
    """
    _widget = LayerBlock()
    return connect_widget(
        layout,
        _widget,
        widget_event=None,
        function=None,
        shortcut=None,
        tooltips=tooltips,
        stretch=stretch,
    )


if __name__ == "__main__":
    path_imgs = "/home/l727r/Documents/E132-Rohdaten/nnUNetv2/Dataset181_Kaggle2025_BYU_FlagMot_BartleysData/imagesTr"
    dtype_imgs = ".nii.gz"
    patterns_imgs = "*_0000"

    path_gt = "/home/l727r/Documents/E132-Rohdaten/nnUNetv2/Dataset181_Kaggle2025_BYU_FlagMot_BartleysData/labelsTr"
    dtype_gt = ".nii.gz"
    patterns_gt = None

    path_pred = "/home/l727r/Documents/cluster-checkpoints-all/isensee/nnUNet_results_kaggle2025_byu/Dataset185_Kaggle2025_BYU_FlagellarMotors_mergedExternalBartley_384/MotorRegressionTrainer_BCEtopK20Loss_moreDA__nnUNetResEncUNetMPlans__3d_fullres_filt16/cv_results_nifti"
    dtype_pred = ".nii.gz"
    patterns_pred = "10*__instseg"

    files_imgs = collect_files(path_imgs, dtype_imgs, patterns_imgs)
    files_gt = collect_files(path_gt, dtype_gt, patterns_gt)
    files_pred = collect_files(path_pred, dtype_pred, patterns_pred)
    # print(files_imgs, files_gt, files_pred)
    for a, b, c in zip(files_imgs, files_gt, files_pred, strict=False):
        print(a.name, b.name, c.name)
