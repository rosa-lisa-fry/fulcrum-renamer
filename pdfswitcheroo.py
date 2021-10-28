#!/usr/bin/env python
# coding: utf-8

# - CSV containing a list of `site-id`, `filename` pairs. 
# - A directory of files with a lot of PDF `site-ids`
# - Wants to remove the extra files based on the `site-ids` in the CSV
# - Then wants to rename the file from `site-ids` to the `filename` in the CSV

# In[2]:


import argparse
import pandas as pd
import re
import sys

from pathlib import Path
from slugify import slugify
from typing import Dict, List


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


def generate_renamed_files_based_on_csv(path_to_csv: str) -> Dict[str, str]:
    
    csv_file = Path(path_to_csv_file)
    
    df = pd.read_csv(str(csv_file))
    
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
    )
    
    return dict(df[['fulcrum_id', 'adjusted_address_rename_value']].values)


# In[3]:


def main(args):
    
    # Read the CSV
    fulcrum_id_to_name_map = generate_renamed_files_based_on_csv(args.path_to_csv_file) # Dict[str, str]
    
    # For each file in the directory with the name <uuid>.pdf
    for fp in Path(args.path_to_target_directory).glob('*.pdf'):
        # If the <uuid> of that file is a key in 
        # the dict of <uuid>: <renamed-file>, then
        # rename that file.
        if fp.stem in fulcrum_id_to_name_map.keys():
            new_filename = fulcrum_id_to_name_map[fp.stem]
            print(f"Renaming {fp.name} tp {new_filename}")
            fp.rename(new_filename)
        else:
            # If not in the dict, delete
            # the file.
            print(f"{fp.stem} not in CSV, deleting: {fulcrum_id_to_name_map.keys()}")
            fp.unlink()
            


# In[ ]:


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert and delete unnecessary Fulcrum files.')
    
    parser.add_argument('path_to_csv_file',
        help='full path to CSV file directory.')
    
    parser.add_argument('path_to_target_directory',
        help='full path to the directory of files to be renamed.')
    
    args = parser.parse_args()
    main(args)

