# vasp_workflow
`vasp_workflow` is a workflow that can be used to rapidly generate and submit
[VASP](https://www.vasp.at/) jobs to SLURM supercomputing clusters. Currently
supported clusters include CU Boulder's [Summit](https://www.colorado.edu/rc/resources/summit)
and the National Renewable Energy Laboratory's (NREL) [Eagle](https://www.nrel.gov/hpc/eagle-system.html).

## Overview

### Environmental Requirements
1. Ensure the following packages are in your environment:
* pymatgen
* numpy
* pyyaml
* pycodestyle

2. Clone the repository with the following command:
`git clone https://github.com/rymo1354/vasp_workflow.git`

3. Append the full path of the `vasp_workflow` directory to the $PATH and $PYTHONPATH variables
within your `.bash_profile` or `.bashrc`. Full path can be found by navigating
to the `vasp workflow` directory and using the `pwd` command.

4. Navigate to the [configuration](https://github.com/rymo1354/vasp_workflow/tree/master/configuration) folder. In `config.py`, set the `MP_api_key` variable to your
Material's Project API key.

### Generating a .yml runfile
