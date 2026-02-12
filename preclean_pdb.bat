@echo off
setlocal enabledelayedexpansion

:: --- 1. LOAD CONFIGURATION ---

set "EXE_CONF=.\variables\settings.txt"
if not exist "%EXE_CONF%" (
    echo [ERROR] %EXE_CONF% not found!
    pause
    exit /b
)

:: Parse the file and set variables
for /f "delims=" %%a in (%EXE_CONF%) do (
    set "%%a"
)

:: Verify paths were loaded [cite: 2]
echo Using PyMOL: %PYMOL_EXE%
echo Using target protein: %TARGET%
echo Using Anaconda python: %ANACONDA_PYTHON%
pause

:: --- 2. DEFINE DIRECTORIES ---
set "RAW_PDB_DIR=.\pdb"
set "CLEAN_OUT=.\pdb_clean"
set "SCR_DIR=.\scripts"
set "PREP_RESULTS=.\prep_results"

echo.
echo [INFO] Starting Receptor Pre-Cleaning Pipeline...

echo ====================================================
echo PRE-CLEANING STEP 01: PDB CLEANING AND FILTERING
echo ====================================================

:: Locate the target PDB (assumes there is only one in the target folder)
echo [1/5] Cleaning PDBs and Filtering with Your Target %TARGET% ...

:: Run the first script
:: PyMOL arguments: -c (headless), -r (run script), followed by script arguments
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\01_clean_pdbs.py"
echo.
echo [STEP 01 COMPLETE] Check %CLEAN_OUT% for results.
pause

echo.
echo ====================================================
echo PRE-CLEANING STEP 02: BATCH SUPERIMPOSITION
echo ====================================================
echo [2/5] Superimpositing Clean PDBs to Your Target %TARGET% ...
:: --- DEFINE STEP 02 VARIABLES ---

:: Run Step 02
:: Arguments: 1=Input(clean), 2=Settings, 3=Output CSV
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\02_batch_superimposition.py"
:: Small pause to let the OS release the file handle 
timeout /t 5 /nobreak >nul

:: --- CHECK FOR RMSD RESULT ---
echo [CHECK] Searching for RMSD results in %PREP_RESULTS%...


set "FOUND_RMSD="
for /f "delims=" %%F in ('dir /s /b "%PREP_RESULTS%\*_RMSD.csv" 2^>nul') do (
    set "FOUND_RMSD=%%F"
)

if defined FOUND_RMSD (
    echo [SUCCESS] Found RMSD file: %FOUND_RMSD%
) else (
    echo [ERROR] No file ending in _RMSD.csv was found in %PREP_RESULTS%.
    pause
    exit /b
)
@REM echo.
@REM echo [STEP 02 COMPLETE] Check %PREP_RESULTS% for results.
@REM pause

echo.
echo ====================================================
echo PRE-CLEANING STEP 03: LIGAND IDENTIFICATION
echo ====================================================
echo [3/5] Listing All Bound Ligands ...
:: Simply run the script. It will find the CSV and Clean folder itself.
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\03_lig_id.py"
:: Small pause to let the OS release the file handle 
timeout /t 5 /nobreak >nul

if exist ".\prep_results\top_match_ligands_inventory.csv" (
    echo [SUCCESS] Ligand inventory created.
) else (
    echo [ERROR] Step 03 failed.
)
@REM echo.
@REM echo [STEP 03 COMPLETE] Check %PREP_RESULTS% for results.
@REM pause

echo.
echo ====================================================
echo PRE-CLEANING STEP 04: CENTROID CALCULATION
echo ====================================================

:: Step 04: Centroid
echo [4/5] Extracting Binding Site Centroid...
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\04_extract_glc_with_centroid.py"
:: Small pause to let the OS release the file handle 
timeout /t 5 /nobreak >nul
@REM echo.
@REM echo [STEP 04 COMPLETE] Check %PREP_RESULTS% for results.
@REM pause

echo.
echo ====================================================
echo PRE-CLEANING STEP 05: UPDATING CENTROID
echo ====================================================

:: Step 05: Update Variables for Vina
echo [5/5] Updating variables.txt with calculated centroid...
"%ANACONDA_PYTHON%" "%SCR_DIR%\05_update_vina_variables.py"
:: Small pause to let the OS release the file handle 
timeout /t 5 /nobreak >nul
@REM echo.
@REM echo [STEP 05 COMPLETE] Check .\variables\variables.txt for updated coords.
@REM pause

echo --------------------------------------
echo [FINISHED] Pipeline complete. variables.txt is ready for docking.
pause