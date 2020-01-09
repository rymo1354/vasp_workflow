#!/usr/bin/env python

import yaml
import os
import sys
from pymatgen.ext.matproj import MPRester
import json
import copy
from configuration.config import MP_api_key
from distutils.util import strtobool
from yaml.scanner import ScannerError
from pymatgen.core.periodic_table import Element
from pymatgen.io.vasp.inputs import Poscar
from pathlib import Path


###############################################################################
''' ONLY CHANGE exit_commands, default_dictionary OR allowed_incar_steps '''

exit_commands = ['escape', 'quit', 'stop', 'exit', 'no mas']

default_dictionary = dict(INCAR_Tags={'step0': {'AUTO_TIME': 24, 'NPAR': 1}},
                          Relaxation_Set='MPRelaxSet',
                          Magnetization_Scheme={'Scheme': 'FM'},
                          Max_Submissions=1,
                          Calculation_Type={'Type': 'bulk'},
                          MPIDs={},
                          PATHs={})

allowed_vtst_tools_tags = {"IOPT": [0, 1, 2, 3, 4, 7]}
# not included in generic Pymatgen VASP inputs

allowed_relaxation_sets = ['MPRelaxSet', 'MITRelaxSet', 'MPMetalRelaxSet',
                           'MPHSERelaxSet', 'MPStaticSet']

allowed_magnetism = ['preserve', 'FM', 'AFM', 'FM+AFM']

allowed_calculation_types = ['bulk', 'defect']

allowed_incar_steps = ['step0', 'step1', 'step2', 'step3', 'step4', 'step5',
                       'step6', 'step7', 'step8', 'step9', 'step10']
# maximum 11 steps by default; can add more steps if necessary (unlikely)

###############################################################################


