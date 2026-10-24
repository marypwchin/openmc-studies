# OpenMC Workbench

This workbench explores OpenMC from the perspective of an experienced Monte Carlo radiation-transport physicist. It emphasizes hands-on investigation, computational workflows, and practical understanding rather than formal research studies. The notebooks combine explanations, Python examples, and comparisons between the OpenMC API and the underlying data files.

This is an evolving workbench.

## Nuclear data

Start with the setup notebook if you want to reproduce the examples locally, or go directly to the exploration notebook to read the analysis.

| Workbench | What it covers |
| --- | --- |
| [Set up OpenMC nuclear data](0_nuclear_data/0_0_setting_up_nuclear_data.ipynb) | Install nuclear-data libraries, windowed multipole data, and depletion chains; check the resulting file layout. |
| [Explore ENDF/B-VIII.1](0_nuclear_data/0_1_exploring_endf-b8.1.ipynb) | Examine the cross-section index and HDF5 files, compare access through Python and OpenMC, and explore materials and reaction availability. |

For text-only setup, the parallel [Python script](0_nuclear_data/0_0_setting_up_nuclear_data.py) serves the same purpose as [0_0_setting_up_nuclear_data.ipynb](0_nuclear_data/0_0_setting_up_nuclear_data.ipynb).

## Reproduce the notebooks

Reading the notebooks does not require a local nuclear-data installation. To run the notebooks, use a Python environment with OpenMC and the dependencies listed in the notebooks, and follow the setup instructions first.

The notebooks and the setup script use [shared configuration](openmc_workbench_config.py) to locate nuclear data under `~/data`. From your local repository root, install that module into the Python environment used by your Jupyter kernel:

```sh
python -m pip install -e .
```

If your data lives elsewhere, edit `DATA_ROOT` in the shared configuration module and restart the kernel. Review the setup notebook's disk-space requirements and preview the installation with `APPLY = False` before enabling downloads or conversion.

## Source and contributions

The notebooks and supporting code are maintained in the [OpenMC Workbench repository](https://github.com/marypwchin/openmc-workbench). For contributor setup, validation checks, and CI workflows, see the [repository automation guide](docs/automation.md).
