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
echo Using conda: %CONDA_BAT%
echo.
pause

:: --- 2. DEFINE DIRECTORIES ---
set "RAW_PDB_DIR=.\pdb"
set "CLEAN_OUT=.\pdb_clean"
set "SCR_DIR=.\scripts"
set "PREP_RESULTS=.\prep_results"
set "VAR=.\variables"
set "ENV_NAME=visualisation_env"


echo ====================================================
echo SETTING UP LOCAL ENVIRONMENT
echo ====================================================
:: Check if the environment directory exists in the conda info list
call "%CONDA_BAT%" info --envs | findstr /l /c:"%ENV_NAME%" >nul

if %errorlevel% equ 0 (
    echo [INFO] Environment '%ENV_NAME%' already exists. Activating...
    call "%CONDA_BAT%" activate %ENV_NAME% 
) else (
    echo [INFO] Environment '%ENV_NAME%' not found. Creating...
    call "%CONDA_BAT%" env create -n %ENV_NAME% -f "%VAR%\visualisation_env.yml" -y
    echo [INFO] Activating environment '%ENV_NAME%' ...
    call "%CONDA_BAT%" activate %ENV_NAME% 
)


:: CHECK IF rcsb-api IS INSTALLED 
python -c "import rcsbapi" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] rcsb-api not found. Installing via pip...
    pip install rcsb-api
)

:: DYNAMICALLY SET THE PYTHON PATH FOR THIS ENV
:: This ensures Step 00 uses the version with rcsb-api installed 
for /f "tokens=*" %%i in ('where python') do set "ENV_PYTHON=%%i" & goto :found_py
:found_py
echo.
echo Using Environment Python: %ENV_PYTHON%
@REM echo.
@REM pause

echo.
echo ====================================================
echo DOWNLOAD PDB FILES ON COMMAND
echo ====================================================

:: STEP 00: Download PDBs
echo [STEP 00] RCSB PDB Downloader
set /p "QUERY=Enter search term (e.g. GlpA): "

:: Call the download script (Interactive)
"%ENV_PYTHON%" "%SCR_DIR%\00_download_pdbs.py" "%QUERY%" --out "%RAW_PDB_DIR%"
echo.
echo [STEP 00 COMPLETE] Check %RAW_PDB_DIR% for downloads.
pause

echo.
echo [INFO] Starting Receptor Pre-Cleaning Pipeline...

echo ====================================================
echo PRE-CLEANING STEP 01: PDB CLEANING AND FILTERING
echo ====================================================

:: Locate the target PDB (assumes there is only one in the target folder)
echo [1/6] Cleaning PDBs and Filtering with Your Target %TARGET% ...
:: --- DYNAMIC TIMEOUT CALCULATION ---
set "FILE_COUNT=0"
for %%A in ("%RAW_PDB_DIR%\*.pdb" "%RAW_PDB_DIR%\*.ent") do set /a FILE_COUNT+=1

:: Run the first script
:: PyMOL arguments: -c (headless), -r (run script), followed by script arguments
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\01_clean_pdbs.py" 
:: Small pause to let the OS release the file handle 
:: Calculate timeout: 1/5 second per file, minimum 5 seconds, change denominator to change the time of waiting
set /a "TIMEOUT_VAL=%FILE_COUNT% * 1 / 5"
if %TIMEOUT_VAL% LSS 5 set "TIMEOUT_VAL=5"

echo [INFO] Cleaning PDB files: 
for /L %%i in (1,1,%TIMEOUT_VAL%) do (
    <nul set /p "=."
    timeout /t 1 /nobreak >nul
)

@REM dir %CLEAN_OUT%
@REM echo.
@REM echo [STEP 01 COMPLETE] Check %CLEAN_OUT% for results.
@REM pause

echo.
echo ====================================================
echo PRE-CLEANING STEP 02: BATCH SUPERIMPOSITION
echo ====================================================
echo [2/6] Superimpositing Clean PDBs to Your Target %TARGET% ...
:: Arguments: 1=Input(clean), 2=Settings, 3=Output CSV
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\02_batch_superimposition.py"
:: Small pause to let the OS release the file handle 
echo [INFO] Superimpositing PDBs: 
for /L %%i in (1,1,%TIMEOUT_VAL%) do (
    <nul set /p "=."
    timeout /t 1 /nobreak >nul
)
:: --- CHECK FOR RMSD RESULT ---
echo.
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
echo [3/6] Listing All Bound Ligands ...
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
echo [4/6] Extracting Binding Site Centroid...
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
echo [5/6] Updating variables.txt with calculated centroid...
"%ANACONDA_PYTHON%" "%SCR_DIR%\05_update_vina_variables.py"
:: Small pause to let the OS release the file handle 
timeout /t 5 /nobreak >nul
@REM echo.
@REM echo [STEP 05 COMPLETE] Check .\variables\variables.txt for updated coords.
@REM pause

echo.
echo ====================================================
echo PRE-CLEANING STEP 06: UPDATING REFERENCE
echo ====================================================

:: Step 06: Update Settings for Vina
echo [6/6] Updating settings.txt with the most similar reference PDB...
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\06_select_reference.py"

echo.
echo [FINISHED] Pipeline complete. settings.txt and variables.txt is ready for docking.
pause