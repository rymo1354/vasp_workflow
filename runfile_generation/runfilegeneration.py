#!/usr/bin/env python

import yaml
import os
import sys
import random
import numpy as np
import copy
from pymatgen.ext.matproj import MPRester
from configuration.config import MP_api_key
from pymatgen.io.vasp import Poscar
from pymatgen.analysis.magnetism.analyzer import \
    CollinearMagneticStructureAnalyzer
from pymatgen.analysis.local_env import CrystalNN


class LoadYaml:

    def __init__(self, load_path):
        if os.path.exists(load_path):
            try:
                with open(load_path, 'r') as loadfile:
                    loaded_dictionary = yaml.safe_load(loadfile)
                    self.loaded_dictionary = loaded_dictionary
            except ScannerError:
                print('Invalid .yml; try again or use default dictionary')
                sys.exit(1)
        else:
            print('Path to %s does not exist' % load_path)
            sys.exit(1)

        try:
            self.mpids = self.loaded_dictionary['MPIDs']
        except KeyError:
            print('MPIDs not in %s; invalid input file' % load_path)
            sys.exit(1)
        try:
            self.paths = self.loaded_dictionary['PATHs']
        except KeyError:
            print('PATHs not in %s; invalid input file' % load_path)
            sys.exit(1)
        try:
            self.calculation_type = self.loaded_dictionary['Calculation_Type']
        except KeyError:
            print('Calculation_Type not in %s; invalid input file' % load_path)
            sys.exit(1)
        try:
            self.relaxation_set = self.loaded_dictionary['Relaxation_Set']
        except KeyError:
            print('Relaxation_Set not in %s; invalid input file' % load_path)
            sys.exit(1)
        try:
            self.magnetization_scheme = self.loaded_dictionary['Magnetization_Scheme']
        except BaseException:
            print(
                'Magnetization_Scheme not in %s; invalid input file' %
                load_path)
            sys.exit(1)
        try:
            self.incar_tags = self.loaded_dictionary['INCAR_Tags']
        except BaseException:
            print('INCAR_Tags not in %s; invalid input file' % load_path)
            sys.exit(1)
        try:
            self.max_submissions = self.loaded_dictionary['Max_Submissions']
        except KeyError:
            print('Max_Submissions not in %s; invalid input file' % load_path)
            sys.exit(1)


class PmgStructureObjects:
    def __init__(self, mpids, paths):
        self.mpids = mpids
        self.paths = paths
        self.structures_dict = {}
        self.structure_number = 1

        self.mpid_structures()
        self.path_structures()

    def mpid_structures(self):
        for mpid in self.mpids:
            with MPRester(MP_api_key) as m:
                try:
                    structure = m.get_structures(mpid, final=True)[0]
                    structure_key = 'Structure ' + str(self.structure_number) + ' (' + str(structure.formula) + ')'
                    self.structures_dict[structure_key] = structure
                    self.structure_number += 1
                except BaseException:
                    print('%s is not a valid mp-id' % mpid)
                    continue

    def path_structures(self):
        for path in self.paths:
            try:
                poscar = Poscar.from_file(path)
                structure = poscar.structure
                structure_key = 'Structure ' + str(self.structure_number) + ' (' + str(structure.formula) + ')'
                self.structures_dict[structure_key] = structure
                self.structure_number += 1
            except FileNotFoundError:
                print('%s path does not exist' % path)
                continue
            except UnicodeDecodeError:
                print('%s likely not a valid CONTCAR or POSCAR' % path)
                continue
            except OSError:
                print('%s likely not a valid CONTCAR or POSCAR' % path)

class Magnetism:
    def __init__(self, structures_dict, magnetization_dict, num_tries=100):
        self.structures_dict = structures_dict
        self.magnetization_dict = magnetization_dict
        self.magnetized_structures_dict = {}
        self.num_tries = num_tries
        self.structure_number = 1

        self.get_magnetic_structures()

    def random_antiferromagnetic(self, ferro_magmom, used_enumerations, num_afm, num_tries):
        # checks if all unique iterations complete OR too many tries achieved
        if num_afm == 0 or num_tries == 0:
            return used_enumerations
        # checks if proposed enumeration is the ferromagnetic enumeration
        dont_use = False
        antiferro_mag_scheme = random.choices([-1, 1], k=len(ferro_magmom))
        antiferro_mag = np.multiply(antiferro_mag_scheme, ferro_magmom)
        if np.array_equal(antiferro_mag, np.array(ferro_magmom)):
            dont_use = True
        # checks if proposed scheme is an already existing antiferromagnetic scheme
        for used_enumeration in used_enumerations:
            if np.array_equal(antiferro_mag, used_enumeration):
                dont_use = True
        # if dont_use = True: tries again with num_tries - 1
        if dont_use is True:
            return self.random_antiferromagnetic(ferro_magmom, used_enumerations,
                                            num_afm, num_tries - 1)
        # else: appends to used_enumerations: tries again with num_rand - 1
        else:
            used_enumerations.append(antiferro_mag)
            return self.random_antiferromagnetic(ferro_magmom, used_enumerations,
                                            num_afm - 1, num_tries)

    def afm_structures(self, structure_key, ferro_structure):
        if set(ferro_structure.site_properties["magmom"]) == set([0]):
            print("%s is not magnetic; ferromagnetic structure to be run"
                    % str(ferro_structure.formula))
            self.magnetized_structures_dict[structure_key]['FM'] = ferro_structure
        else:
            random_enumerations = self.random_antiferromagnetic(
                ferro_structure.site_properties["magmom"], [],
                self.magnetization_dict['Max_antiferro'], self.num_tries)
            afm_enum_number = 1
            for enumeration in random_enumerations:
                antiferro_structure = ferro_structure.copy()
                for magmom_idx in range(len(antiferro_structure.site_properties["magmom"])):
                    antiferro_structure.replace(magmom_idx, antiferro_structure.species[magmom_idx], properties={'magmom': enumeration[magmom_idx] + 0})
                    afm_key = 'AFM' + str(afm_enum_number)
                self.magnetized_structures_dict[structure_key][afm_key] = antiferro_structure
                afm_enum_number += 1

    def get_magnetic_structures(self):
        # assigns magnetism to structures. returns the magnetic get_structures
        # num_rand and num_tries only used for random antiferromagnetic assignment
        for structure in self.structures_dict.values():
            collinear_object = CollinearMagneticStructureAnalyzer(
                structure, overwrite_magmom_mode="replace_all")
            ferro_structure = collinear_object.get_ferromagnetic_structure()
            structure_key = 'Structure ' + str(self.structure_number) + ' (' + str(structure.formula) + ')'
            self.magnetized_structures_dict[structure_key] = {}

            if self.magnetization_dict['Scheme'] == 'preserve':
                self.magnetized_structures_dict[structure_key]['preserve'] = structure

            elif self.magnetization_dict['Scheme'] == 'FM':
                self.magnetized_structures_dict[structure_key]['FM'] = ferro_structure

            elif self.magnetization_dict['Scheme'] == 'AFM':
                self.afm_structures(structure_key, ferro_structure)

            elif self.magnetization_dict['Scheme'] == 'FM+AFM':
                self.magnetized_structures_dict[structure_key]['FM'] = ferro_structure
                self.afm_structures(structure_key, ferro_structure)

            else:
                print('Magnetization Scheme %s not recognized; fatal error' % self.magnetization_dict['Scheme'])
                sys.exit(1)

            self.structure_number += 1


