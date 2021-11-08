
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



DIRECTION_REGEX = re.compile(r'^([NSEW]{1,2}\.?|North|South|East|West)$', re.I)


def split_c_address_thoroughfare(c_address_thoroughfare: str) -> str:
    
    if not isinstance(c_address_thoroughfare, str):
        return ''
    
    output = []
    possible_direction, rest_of_address = c_address_thoroughfare.split(' ', maxsplit=1)
    
    match = DIRECTION_REGEX.match(possible_direction)
    
    if match:
        output.extend([rest_of_address, possible_direction])
    else:
        output.append(c_address_thoroughfare)
        
    return ' '.join(output)


def get_ids_from_source_csv(path_to_csv: str) -> pd.DataFrame:
    df = pd.read_csv(path_to_csv)
    if not '_record_id' in df.columns:
        raise Exception(f"Can't find the _record_id column in the CSV {path_to_csv}!")
    return df['_record_id'].unique().tolist()

    
def generate_renamed_files_from_target_csv(path_to_csv: str) -> Dict[str, str]:
    
    df = pd.read_csv(path_to_csv)
    
    df['fixed_c_address_thoroughfare'] = df.c_address_thoroughfare.apply(split_c_address_thoroughfare)
    
    output_file_name_columns = [
        'district_name', 
        'district_name_other', 
        'fixed_c_address_thoroughfare', 
        'c_address_sub_thoroughfare', 
        'c_address_suite'
    ]
    
    for col in output_file_name_columns:
        if not col in df.columns:
            df[col] = ''
            
    df['adjusted_address_rename_value'] = (
        df[output_file_name_columns]
        .fillna('')
        .apply(lambda x: ' '.join(x), axis=1)
        .str.title()
        .apply(lambda x: slugify(x, to_lower=True))
    )
    
    return dict(df[['fulcrum_id', 'adjusted_address_rename_value']].values)


def run(source_csv: str, target_csv: str):
    
    # Read the source CSV and get the _record_ids of interest
    record_ids_to_keep = get_ids_from_source_csv(source_csv) # List[str]
    
    # Read the target CSV and caluclate a dictionary of record_id::new filenames
    fulcrum_id_to_filename_map = generate_renamed_files_from_target_csv(target_csv) # Dict[str, str]

    # Target directory is where the PDF files live
    target_directory = Path(target_csv).parent # Path'

    # Trash directory is where we want to move unwanted files.
    trash_directory = target_directory / 'unwanted_files' # Path
    trash_directory.mkdir(exist_ok=True)

    print(f'Keeping files with the following IDs: {record_ids_to_keep}')

    # For each file in the directory with the name <uuid>.pdf

    for fp in target_directory.glob('*.pdf'):

        # If the <uuid> of that file is in the 
        # list of record IDs in the source CSV.

        if fp.stem in record_ids_to_keep:

            # Obtain the new filename by looking up the
            # id in the dictionary of ids->converted filenames.
            new_filename = fulcrum_id_to_filename_map.get(fp.stem) # str

            if not new_filename:
                print(f'File {fp.name} is in the source CSV and the destination directory, but not in the target CSV!')
                continue

            renamed_file = target_directory / f'{new_filename}.pdf' # Path

            # If the renamed file already exists
            # in the target directory, then append
            # an incrementing number to the filename
            # to ensure uniqueness.

            if renamed_file.exists():
                existing_files = target_directory.glob(new_filename + '*')
                renamed_file = Path('-'.join(new_filename, str(len(list(existing_files))), '.pdf')) # Path

            # Rename the file to the newly calculated
            # filename.
            
            print(f"Renaming {fp.name} to {renamed_file}")
            fp.rename(renamed_file)

        else:
            # If the file is not in the list of 
            # records to keep, then delete the file.

            print(f"{fp.name} not in CSV, moving to unwanted directory")
            fp.replace(trash_directory / fp.name)
            
            
def prep_file_picker(
    title: str, 
    filter_pattern: Optional[str] = None
) -> FileChooser:
    
    fc = FileChooser(title=f'<b>{title}</b>')
    fc.register_callback(on_selection_callback)
    
    if filter_pattern:
        fc.filter_pattern = filter_pattern
        
    return fc


def on_selection_callback(e):
    if source_csv.selected and target_csv.selected:
        run_button.disabled = False
    else:
        run_button.disabled = True


def on_btn_click(e):
    if source_csv.selected and target_csv.selected:
        run(source_csv.selected, target_csv.selected)


source_csv = prep_file_picker('Unevaluated CSV')
target_csv = prep_file_picker('Target CSV')

hbox = w.HBox([source_csv, target_csv])
run_button = w.Button(
    description='Run PDF Switcheroo', 
    icon='check',
    disabled=True,
    button_style='success',
    layout=w.Layout(width='99%')
)
run_button.on_click(on_btn_click)

display_markdown('# PDF Switcheroo App', raw=True)
display_markdown('Please select your CSVs files.', raw=True)
display(hbox)
display(run_button)
