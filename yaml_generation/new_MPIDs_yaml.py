#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import yaml
import argparse
#import argcomplete
import os
import sys
from pymatgen.ext.matproj import MPRester
import json
from configuration.config import MP_api_key
from yaml.scanner import ScannerError
from pymatgen.core.periodic_table import Element
from pymatgen.io.vasp.inputs import Incar
from pathlib import Path


###############################################################################
''' GLOBAL VARIABLES: IF YOU CHANGE, THEY COULD BREAK '''

''' STARTING DICTIONARY '''

exit_commands = ['escape', 'quit', 'stop', 'exit', 'no mas']

default_dictionary = dict(INCAR_Tags={'AUTO_TIME': 24, 'NPAR': 1},
                          Relaxation_Set='MPRelaxSet',
                          Magnetization_Scheme={'Scheme': 'FM'},
                          Max_Submissions=1,
                          Convergence_Scheme='Single-Step',
                          Calculation_Type={'Type': 'bulk'},
                          MPIDs={})

allowed_relaxation_sets = ['MPRelaxSet', 'MITRelaxSet', 'MPMetalRelaxSet',
                           'MPHSERelaxSet', 'MPStaticSet']

allowed_magnetism = ['FM', 'AFM', 'preserve', 'FM+AFM']

allowed_convergence_schemes = ['Single-Step', 'BareRelaxSet']

allowed_calculation_types = ['bulk', 'defect']

###############################################################################

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_pos_int(s):
    try:
        int(s)
        if int(s) > 0:
            return True
        else:
            return False
    except ValueError:
        return False


def is_mpid(mpid):
    with MPRester(MP_api_key) as m:
        try:
            structure = m.get_structures(mpid, final=True)[0]
            return True
        except BaseException:
            print('%s is not a valid mp-id' % mpid)
            return False


def validate_general_positive_integer(tag, default_value, prompt_statement):
    print('%s; default is %s' % (tag, default_value))
    integer_value = input(prompt_statement + ': should be positive integer\n')
    if integer_value.lower() in exit_commands:
        print('Exiting: default value "%s" will be used' % default_value)
        return default_value
    if is_pos_int(integer_value) == True:
        return int(integer_value)
    else:
        print('"%s" not an accepted value; try again' % string_value)
        return validate_general_string(accepted_values, prompt_statement)


def validate_general_string(tag, default_value, accepted_values, prompt_statement):
    print('%s; default is %s' % (tag, default_value))
    string_value = input(prompt_statement + str(accepted_values) + ')\n')
    if string_value in accepted_values:
        return string_value
    elif string_value.lower() in exit_commands:
        print('Exiting: default value "%s" will be used' % default_value)
        return default_value
    else:
        print('"%s" not an accepted value; try again' % string_value)
        return validate_general_string(tag, default_value, accepted_values, prompt_statement)


def validate_incar_tags(default_values):
    print('Add/remove INCAR_Tags; existing tags are %s' % default_values)
    add_or_remove = input('Add or remove tags?\n')
    if add_or_remove.lower() == 'add':
        tag = input('Name of tag to add\n')
        value = input('Value of tag to add\n')
        if is_float(value) == True:
            default_values[tag] = float(value)
        else:
            default_values[tag] = value
        validate_incar_tags(default_values)
    elif add_or_remove.lower() == 'remove':
        tag = input('Name of tag to remove\n')
        default_values.pop(tag, None)
        validate_incar_tags(default_values)
    elif add_or_remove.lower() in exit_commands:
        return default_values
    else:
        print('Not a valid option; try again')
        validate_incar_tags(default_values)


def validate_magnetization(default_value, accepted_values):
    print('Magnetization_Scheme; default is %s' % default_value)
    magnetization = input('Scheme (%s' % accepted_values + ')\n')
    if magnetization.upper() == 'FM':
        default_value['Scheme'] = 'FM'
        return default_value
    elif magnetization.lower() == 'preserve':
        default_value['Scheme'] = 'preserve'
        return default_value
    elif magnetization.upper() == 'AFM':
        default_value['Scheme'] = 'AFM'
        max_number = input('Max number of antiferromagnetic structures\n')
        if is_pos_int(max_number) == True:
            default_value['Max_antiferro'] = int(max_number)
            return default_value
        else:
            print('Not valid positive integer; try again')
            validate_magnetization(default_value, accepted_values)
    elif magnetization.upper() == 'FM+AFM':
        default_value['Scheme'] = 'FM+AFM'
        max_number = input('Max number of antiferromagnetic structures\n')
        if is_pos_int(max_number) == True:
            default_value['Max_antiferro'] = int(max_number)
            return default_value
        else:
            print('Not valid positive integer; try again')
            validate_magnetization(default_value, accepted_values)
    else:
        print('Not a valid option; try again')
        validate_magnetization(default_value, accepted_values)


