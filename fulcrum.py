from pathlib import Path
import pandas as pd
from slugify import slugify
import argparse
import sys


def main(args):
    csv_file = Path(args.path_to_csv_file)
    cwd = csv_file.parent
    
    df = pd.read_csv(str(csv_file))
    
    if 'output_column' not in df.columns:
        print('There is no "output_column" column in the CSV file! Panic.')
        sys.exit(1)

    for guid, address in df[[
        'fulcrum_id', 'output_column']].to_records(index=False):
        
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
