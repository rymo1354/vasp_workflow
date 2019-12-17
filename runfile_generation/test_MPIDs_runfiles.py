#!/usr/bin/env python

import unittest
import sys
import os
import io
import subprocess
import yaml
import MPIDs_runfiles


class TestMPIDs_runfiles(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # create example_yaml.yml if it dne; read in dict from this
        workflow_path = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        yaml_gen_path = os.path.join(workflow_path, 'yaml_generation')
        MPIDs_yaml_path = os.path.join(yaml_gen_path, 'MPIDs_yaml.py')
        example_yaml_path = os.path.join(yaml_gen_path, 'example_yaml.yml')

        args = ['python', MPIDs_yaml_path, '-a', 'mp-500', '-o',
                example_yaml_path]
        subprocess.call(args, shell=True)
        with open(example_yaml_path, 'r') as testfile:
            self.test_yaml = yaml.safe_load(testfile)
            self.test_yaml_path = example_yaml_path

    def test_load_yaml(self):
        # assert that the yaml file created is properly loaded
        self.assertEqual(
            self.test_yaml,
            MPIDs_runfiles.load_yaml(self.test_yaml_path))

    def test_get_MP_structures(self):
        # make sure that structure objects are correctly loaded
        structures = MPIDs_runfiles.get_MP_structures(self.test_yaml['MPIDs'])
        self.assertEqual(structures[0].formula, self.test_yaml['Formulas'][0])

    @classmethod
    def tearDownClass(self):
        # Removes the temporary example_yaml.yml file used for testing
        args = ['rm', self.test_yaml_path]
        subprocess.call(args, shell=True)


if __name__ == "__main__":
    unittest.main()