class CalculationType:
    def __init__(self, magnetic_structures_dict, calculation_dict):
        self.magnetic_structures_dict = magnetic_structures_dict
        self.calculation_dict = calculation_dict
        self.calculation_structures_dict = copy.deepcopy(self.magnetic_structures_dict)

        self.alter_structures()

    def structure_rescaler(self, structure):
        if len(structure.species) <= 2:
            structure.make_supercell([4, 4, 4])
        elif len(structure.species) <= 4:
            structure.make_supercell([3, 3, 3])
        elif len(structure.species) <= 7:
            structure.make_supercell([3, 3, 2])
        elif len(structure.species) <= 10:
            structure.make_supercell([3, 2, 2])
        elif len(structure.species) <= 16:
            structure.make_supercell([2, 2, 2])
        elif len(structure.species) <= 32:
            structure.make_supercell([2, 2, 1])
        elif len(structure.species) <= 64:
            structure.make_supercell([2, 1, 1])
        else:
            pass
        return structure

    def get_unique_coordination_environment_indices(self, structure, tolerance=0):
        structure.add_oxidation_state_by_guess() #adds oxidation guess to a structure
        unique_species = np.unique(structure.species) #returns the unique species in the structure
        coord_envs = np.zeros((len(structure.species), len(unique_species))) #builds array to house coordination envs

        unique_sites = []
        site_counter = np.ones(len(unique_species))
        sites_dict = {} #contains all the equivalent substitution sites in arrays
        sub_site_dict = {} #contains only the first substitution site in the sites_dict array

        cnn = CrystalNN(weighted_cn=True)
        for i in range(len(structure.sites)):
            cnn_structure = cnn.get_nn_info(structure, i)
            for j in range(len(cnn_structure)):
                site = cnn_structure[j]['site']
                for specie in unique_species:
                    if site.specie == specie:
                        el_ind = int(np.where(unique_species == specie)[0])
                        coord_envs[i][el_ind] += cnn_structure[j]['weight']

        for i in range(len(coord_envs)):
            duplicate_sites = []
            for j in range(len(coord_envs)):
                if np.linalg.norm(coord_envs[i]-coord_envs[j]) <= env_tolerance:
                    duplicate_sites.append(i)
                    duplicate_sites.append(j)
            one_unique = list(np.unique(duplicate_sites))
            if one_unique not in [x for x in unique_sites]:
                unique_sites.append(one_unique)

        for i in range(len(unique_sites)):
            species = []
            for j in range(len(unique_sites[i])):
                species.append(structure.species[unique_sites[i][j]])

            if len(np.unique(species)) == 1: #only a single element in the group of coordination environments
                specie = np.unique(species)[0]
                site_index = np.where(unique_species == specie)
                key = '%s_site_%s' % (str(specie.element), int(site_counter[site_index]))
                sites_dict[key] = (specie.element, unique_sites[i])
                sub_site_dict[key] = (specie.element, unique_sites[i][0]) #pick the first equivalent site
                site_counter[site_index] += 1
            else:
                raise Exception('Coordination environments similar w/in tolerance, but species %s are not' % np.unique(species))
            # should be a very rare exception when weighted_cn=True in CrystalNN, unless threshold is high

        return sub_site_dict

    def alter_structures(self):
        if self.calculation_dict['Type'] == 'bulk':
            pass
        elif self.calculation_dict['Type'] == 'defect':
            # need to perform cell rescaling
            defect_element = self.calculation_type['Defect']
            for structure in self.calculation_structures_dict.keys():
                for magnetism in self.calculation_structures_dict[structure].keys():
                    structure = self.calculation_structures_dict[structure][magnetism]
                    rescaled_structure = self.structure_rescaler(structure)
            pass
