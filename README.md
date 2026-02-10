# auto2dock - Automated Molecular Docking & Analysis Pipeline
This repository provides an automated workflow for high-throughput molecular docking using AutoDock Vina and MGLTools. The pipeline is designed to handle protein structures with multiple conformations, standardize receptor (protein) and ligand preparation, and perform batch analysis of docking results.


## 🚀 **Key Features**

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


  - `split_check.py`: Logic for alternate conformation handling.
  
  
  - `analyse_vina.py`: Spatial analysis and CSV generation script.


- `variables/`: Contains `settings.txt` (path configurations) and `variables.txt` (Vina search configurations).


- `receptor/`: Input folder for raw PDB protein files.


- `sdf/`: Input folder for ligand files in `.sdf` format.


- `reference/`: Folder to save the crystal structure as reference for your proteins

## 🛠️ **Setup & Usage**

***1. Configuration***

Edit `.\variables\settings.txt` to define your local installation paths for:

  - MGL_PYTHON: Path to MGLTools python executable.
 
  - PYMOL_EXE: Path to PyMOL executable.
  
  - VINA: Path to AutoDock Vina executable.
  
  - Check more details in the README.md file

  - You need to have the following installed: MGL, PyMOL, Vina, and anaconda

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
        PYMOL_EXE=C:\Users\wanx1\AppData\Local\pymol\PyMOLWin.exe
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
    
    - Replace the your own crystal reference structure in the reference folder
    e.g.
        ```
        REF_PDB=.\reference\3o5b_pdb.ent
        ```



### ***2. Define Search Space***

Set your docking box coordinates (center and dimensions) in `.\variables\variables.txt`.

### ***3. Run the Pipeline***

Double-click `automated_docking.bat`. The script will:

  - Load your configuration paths.
  
  - Pre-process receptors (handling split conformations).
  
  - Prepare ligands into PDBQT format.
  
  - Run AutoDock Vina for every ligand against every receptor.

### ***4. Analysis***

Run the analysis script `automated_analysis.bat` to compile results into a master CSV, and visualise the distribution of the docking results in bar charts and heatmap.


## 📊 **Outputs**

`receptor_out/`: Prepared PDBQT receptor files.

`ligand`: Prepared PDB ligand files from `.sdf` format.

`ligand_out/`: Prepared PDBQT ligand files.

`output/`: Subfolders for each receptor containing `_out.pdbqt` docking results.

`results/`: Comprehensive CSV reports containing affinities and spatial metrics.