class WriteYaml():

    def __init__(self, copy_path):
        self.exit_commands = exit_commands
        self.allowed_relaxation_sets = allowed_relaxation_sets
        self.allowed_magnetism = allowed_magnetism
        self.allowed_vtst_tools_tags = allowed_vtst_tools_tags
        self.allowed_calculation_types = allowed_calculation_types
        self.allowed_incar_steps = allowed_incar_steps

        with open("incar_parameters.json") as incar_params:
            self.incar_params = json.loads(incar_params.read())

        if copy_path is not None:
            if os.path.exists(copy_path):
                try:
                    with open(copy_path, 'r') as copyfile:
                        copied_dictionary = yaml.safe_load(copyfile)
                        self.default_dictionary = copied_dictionary
                except ScannerError:
                    print('Invalid .yml; try again or use default dictionary')
                    sys.exit(1)
            else:
                print('Path to %s does not exist' % copy_path)
                sys.exit(1)
        else:
            self.default_dictionary = default_dictionary

        self.new_dictionary = copy.deepcopy(self.default_dictionary)

    def is_float(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    def is_pos_or_zero_float(self, string):
        try:
            float(string)
            if float(string) >= 0:
                return True
            else:
                return False
        except ValueError:
            return False

    def is_pos_int(self, string):
        try:
            int(string)
            if int(string) > 0:
                return True
            else:
                return False
        except ValueError:
            return False

    def is_mpid(self, mpid):
        with MPRester(MP_api_key) as m:
            try:
                structure = m.get_structures(mpid, final=True)[0]
                return True
            except BaseException:
                print('%s is not a valid mp-id' % mpid)
                return False

    def is_vasp_readable_structure(self, path):
        try:
            checked_path = Path(path)
            Poscar.from_file(str(checked_path))
            return True
        except FileNotFoundError:
            print('%s path does not exist' % path)
            return False
        except UnicodeDecodeError:
            print('%s likely not a valid CONTCAR or POSCAR' % path)
            return False
        except OSError:
            print('%s likely not a valid CONTCAR or POSCAR' % path)
            return False

    def validate_general_positive_integer(self, tag, prompt_statement):
        print('%s; existing value is %s' % (tag, self.new_dictionary[tag]))
        integer_value = input(
            prompt_statement +
            ': should be a positive integer\n')
        if self.is_pos_int(integer_value) is True:
            self.new_dictionary[tag] = int(integer_value)
            print('New value "%s" updated for %s' % (integer_value, tag))
        elif integer_value.lower() in self.exit_commands:
            print(
                'Exiting: existing value "%s" will be used' %
                self.new_dictionary[tag])
            return
        else:
            print(
                '"%s" not an accepted value; try again or exit' %
                integer_value)
            self.validate_general_positive_integer(tag, prompt_statement)

    def validate_general_string(self, tag, accepted_values, prompt_statement):
        print('%s; existing value is %s' % (tag, self.new_dictionary[tag]))
        string_value = input(prompt_statement + str(accepted_values) + ')\n')
        if string_value in accepted_values:
            self.new_dictionary[tag] = str(string_value)
            print('New value "%s" updated for %s' % (string_value, tag))
        elif string_value.lower() in self.exit_commands:
            print(
                'Exiting: existing value "%s" will be used' %
                self.new_dictionary[tag])
            return
        else:
            print('"%s" not an accepted value; try again' % string_value)
            self.validate_general_string(
                tag, accepted_values, prompt_statement)

    def check_valid_LDAU_value(self, tag):
        try:
            print('Add %s tag; existing tags are %s' %
                  (tag, self.new_dictionary['INCAR_Tags'][tag]))
            tag_dict = self.new_dictionary['INCAR_Tags'][tag].copy()
        except KeyError:
            print('Add %s tag; no existing tags' % tag)
            tag_dict = {}
        element = input('%s element; i.e. Gd, Ce, La, etc.\n' % tag)
        try:
            Element(element)
            value = input('%s value for element %s\n' % (tag, element))
            if self.is_pos_or_zero_float(value):
                tag_dict[element] = float(value)
                return tag_dict
            else:
                print('%s not a positive or zero value' % value)
                self.check_valid_LDAU_value(tag)
        except ValueError:
            print('%s not a valid element' % element)
            self.check_valid_LDAU_value(tag)

    def check_valid_incar_value(self, dictionary, tag, value):
        if type(dictionary[tag]).__name__ == "str":
            if dictionary[tag] == 'int':
                try:
                    return int(value)
                except ValueError:
                    print(
                        '%s requires integer; %s not an integer\n' %
                        (tag, value))
                    return 'bad_value'
            elif dictionary[tag] == 'float':
                try:
                    return float(value)
                except ValueError:
                    print('%s requires float; %s not a float\n' % (tag, value))
                    return 'bad_value'
            elif dictionary[tag] == 'bool':
                try:
                    return bool(strtobool(value))
                except ValueError:
                    print('%s requires bool; %s not a bool\n' % (tag, value))
                    return 'bad_value'
                except AttributeError:
                    print('%s requires bool; %s not a bool\n' % (tag, value))
                    return 'bad_value'
            elif dictionary[tag] == 'list':
                print(
                    '\n*** WARNING *** List required for this tag; inputs '
                    'may not be appropriate. Consult VASP documentation\n')
                print(
                    'List inputs. Ex. [1, 2, 3] should be input as 1 2 3\n')
                value_list = list(value.split(' '))
                try:
                    value_list = list(map(float, value_list))
                except ValueError:
                    pass
                try:
                    return list(value_list)
                except BaseException:
                    print('%s requires list; %s not a list\n' % (tag, value))
                    return 'bad_value'
        elif type(dictionary[tag]).__name__ == "list":
            try:
                value = int(value)
            except ValueError:
                pass
            if value not in dictionary[tag]:
                return 'bad_value'
            else:
                return value
        else:
            print('%s input type not supported' % tag)

    def add_or_edit_convergence_step(self):
        print(
            'Add/edit convergence step; existing steps are %s' %
            self.new_dictionary['INCAR_Tags'])
        print(
            'Can also exit with one of the allowed exit commands %s' %
            self.exit_commands)
        add_or_edit = input('Add or edit steps?\n')
        if add_or_edit in self.exit_commands:
            print(
                'Exiting: existing INCAR values %s will be used' %
                self.new_dictionary['INCAR_Tags'])
            return
        elif add_or_edit.lower() == 'edit':
            step_to_edit = input(
                'Step to edit; existing steps are %s\n' % str(
                    list(
                        self.new_dictionary['INCAR_Tags'].keys())))
            if step_to_edit in list(self.new_dictionary['INCAR_Tags'].keys()):
                action = input(
                    'Change %s; allowed inputs are "rename", '
                    '"modify" and "delete"\n' % step_to_edit)
                if action.lower() == 'rename':
                    rename_step = input('Rename %s to what?\n' % step_to_edit)
                    if rename_step in self.allowed_incar_steps and rename_step not in list(self.new_dictionary['INCAR_Tags'].keys()):
                        self.new_dictionary['INCAR_Tags'][rename_step] = self.new_dictionary['INCAR_Tags'].pop(
                            step_to_edit)
                    else:
                        if rename_step not in self.allowed_incar_steps:
                            print(
                                '%s not an allowed step name. Allowed names are %s' %
                                (rename_step, self.allowed_incar_steps))
                        if rename_step in list(
                                self.new_dictionary['INCAR_Tags'].keys()):
                            print(
                                '%s already a step name; choose a different step name for this step first' %
                                rename_step)
                elif action.lower() == 'modify':
                    self.validate_incar_tags(step_to_edit)
                elif action.lower() == 'delete':
                    self.new_dictionary['INCAR_Tags'].pop(step_to_edit)
                else:
                    print('%s not a valid action; try again\n')
                self.add_or_edit_convergence_step()
            else:
                print('%s not a current step; try again\n' % step_to_edit)
                self.add_or_edit_convergence_step()
        elif add_or_edit.lower() == 'add':
            step_to_add = input('Step to add; existing steps are %s\n' % str(
                list(self.new_dictionary['INCAR_Tags'].keys())))
            if step_to_add in self.allowed_incar_steps and step_to_add not in list(
                    self.new_dictionary['INCAR_Tags'].keys()):
                self.new_dictionary['INCAR_Tags'][step_to_add] = {}
                self.validate_incar_tags(step_to_add)
            else:
                if step_to_add not in self.allowed_incar_steps:
                    print(
                        '%s not an allowed step name. Allowed names are %s\n' %
                        (step_to_add, self.allowed_incar_steps))
                if step_to_add in list(
                        self.new_dictionary['INCAR_Tags'].keys()):
                    print(
                        '%s already a step name; to change it, choose to edit a convergence step\n' %
                        step_to_add)
            self.add_or_edit_convergence_step()
        else:
            print('Not a valid option; try again\n')
            self.add_or_edit_convergence_step()

    def validate_incar_tags(self, step):
        print('Add/remove INCAR_Tags for %s; existing tags are %s' %
              (step, self.new_dictionary['INCAR_Tags'][step]))
        add_or_remove = input('Add or remove tags?\n')
        if add_or_remove.lower() == 'add':
            tag = input('Name of tag to add\n')
            if tag == 'AUTO_TIME':
                value = input('Value of tag to add\n')
                if self.is_pos_int(value):
                    self.new_dictionary['INCAR_Tags'][step][tag] = int(value)
                else:
                    print('%s not a valid input for AUTO_TIME' % value)
            elif tag in ['LDAUU', 'LDAUJ', 'LDAUL']:
                value_dict = self.check_valid_LDAU_value(tag)
                self.new_dictionary['INCAR_Tags'][step][tag] = value_dict
            elif tag in self.allowed_vtst_tools_tags.keys():
                value = input('Value of tag to add\n')
                check_value = self.check_valid_incar_value(
                    self.allowed_vtst_tools_tags, tag, value)
                if check_value != 'bad_value':
                    self.new_dictionary['INCAR_Tags'][step][tag] = check_value
                else:
                    print('Invalid value %s for INCAR tag %s' % (value, tag))
            elif tag not in self.incar_params.keys():
                print('%s not a valid INCAR tag; try again' % tag)
            else:
                value = input('Value of tag to add\n')
                check_value = self.check_valid_incar_value(
                    self.incar_params, tag, value)
                if check_value != 'bad_value':
                    self.new_dictionary['INCAR_Tags'][step][tag] = check_value
                else:
                    print('Invalid value %s for INCAR tag %s' % (value, tag))
            self.validate_incar_tags(step)
        elif add_or_remove.lower() == 'remove':
            tag = input('Name of tag to remove\n')
            self.new_dictionary['INCAR_Tags'][step].pop(tag, None)
            self.validate_incar_tags(step)
        elif add_or_remove.lower() in self.exit_commands:
            print('Exiting: existing tags will be used')
            return
        else:
            print('Not a valid option; try again')
            self.validate_incar_tags(step)

    def validate_magnetization(self):
        print('Magnetization_Scheme; existing is %s' %
              self.new_dictionary['Magnetization_Scheme'])
        magnetization = input(
            'Input new scheme (%s' %
            self.allowed_magnetism + ')\n')
        if magnetization.upper() == 'FM':
            self.new_dictionary['Magnetization_Scheme']['Scheme'] = 'FM'
            try:
                del self.new_dictionary['Magnetization_Scheme']['Max_antiferro']
            except KeyError:
                pass
        elif magnetization.lower() == 'preserve':
            self.new_dictionary['Magnetization_Scheme']['Scheme'] = 'preserve'
            try:
                del self.new_dictionary['Magnetization_Scheme']['Max_antiferro']
            except KeyError:
                pass
        elif magnetization.upper() == 'AFM':
            self.new_dictionary['Magnetization_Scheme']['Scheme'] = 'AFM'
            max_number = input('Max number of antiferromagnetic structures\n')
            if self.is_pos_int(max_number):
                self.new_dictionary['Magnetization_Scheme']['Max_antiferro'] = int(
                    max_number)
            else:
                print('Not valid positive integer; try again')
                self.validate_magnetization()
        elif magnetization.upper() == 'FM+AFM':
            self.new_dictionary['Magnetization_Scheme']['Scheme'] = 'FM+AFM'
            max_number = input('Max number of antiferromagnetic structures\n')
            if self.is_pos_int(max_number):
                self.new_dictionary['Magnetization_Scheme']['Max_antiferro'] = int(
                    max_number)
            else:
                print('Not valid positive integer; try again')
                self.validate_magnetization()
        else:
            print('Not a valid option; try again')
            self.validate_magnetization()

    def validate_calculation_type(self):
        print('Calculation_Type; existing is %s' %
              self.new_dictionary['Calculation_Type'])
        calculation = input(
            'Type (%s' %
            self.allowed_calculation_types +
            ')\n')
        if calculation.lower() == 'bulk':
            self.new_dictionary['Calculation_Type']['Type'] = 'bulk'
            try:
                del self.new_dictionary['Calculation_Type']['Defect']
            except KeyError:
                pass
        elif calculation.lower() == 'defect':
            self.new_dictionary['Calculation_Type']['Type'] = 'defect'
            element = input(
                'Defect element abbreviation; i.e. H, O, C, etc.\n')
            try:
                Element(element)
                self.new_dictionary['Calculation_Type']['Defect'] = element
            except ValueError:
                print('%s not a valid element' % element)
                self.validate_calculation_type()
        else:
            print('Not a valid option; try again')
            self.validate_calculation_type()

    def validate_mpids(self):
        # add in manual vs automatic read in from .yml file
        print(
            'Add/remove MPIDs; existing mp-ids are %s' %
            self.new_dictionary['MPIDs'])
        add_or_remove = input('Add or remove mpids?\n')
        if add_or_remove.lower() == 'add':
            mpid = input('Name of mpid to add\n')
            if self.is_mpid(mpid):
                with MPRester(MP_api_key) as m:
                    structure = m.get_structures(mpid, final=True)[0]
                    formula = structure.formula
                    self.new_dictionary['MPIDs'][mpid] = formula
            else:
                pass
            self.validate_mpids()
        elif add_or_remove.lower() == 'remove':
            mpid = input('mpid to remove\n')
            if self.is_mpid(mpid):
                try:
                    del self.new_dictionary['MPIDs'][mpid]
                except KeyError:
                    print('%s not in the list of current mpids' % mpid)
                    pass
            else:
                print('Invalid mpid; try again')
            self.validate_mpids()
        elif add_or_remove.lower() in self.exit_commands:
            print('Exiting: existing tags will be used')
            return
        else:
            print('Not a valid option; try again')
            self.validate_mpids()

    def validate_paths(self):
        # add manual vs automatic read in from .yml file
        print(
            'Add/remove structure PATHs; existing paths are %s' %
            self.new_dictionary['PATHs'])
        add_or_remove = input('Add or remove paths?\n')
        if add_or_remove.lower() == 'add':
            path = input('Name of path to add\n')
            if self.is_vasp_readable_structure(path):
                poscar = Poscar.from_file(path)
                formula = poscar.structure.formula
                self.new_dictionary['PATHs'][path] = formula
            else:
                pass
            self.validate_paths()
        elif add_or_remove.lower() == 'remove':
            path = input('path to remove\n')
            if self.is_vasp_readable_structure(path):
                try:
                    del self.new_dictionary['PATHs'][path]
                except KeyError:
                    print('%s not in the list of current paths' % path)
                    pass
            else:
                print('Invalid mpid; try again')
            self.validate_paths()
        elif add_or_remove.lower() in self.exit_commands:
            print('Exiting: existing tags will be used')
            return
        else:
            print('Not a valid option; try again')
            self.validate_paths()
