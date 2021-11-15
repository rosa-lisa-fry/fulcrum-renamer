import ipywidgets as w
import pandas as pd
import re
import sys

from IPython.display import display_markdown
from pathlib import Path
from slugify import slugify
from typing import Dict, List, Optional
from uuid import uuid4
from ipyfilechooser import FileChooser


DIRECTION_REGEX = re.compile(r"^([NSEW]{1,2}\.?|North|South|East|West)$", re.I)


def split_c_address_thoroughfare(c_address_thoroughfare: str) -> str:

    if not isinstance(c_address_thoroughfare, str):
        return ""

    output = []
    possible_direction, rest_of_address = c_address_thoroughfare.split(" ", maxsplit=1)

    match = DIRECTION_REGEX.match(possible_direction)

    if match:
        output.extend([rest_of_address, possible_direction])
    else:
        output.append(c_address_thoroughfare)

    return " ".join(output)


def get_ids_from_source_csv(path_to_csv: str) -> pd.DataFrame:
    df = pd.read_csv(path_to_csv)
    if not "_record_id" in df.columns:
        raise Exception(f"Can't find the _record_id column in the CSV {path_to_csv}!")
    return df["_record_id"].unique().tolist()


def generate_renamed_files_from_export_csv(path_to_csv: str) -> Dict[str, str]:

    df = pd.read_csv(path_to_csv)

    df["fixed_c_address_thoroughfare"] = df.c_address_thoroughfare.apply(
        split_c_address_thoroughfare
    )

    output_file_name_columns = [
        "district_name",
        "district_name_other",
        "fixed_c_address_thoroughfare",
        "c_address_sub_thoroughfare",
        "c_address_suite",
    ]

    for col in output_file_name_columns:
        if not col in df.columns:
            df[col] = ""

    df["adjusted_address_rename_value"] = (
        df[output_file_name_columns]
        .fillna("")
        .apply(lambda x: " ".join(x), axis=1)
        .str.title()
        .apply(lambda x: slugify(x, to_lower=True))
    )

    return dict(df[["fulcrum_id", "adjusted_address_rename_value"]].values)


def run(source_csv: str, export_csv: str, output_directory: str):

    # Read the source CSV and get the _record_ids of interest
    record_ids_to_keep = get_ids_from_source_csv(source_csv)  # List[str]

    # Read the target CSV and caluclate a dictionary of record_id::new filenames
    fulcrum_id_to_filename_map = generate_renamed_files_from_export_csv(
        export_csv
    )  # Dict[str, str]

    # Target directory is where the PDF files live
    export_directory = Path(export_csv).parent  # Path
    if not export_directory.exists():
        raise ValueError(f"Path {export_directory} does not exist!")

    # Output directory where the renamed files go
    output_directory = Path(output_directory).resolve()  # Path
    output_directory.mkdir(exist_ok=True)

    print(
        f"Saving renamed files with the following IDs to {output_directory}: {record_ids_to_keep}"
    )

    # For each PDF file in the export directory with the name <uuid>.pdf

    for fp in export_directory.glob("*.pdf"):

        # If the <uuid> of that file is in the
        # list of record IDs in the source CSV.

        if fp.stem in record_ids_to_keep:

            # Obtain the new filename by looking up the
            # id in the dictionary of ids->converted filenames.
            new_filename = fulcrum_id_to_filename_map.get(fp.stem)  # str

            if not new_filename:
                print(
                    f"File {fp.name} is in the source CSV, but not in the export CSV!"
                )
                continue

            renamed_file = output_directory / f"{new_filename}.pdf"  # Path

            # If the renamed file already exists
            # in the target directory, then append
            # an incrementing number to the filename
            # to ensure uniqueness.

            if renamed_file.exists():
                existing_files = output_directory.glob(new_filename + "*")
                renamed_file = output_directory / (
                    "-".join(new_filename, str(len(list(existing_files))), ".pdf")
                )  # Path

            # Read in the original file and save
            # out to disk in the new output directory

            print(f"Renaming {fp} to {renamed_file}")
            renamed_file.write_bytes(fp.read_bytes())

        else:
            # Do Nothing
            print(f"Skipping {fp}")


def prep_file_picker(
    title: str, filter_pattern: Optional[str] = None, show_only_dirs: bool = False
) -> FileChooser:

    fc = FileChooser(title=f"<b>{title}</b>")
    fc.register_callback(on_selection_callback)

    if filter_pattern:
        fc.filter_pattern = filter_pattern

    if show_only_dirs:
        fc.show_only_dirs = True

    return fc


def on_selection_callback(e):
    if source_csv.selected and export_csv.selected and output_dir.selected_path:
        run_button.disabled = False
    else:
        run_button.disabled = True


def on_btn_click(e):
    if source_csv.selected and export_csv.selected and output_dir.selected_path:
        run(source_csv.selected, export_csv.selected, output_dir.selected_path)


source_csv = prep_file_picker(
    "Source CSV contaning list of UUIDs to rename", filter_pattern="*.csv"
)
export_csv = prep_file_picker("CSV in the export directory", filter_pattern="*.csv")
output_dir = prep_file_picker(
    "Directory to save renamed PDF files", show_only_dirs=True
)

hbox = w.HBox([source_csv, export_csv])
hbox2 = w.HBox([output_dir])
run_button = w.Button(
    description="Run PDF Switcheroo",
    icon="check",
    disabled=True,
    button_style="success",
    layout=w.Layout(width="99%"),
)
run_button.on_click(on_btn_click)

display_markdown("# PDF Switcheroo App", raw=True)
display_markdown(
    "Before you begin, please create a folder where you would like to save the renamed PDF files.",
    raw=True,
)

display(hbox)
display_markdown(
    "Please select a directory where you would like to save the renamed PDF files:",
    raw=True,
)
display(hbox2)
display(run_button)
