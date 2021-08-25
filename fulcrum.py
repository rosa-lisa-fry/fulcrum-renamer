import argparse
import pandas as pd
import re
import sys

from pathlib import Path
from slugify import slugify


DIRECTION_REGEX = re.compile(r'^([NSEW]{1,2}\.?|North|South|East|West)$', re.I)


def split_c_address_thoroughfare(c_address_thoroughfare):
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


def main(args):
    csv_file = Path(args.path_to_csv_file)
    cwd = csv_file.parent
    
    df = pd.read_csv(str(csv_file))
    
    df['fixed_c_address_thoroughfare'] = df.c_address_thoroughfare.apply(split_c_address_thoroughfare)
    output_file_name_columns = ['district_name', 'district_name_other', 'fixed_c_address_thoroughfare', 'c_address_sub_thoroughfare', 'c_address_suite']
    for col in output_file_name_columns:
        if not col in df.columns:
            df[col] = ''
    df['adjusted_address_rename_value'] = df[output_file_name_columns].fillna('').apply(lambda x: ' '.join(x), axis=1).str.title()

    for guid, address in df[[
        'fulcrum_id', 'adjusted_address_rename_value']].to_records(index=False):
        
        slugified_address = slugify(address, to_lower=True)
        guid_file = cwd / (guid + '.pdf')

        if guid_file.exists():
            existing_files = cwd.glob(slugified_address + '*')
            renamed_file = guid_file.rename(
                slugified_address + '-' + str(len(list(existing_files))) + '.pdf')
            print(f'Renaming {guid_file} to {renamed_file}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert Fulcrum directory from CSV.')
    
    parser.add_argument('path_to_csv_file',
        help='full path to CSV file inside directory containing CSV')
    
    args = parser.parse_args()
    main(args)
