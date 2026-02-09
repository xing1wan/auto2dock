# Automated Molecular Docking & Analysis Pipeline
This repository contains a high-throughput workflow for automated molecular docking and spatial analysis using AutoDock Vina, MGLTools, and PyMOL. It is designed to streamline the transition from raw structural files to comprehensive binding data.

🚀 **Key Features**

- Intelligent Receptor Pre-processing: Automatically detects alternate conformations in PDB files using `split_check.py`. If multiple conformations are found, it isolates the primary conformation (_A) to ensure docking consistency.


- Standardized Ligand Preparation: Converts SDF files to PDB via PyMOL and prepares them into PDBQT format using MGLTools, including the addition of Gasteiger charges.


- High-Throughput Docking: A centralized Windows Batch script (`automated_docking.bat`) manages the entire flow, executing AutoDock Vina across all receptor-ligand combinations.

- Comprehensive Spatial Analysis: Post-docking analysis via `analyse_vina.py` uses PyMOL to calculate:

  - Binding affinities from Vina remarks.
  
  - Centroid distances based on user-defined coordinates.
  
  - Reference distances to a crystal template.
  
  - Radius of gyration and polar contact residues.


📂 **Repository Structure**

- `automated_docking.bat`: The main entry point for the pipeline.

- `scripts/`: Contains custom Python helpers:


  - `split_check.py`: Logic for alternate conformation handling.
  
  
  - `analyse_vina.py`: Spatial analysis and CSV generation script.


- `variables/`: Contains `settings.txt` (path configurations) and `variables.txt` (Vina search configurations).


- `receptor/`: Input folder for raw PDB protein files.


- `ligand/`: Input folder for ligand files.

🛠️ **Setup & Usage**

***1. Configuration***

Edit `.\variables\settings.txt` to define your local installation paths for:

  - MGL_PYTHON: Path to MGLTools python executable.
 
  - PYMOL_EXE: Path to PyMOL executable.
  
  - VINA: Path to AutoDock Vina executable.
  
  - Check more details in the README.md file

***2. Define Search Space***

Set your docking box coordinates (center and dimensions) in `.\variables\variables.txt`.

***3. Run the Pipeline***

Double-click `automated_docking.bat`. The script will:

  - Load your configuration paths.
  
  - Pre-process receptors (handling split conformations).
  
  - Prepare ligands into PDBQT format.
  
  - Run AutoDock Vina for every ligand against every receptor.

***4. Analysis***

Run the analysis script `automated_analysis.bat` to compile results into a master CSV:


📊 **Outputs**

`receptor_out/`: Prepared PDBQT receptor files.

`ligand_out/`: Prepared PDBQT ligand files.

`output/`: Subfolders for each receptor containing _out.pdbqt docking results.

`results/`: Comprehensive CSV reports containing affinities and spatial metrics.