def validate_calculation_type(default_value, accepted_values):
    print('Calculation_Type; default is %s' % default_value)
    calculation = input('Type (%s' % accepted_values + ')\n')
    if calculation.lower() == 'bulk':
        default_value['Type'] = 'bulk'
        return default_value
    elif calculation.lower() == 'defect':
        default_value['Type'] = 'defect'
        element = input('Defect element abbreviation; i.e. H, O, C, etc.\n')
        try:
            Element(element)
            default_value['Defect'] = element
            return default_value
        except ValueError:
            print('%s not a valid element' % element)
            return validate_calculation_type(default_value, accepted_values)
    else:
        print('Not a valid option; try again')
        validate_calculation_type(default_value, accepted_values)


def validate_mpids(default_values):
    print('Add/remove MPIDs; existing mp-ids are %s' % default_values)
    add_or_remove = input('Add or remove mpids?\n')
    if add_or_remove.lower() == 'add':
        mpid = input('Name of mpid to add\n')
        if is_mpid(mpid) == True:
            with MPRester(MP_api_key) as m:
                structure = m.get_structures(mpid, final=True)[0]
                formula = structure.formula
                default_values[mpid] = formula
        else:
            print('Invalid mpid; try again')
        validate_mpids(default_values)
    elif add_or_remove.lower() == 'remove':
        mpid = input('Name of mpid to remove\n')
        if is_mpid(mpid) == True:
            default_values.pop(mpid, None)
        else:
            print('Invalid mpid; try again')
        validate_mpids(default_values)
    elif add_or_remove.lower() in exit_commands:
        default_values
        return default_values
    else:
        print('Not a valid option; try again')
        validate_mpids(default_values)


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o', '--outfile_name', help='Output .yml file path', type=str, required=True)
    parser.add_argument(
        '-c', '--copyfile_name', help='Copied .yml file path', type=str, default=None)
    parser.add_argument(
        '-e', '--edit_fields', help='Fields to edit', nargs='+', type=str,
        choices=['INCAR_Tags', 'Relaxation_Set', 'MPIDs', 'Formulas',
                 'Magnetization_Scheme', 'Convergence_Scheme', 'Calculation_Type',
                 'Max_Submissions'], default=None)
    #argcomplete.autocomplete(parser)
    args = parser.parse_args()

    return args


def get_starting_dictionary(copy_path):
    if copy_path is not None:
        if os.path.exists(copy_path):
            try:
                with open(copy_path, 'r') as copyfile:
                    copied_dictionary = yaml.safe_load(copyfile)
                    return copied_dictionary
            except ScannerError:
                print('Invalid .yml path; try again or use default dictionary')
                sys.exit(1)
        else:
            print('Path to %s does not exist' % copy_path)
            sys.exit(1)
    else:
        return default_dictionary


def yml_inputs(args):
    yaml_dict = get_starting_dictionary(args.copyfile_name)
    edit_fields = args.edit_fields

    if edit_fields is None:
        print('-e (edit_fields) not specified; writing .yml file')
        return yaml_dict

    else:
        # not sure why == is needed to update dictionaries
        for field in args.edit_fields:
            if field == 'INCAR_Tags':
                yaml_dict[field] == validate_incar_tags(yaml_dict[field])

            if field == 'Relaxation_Set':
                yaml_dict[field] = validate_general_string(field,
                    yaml_dict[field], allowed_relaxation_sets,
                    'Materials Project Relax Set (')

            if field == 'Magnetization_Scheme':
                yaml_dict[field] == validate_magnetization(
                    yaml_dict[field], allowed_magnetism)

            if field == 'Max_Submissions':
                yaml_dict[field] = validate_general_positive_integer(
                    field, yaml_dict[field], 'Number of Workflow Submissions')

            if field == 'Convergence_Scheme':
                yaml_dict[field] = validate_general_string(field,
                    yaml_dict[field], allowed_convergence_schemes,
                    'Convergence Scheme (')

            if field == 'Calculation_Type':
                yaml_dict[field] == validate_calculation_type(yaml_dict[field],
                    allowed_calculation_types)

            if field == 'MPIDs':
                yaml_dict[field] == validate_mpids(yaml_dict[field])

    return yaml_dict


def write_yaml(write_dict, path):
    # writes a dictionary to the path as a .yml file
    abs_path = os.path.abspath(path)
    parent = Path(abs_path).parent
    if '.yml' in path and os.path.exists(parent):
        with open(abs_path, "w") as outfile:
            yaml.safe_dump(write_dict, outfile, default_flow_style=False)
    else:
        new_path = input('Need write path that exists; file should have .yml file extension'/n)
        write_yaml(write_dict, new_path)



def main():
    args = argument_parser()
    yml_dict = yml_inputs(args)
    write_yaml(yml_dict, args.outfile_name)
    print('done\n')

if __name__ == "__main__":
    main()
