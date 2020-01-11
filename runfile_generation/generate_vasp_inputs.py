#!/usr/bin/env python

import argparse
import os
import copy
from runfile_generation.runfilegeneration import *
from yaml_generation.create_input_yaml import write_yaml

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r', '--readfile_path',
        help='Read-in .yml file path; best to put "" around path name',
        type=str,
        required=True)
    args = parser.parse_args()

    return args

def main():
    args = argument_parser()
    LY = LoadYaml(args.readfile_path)
    PSO = PmgStructureObjects(LY.mpids, LY.paths)
    M = Magnetism(PSO.structures_dict, LY.magnetization_scheme)
    CT = CalculationType(M.magnetized_structures_dict, LY.calculation_type)
    WVF = WriteVaspFiles(CT.calculation_structures_dict, LY.calculation_type, None, None)

    with open('defect/test.txt', 'w') as file:
        file.write(str(M.unique_magnetizations))
        file.close()
    # currently writing just the POSCAR files

if __name__ == "__main__":
    main()
