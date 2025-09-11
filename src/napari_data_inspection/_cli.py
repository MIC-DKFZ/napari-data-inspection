import argparse
from pathlib import Path

import napari

from napari_data_inspection import DataInspectionWidget


def main():
    parser = argparse.ArgumentParser(description="Launch Napari with Data Inspection plugin")
    parser.add_argument("-c", "--config", type=Path, default=None, help="Path to YAML config file")
    parser.add_argument("-s", "--split", choices=["train", "val", "test"], default=None)
    parser.add_argument("-f", "--fold", type=int, default=None)
    args = parser.parse_args()
    config_path = args.config

    viewer = napari.Viewer()
    widget = DataInspectionWidget(viewer)
    if config_path is not None:
        widget._load_yaml_cfg(args.config, split=args.split, fold=args.fold)

    viewer.window.add_dock_widget(
        widget,
        name="Data Inspection Widget (Data Inspection)",
        area="right",  # 'right' | 'left' | 'bottom' | 'top'
        add_vertical_stretch=True,  # optional, makes layout nicer
        tabify=False,  # set True to tab with existing dock
    )

    napari.run()


if __name__ == "__main__":
    main()
