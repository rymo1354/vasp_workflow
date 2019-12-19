# vasp_workflow
`vasp_workflow` is a workflow that can be used to rapidly generate and submit
[VASP](https://www.vasp.at/) jobs to SLURM supercomputing clusters. Currently
supported clusters include CU Boulder's [Summit](https://www.colorado.edu/rc/resources/summit)
and the National Renewable Energy Laboratory's (NREL) [Eagle](https://www.nrel.gov/hpc/eagle-system.html).

## Overview

### Environmental Requirements
1. Clone the repository with the following command:
`git clone https://github.com/rymo1354/vasp_workflow.git`

2. Append the full path of the `vasp_workflow` directory to the $PATH and $PYTHONPATH variables
within your `.bash_profile` or `.bashrc`. Full path can be found by navigating
to the `vasp_workflow` directory and using the `pwd` command.

3. Load the `vasp_workflow` conda environment from `/home/rmorelock/.conda-envs/vasp_workflow`. On Eagle, this is performed executing `module load conda` to load Eagle's default conda environment. You can then run `conda activate /home/rmorelock/.conda-envs/vasp_workflow.` to load the vasp_workflow environment. (Note: you may need to run `conda init bash` to make your default shell bash, thereby enabling the `conda activate` command.) You can also add `/home/rmorelock/.conda-envs/vasp_workflow` to your path variable 
for more rapid loading.

The `vasp_workflow` environment should have the following packages (among others):
* pymatgen
* pyyaml
* pycodestyle

You can check for these packages using the `conda list` command. You can also create your own environment and install these packages
with the following commands:
* `conda install -c conda-forge pymatgen`
* `conda install -c anaconda pyyaml`
* `conda install -c conda-forge pycodestyle`

4. Navigate to the [configuration](https://github.com/rymo1354/vasp_workflow/tree/master/configuration) folder. In `config.py`, set the `MP_api_key` variable to your Material's Project API key.

### Generating a .yml runfile
