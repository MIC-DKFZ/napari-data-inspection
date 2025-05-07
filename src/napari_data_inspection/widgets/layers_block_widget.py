from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

from napari._qt.qt_resources import QColoredSVGIcon
from napari_toolkit.containers import setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import get_value, set_value
from napari_toolkit.utils.theme import get_theme_colors
from napari_toolkit.utils.utils import connect_widget
from napari_toolkit.widgets import setup_combobox, setup_iconbutton, setup_lineedit
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLayout, QSizePolicy, QVBoxLayout, QWidget


def collect_files(folder_path, file_type):

    if file_type == "" or folder_path == "":
        return []

    if "*" not in file_type:
        file_type = "*" + file_type
    files = sorted(Path(folder_path).glob(file_type))
    return files


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

        self.name_ledt = setup_lineedit(None, placeholder="Name", function=self.on_change)
        self.dtype_ledt = setup_lineedit(None, placeholder="Dtype", function=self.on_change)
        self.refresh_btn = setup_iconbutton(
            None, "", "right_arrow", theme=get_theme_colors().id, function=self.refresh
        )
        self.refresh_btn.setFixedWidth(30)
        self.dtype_ledt.setFixedWidth(60)

        self.path_ledt = setup_lineedit(
            None,
            placeholder="Path",
            function=self.on_change,
        )
        self.ltype_cbx = setup_combobox(None, options=["Image", "Labels"], function=self.on_change)
        self.delete_btn = setup_iconbutton(
            None, "", "delete", theme=get_theme_colors().id, function=self.remove_self
        )
        self.delete_btn.setFixedWidth(30)

        _ = hstack(layout, [self.name_ledt, self.ltype_cbx, self.refresh_btn], stretch=[1, 1, 1])
        _ = hstack(layout, [self.path_ledt, self.dtype_ledt, self.delete_btn], stretch=[1, 1, 1])

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
        return get_value(self.dtype_ledt)

    @property
    def ltype(self):
        return get_value(self.ltype_cbx)[0]

    def get_config(self):
        return {
            "name": get_value(self.name_ledt),
            "path": get_value(self.path_ledt),
            "dtype": get_value(self.dtype_ledt),
            "ltype": get_value(self.ltype_cbx)[0],
        }

    def set_config(self, config):
        set_value(self.name_ledt, config["name"])
        set_value(self.path_ledt, config["path"])
        set_value(self.dtype_ledt, config["dtype"])
        set_value(self.ltype_cbx, config["ltype"])

        # self.refresh()

    def on_change(self):
        self.files = []

        _icon = QColoredSVGIcon.from_resources("right_arrow")

        _icon = _icon.colored(theme=get_theme_colors().id)
        self.refresh_btn.setIcon(_icon)
        self.updated.emit(self)

    def refresh(self):
        self.files = collect_files(self.path, self.dtype)

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
    function: Optional[Callable[[str], None]] = None,
    default: int = None,
    fixed_color: Optional[Any] = None,
    shortcut: Optional[str] = None,
    tooltips: Optional[str] = None,
    stretch: int = 1,
):
    """Create a horizontal switch widget (QHSwitch), configure it, and add it to a layout.

    This function creates a `QHSwitch` widget, populates it with options, sets a default
    selection if provided, and connects an optional callback function. A shortcut key
    can be assigned to toggle between options.

    Args:
        layout (QLayout): The layout to which the QHSwitch will be added.
        options (List[str]): A list of string options for the switch widget.
        function (Optional[Callable[[str], None]], optional): A callback function that takes the selected option as an argument. Defaults to None.
        default (Optional[int], optional): The index of the default selected option. Defaults to None.
        If given this oneis used, else the theme color
        shortcut (Optional[str], optional): A keyboard shortcut to toggle the switch. Defaults to None.
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
