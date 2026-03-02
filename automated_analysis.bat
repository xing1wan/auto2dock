@echo off
setlocal enabledelayedexpansion

:: ==============================================================
:: CONFIGURATION: PASTE YOUR anaconda and PYMOL INSTALL PATH HERE
:: ==============================================================
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
echo Using MGL python: %MGL_PYTHON%
echo Using PyMOL: %PYMOL_EXE%
echo Utilities are in: %UTILS%
echo Using Vina: %VINA%
echo Using conda: %CONDA_BAT%
echo Using reference protein: %REF_PDB%

:: Folder names in your current working directory, receptor, sdf, var, and scripts folders need to exist
:: put all sdf ligand files downloaded from Pubchem to sdf folder 
:: put all clean protein targets .pdb files to receptor folder
:: scripts folder should contain the customised python file convert_sdf_to_pdb.py
:: variables folder should contain the variables.txt file, which contains the centroid and dimensions
:: Data folders used by the scripts 
set "OUTPUT_DIR=.\output"
set "RECEPTOR_DIR=.\receptor"
set "RESULTS_DIR=.\results"
set "VAR=.\variables"
set "SCR_DIR=.\scripts"

set "ENV_NAME=visualisation_env"


if not exist "%OUTPUT_DIR%" (
    echo [ERROR] Could not find output folder %OUTPUT_DIR%
    echo Please run automated_docking.bat first.
    pause
    exit /b
)

if not exist "%PYMOL_EXE%" (
    echo [ERROR] Could not find PyMOLWIN.exe [cite: 2]
    echo Please check the PyMOL installation.
    pause
    exit /b
)

if not exist "%CONDA_BAT%" (
    echo [ERROR] Could not find conda [cite: 2]
    echo Please check anaconda installation.
    pause
    exit /b
)

@REM echo ========================================
@REM echo SETTING UP LOCAL ENVIRONMENT
@REM echo ========================================
@REM :: Check if the environment directory exists in the conda info list
@REM call "%CONDA_BAT%" info --envs | findstr /l /c:"%ENV_NAME%" >nul

@REM if %errorlevel% equ 0 (
@REM     echo [INFO] Environment '%ENV_NAME%' already exists. Activating...
@REM     call "%CONDA_BAT%" activate %ENV_NAME% 
@REM ) else (
@REM     echo [INFO] Environment '%ENV_NAME%' not found. Creating...
@REM     call "%CONDA_BAT%" env create -n %ENV_NAME% -f "%VAR%\visualisation_env.yml" -y
@REM )

@REM echo.
@REM pause

echo.
echo ========================================
echo STEP 1: Analyse Vina results
echo ========================================
@REM echo o: %OUTPUT_DIR%
@REM echo r: %RECEPTOR_DIR%
@REM echo t: "%TEMP_DIR%\3o5b_pdb.ent"
@REM echo R: %RESULTS_DIR%
@REM echo var: "%VAR%\variables.txt"
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\analyse_vina.py"  --o "%OUTPUT_DIR%" --r "%RECEPTOR_DIR%" --t "%REF_PDB%" --R "%RESULTS_DIR%" --var "%VAR%\variables.txt"
@REM pause

echo.
echo ========================================
echo STEP 2: Running Visualisation
echo ========================================
:: --- STEP 2: Run Visualisation ---
:: We use 'conda run' to execute the script inside the env without "activating" it manually
call "%CONDA_BAT%" run -n %ENV_NAME% python "%SCR_DIR%\visualise_vina.py" --R "%RESULTS_DIR%"
dir "%RESULTS_DIR%"
echo.
choice /c cq /n /m "Visualisation completed. Press [C] to clean the system or [Q] to abort: "
if %errorlevel% equ 2 exit /b

echo.
echo ========================================
echo CLEANING UP ENVIRONMENT
echo ========================================
call "%CONDA_BAT%" deactivate
call "%CONDA_BAT%" remove -n %ENV_NAME% --all -y -q

echo.
echo Process Complete. Temporary environment removed.

pause

