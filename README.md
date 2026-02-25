# auto2dock - Automated Molecular Docking & Analysis Pipeline
This repository provides an automated workflow for high-throughput molecular docking using AutoDock Vina and MGLTools. The pipeline is designed to handle protein structures with multiple conformations, standardize receptor (protein) and ligand preparation, and perform batch analysis of docking results.


## 🚀 **Key Features**

- Raw data retrieving: `preclean_pdb.bat` script serves as an automated, end-to-end orchestration pipeline that manages local environment setup, interactive RCSB PDB data retrieval, and multi-stage structural refinement—including chain-specific cleaning, coordinate-frame alignment, and RMSD-based receptor selection—to prepare standardized protein structures for molecular docking.

- Intelligent Receptor Pre-processing: Automatically detects alternate conformations in PDB files using `split_check.py`. If multiple conformations are found, it isolates the primary conformation (_A) to ensure docking consistency.

- Standardized Ligand Preparation: Converts SDF files to PDB via PyMOL and prepares them into PDBQT format using MGLTools, including the addition of Gasteiger charges.

- High-Throughput Docking: A centralized Windows Batch script (`automated_docking.bat`) manages the entire flow, executing AutoDock Vina across all receptor-ligand combinations.

- Comprehensive Spatial Analysis: Post-docking analysis via `analyse_vina.py` uses PyMOL to calculate:

  - Binding affinities from Vina remarks.
  
  - Centroid distances based on user-defined coordinates.
  
  - Reference distances to a crystal template.
  
  - Radius of gyration and polar contact residues.


## 📂 **Repository Structure**

- `automated_docking.bat`: The main entry point for the pipeline.

- `automated_analysis.bat`: Optimal data analysis tool

- `scripts/`: Contains custom Python helpers:

  - `00-06.py`: Download crystalised structure from PDB using text search, and select the most similar reference for your protein.

  - `split_check.py`: Logic for alternate conformation handling.
    
  - `analyse_vina.py`: Spatial analysis and CSV generation script.
 
  - `visualise_vina.py`: Visualise the districution of 9 docking results from Vina.

- `variables/`: Contains `settings.txt` (path configurations) and `variables.txt` (Vina search configurations).

- `receptor/`: Input folder for your PDB protein files.

- `sdf/`: Input folder for ligand files in `.sdf` format.


## 🛠️ **Setup & Usage**

### ***1. Configuration***

Edit `.\variables\settings.txt` to define your local installation paths for:

  - MGL_PYTHON: Path to MGLTools python executable.
 
  - PYMOL_EXE: Path to PyMOL executable.
  
  - VINA: Path to AutoDock Vina executable.
  
  - Check more details in the README.md file

  - You need to have the following installed: MGL tools ([https://ccsb.scripps.edu/mgltools/downloads/](url)), PyMOL ([https://www.pymol.org/](url)), Vina ([https://vina.scripps.edu/downloads/](url)), and Anaconda ([https://www.anaconda.com/download](url))

    - Find in MGL installation path the python.exe and Utilities24 folder, replace the texts in settings.txt
    e.g.

        ```
        MGL_PYTHON=C:\Program Files (x86)\MGLTools-1.5.7\python.exe
        UTILS=C:\Program Files (x86)\MGLTools-1.5.7\Lib\site-packages\AutoDockTools\Utilities24
        ```
    
    - Find in Vina installation path the vina.exe, replace the texts in settings.txt
    e.g.
        ```
        VINA=C:\Program Files (x86)\The Scripps Research Institute\Vina\vina.exe
        ```
    
    - Find in PyMOL installation path the PyMOLWin.exe, it might be slightly different, but should be one which opens PyMOL GUI, replace the texts in settings.txt
    e.g.
        ```
        PYMOL_EXE=C:\Users\xxxx\AppData\Local\pymol\PyMOLWin.exe
        ```
    
    - Anaconda can be installed with your own choices, open cmd (win+R) then find where is conda, by typing "where conda" and enter, replace the texts in settings.txt
    e.g.
        ```
        CONDA_BAT=C:\ProgramData\anaconda3\condabin\conda.bat
        ```
    
    - Similarly python3 is also coming with anaconda, replace the texts in settings.txt
    e.g.
        ```
        ANACONDA_PYTHON=C:\ProgramData\anaconda3\python.exe
        ```
    
    - The crystal reference structure will be selected by `preclean_pdb.bat` and saved in the reference folder
    e.g.
        ```
        REF_PDB=.\reference\3o5b.pdb
        ```
    **‼️NOTE‼️This pipeline has been tested on MGL win32_1.5.7 (Python 2.7.11), Vina 1_1_2_win32, PyMOL 3.1.6.1, and Anaconda Navigator 2.7.0 (conda 24.11.3, Python 3.12.7)** 



### ***2. Define Search Space***

Set your docking search grid dimensions in `.\variables\variables.txt`. The centroid of the ligand is calculated by `preclean_pdb.bat`

### ***3. Run the Pipeline***

Double-click `preclean_pdb.bat`. The script will:

  - Download PDBs based on your search words.

  - Clean PDB files and synchronise their positions according to your protein.

  - Identify ligands bound in the clean PDBs, and find centroid of those ligands.

  - Identify the most similar crystal structure to your protein. 

  - Update the centroid to vina's parameters in `variables\variables.txt`, and update the most similar crystal structure as reference in `variables\settings.txt`

Double-click `automated_docking.bat`. The script will:

  - Load your configuration paths.
  
  - Pre-process receptors (handling split conformations).
  
  - Prepare ligands into PDBQT format.
  
  - Run AutoDock Vina for every ligand against every receptor.

### ***4. Analysis***

Run the analysis script `automated_analysis.bat` to compile results into a master CSV, and visualise the distribution of the docking results in bar charts and heatmap.


## 📊 **Outputs**

`pdb`: Raw PDB files downloaded on command from PDB database.

`pdb_clean`: Clean PDB monomers with similar protein length to your protein.

`prep_results`: Structural comparison between clean PDBs and your protein, identified ligands, and coordinates of centroid for docking.

`receptor_out/`: Prepared PDBQT receptor files.

`reference`: Best match crystal structure to your protein.

`ligand`: Prepared PDB ligand files from `.sdf` format.

`ligand_out/`: Prepared PDBQT ligand files.

`output/`: Subfolders for each receptor containing `_out.pdbqt` docking results.

`results/`: Comprehensive CSV reports containing affinities and spatial metrics.










