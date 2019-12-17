#!/usr/bin/env python

import yaml
import argparse
import os
import sys
from pymatgen.ext.matproj import MPRester

config_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(config_path)
from config import MP_api_key  # noqa: E402


def load_yaml(path):
    # loads a .yml file from the specified path
    with open(path, 'r') as loadfile:
        read_yaml = yaml.safe_load(loadfile)
    return read_yaml


def get_MP_structures(mpid_list, mp_key=MP_api_key):
    # gets structure objects from mpids list
    structures = []
    with MPRester(mp_key) as m:
        for mpid in mpid_list:
            try:
                structure = m.get_structures(mpid, final=True)[0]
                structures.append(structure)
            except BaseException:
                print('%s is not a valid mp-id' % mpid)
    return structures


def get_magnetic_structures(structures):
    # assigns magnetism to structures
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r',
        '--read_yaml_path',
        help='Path to the .yml file to read',
        type=str,
        required=True)
    parser.add_argument(
        '-o',
        '--output_directory_path',
        help='Path to where the output directory WILL BE created. ' +
        'User-specify /Path/To/Folder, full path will add the ' +
        '"Relaxation_Scheme" value from .yml file',
        type=str,
        required=True)

    args = parser.parse_args()

    if os.path.exists(args.read_yaml_path):
        read_dict = load_yaml(args.read_yaml_path)
        structures = get_MP_structures(read_dict['MPIDs'])
    else:
        print('%s is not a valid path to a .yml file' % args.read_yaml_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
