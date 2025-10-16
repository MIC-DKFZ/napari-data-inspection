from pathlib import Path
from typing import Union

from napari._qt.qt_resources import QColoredSVGIcon
from napari_toolkit.containers import setup_vgroupbox
from napari_toolkit.containers.boxlayout import hstack
from napari_toolkit.utils import get_value, set_value
from napari_toolkit.utils.theme import get_theme_colors
from napari_toolkit.utils.utils import connect_widget
from napari_toolkit.widgets import (
    setup_combobox,
    setup_iconbutton,
    setup_lineedit,
    setup_toolbutton,
)
from napari_toolkit.widgets.buttons.tool_button import (  # make get_value,set_value
    activate_option,
    get_option,
    set_options,
)
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLayout, QSizePolicy, QVBoxLayout, QWidget
from vidata import LOADER_REGISTRY
from vidata.file_manager import FileManager

PathLike = Union[str, Path]

REGISTRY_MAPPING = {"Image": "image", "Labels": "mask"}


class LayerBlock(QWidget):
    deleted = Signal(QWidget)
    updated = Signal(QWidget)
    loaded = Signal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fm = FileManager("", "")
        self.include_names = None

        main_layout = QVBoxLayout()
        container, layout = setup_vgroupbox(main_layout)
        # Path
        self.path_ledt = setup_lineedit(
            None,
            placeholder="Path",
            function=self.on_change,
        )
        # // Next Line
        # Layer Name
        self.name_ledt = setup_lineedit(None, placeholder="Layer Name", function=self.on_change)
        # Layer Type
        self.ltype_cbx = setup_combobox(
            None, options=["Image", "Labels"], function=self.on_change_ltype
        )
        # Delete and Load
        self.delete_btn = setup_iconbutton(
            None, "", "delete", theme=get_theme_colors().id, function=self.remove_self
        )
        self.refresh_btn = setup_iconbutton(
            None, "", "right_arrow", theme=get_theme_colors().id, function=self.refresh
        )
        # // Next Line
        # Pattern
        self.pattern_ledt = setup_lineedit(
            None,
            placeholder="File Pattern",
            function=self.on_change,
        )
        # File Type
        file_type_options = list(LOADER_REGISTRY[REGISTRY_MAPPING[self.ltype]].keys())
        self.file_type_cbx = setup_combobox(
            None, options=file_type_options, function=self.on_change_file_type
        )
        # Backend

        # Fix the size
        self.ltype_cbx.setFixedWidth(90)
        self.refresh_btn.setFixedWidth(30)
        self.delete_btn.setFixedWidth(30)

        self.file_type_cbx.setFixedWidth(90)
        self.name_ledt.setMinimumWidth(50)
        self.pattern_ledt.setMinimumWidth(50)

        backend_options = list(LOADER_REGISTRY[REGISTRY_MAPPING[self.ltype]][self.file_type].keys())
        self.backend_btn = setup_toolbutton(
            None, backend_options, tooltips="Backend/Package to load the data"
        )
        self.backend_btn.setFixedWidth(30)

        _ = hstack(layout, [self.path_ledt, self.refresh_btn])
        _ = hstack(layout, [self.name_ledt, self.ltype_cbx, self.delete_btn])
        _ = hstack(layout, [self.pattern_ledt, self.file_type_cbx, self.backend_btn])

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
    def file_type(self):
        return get_value(self.file_type_cbx)[0]

    @property
    def ltype(self):
        return get_value(self.ltype_cbx)[0]

    @property
    def backend(self):
        return get_option(self.backend_btn)

    @property
    def pattern(self):
        return get_value(self.pattern_ledt)

    @property
    def files(self):
        return self.fm.files

    def get_config(self):
        return {
            "name": get_value(self.name_ledt),
            "type": get_value(self.ltype_cbx)[0],
            "path": get_value(self.path_ledt),
            "file_type": get_value(self.file_type_cbx)[0],
            "pattern": get_value(self.pattern_ledt),
            "backend": get_option(self.backend_btn),
        }

    def set_config(self, config):
        set_value(self.name_ledt, config["name"])
        set_value(self.path_ledt, config["path"])
        set_value(self.file_type_cbx, config["file_type"])
        activate_option(self.backend_btn, config.get("backend", None))
        pattern = config.get("pattern", "")
        set_value(self.pattern_ledt, pattern if pattern is not None else "")
        set_value(
            self.ltype_cbx, "Labels" if config["type"].lower() == "semseg" else config["type"]
        )
        self.include_names = config.get("include_names")

    def on_change_ltype(self):
        self.on_change_file_type()

    def on_change_file_type(self):
        backend_options = list(LOADER_REGISTRY[REGISTRY_MAPPING[self.ltype]][self.file_type].keys())
        set_options(self.backend_btn, backend_options)
        self.on_change()

    def on_change(self):
        self.fm = FileManager("", "")

        _icon = QColoredSVGIcon.from_resources("right_arrow")

        _icon = _icon.colored(theme=get_theme_colors().id)
        self.refresh_btn.setIcon(_icon)
        self.updated.emit(self)

    def refresh(self):
        # self.files = collect_files(self.path, self.file_type, get_value(self.pattern_ledt))
        self.fm = FileManager(
            path=self.path,
            file_type=self.file_type,
            pattern=self.pattern,
            include_names=self.include_names,
        )

        if len(self.fm) != 0 and get_value(self.name_ledt) != "":
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

    def load_data(self, path):
        lf = LOADER_REGISTRY[REGISTRY_MAPPING[self.ltype]][self.file_type][self.backend]
        return lf(path)

    def __getitem__(self, item):
        if item < len(self.fm):
            return self.fm[item]
        else:
            return None

    def __len__(self):
        return len(self.fm)


def setup_layerblock(
    layout: QLayout,
    tooltips: str | None = None,
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
