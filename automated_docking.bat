@echo off
setlocal enabledelayedexpansion

:: ==============================================================
:: CONFIGURATION: PASTE YOUR MGLTOOLS and PYMOL INSTALL PATH HERE
:: ==============================================================
:: Construct paths based on the installation folder
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

@REM :: --- LOGGING SETUP ---
@REM :: Create the LOG folder if it doesn't exist (provided by your external variable)
@REM if not exist "%LOG%" mkdir "%LOG%"

@REM :: Get date in YYYYMMDD format (depends on system locale, usually works for most)
@REM set "t_date=%date:~10,4%%date:~4,2%%date:~7,2%"

@REM :: Get time and handle the leading space if the hour is < 10
@REM set "t_time=%time: =0%"
@REM set "t_time=%t_time:~0,2%%t_time:~3,2%"

@REM :: Combine them into a single stamp
@REM set "STAMP=%t_date%_%t_time%"

@REM :: Define the log filename with a timestamp (optional) to avoid overwriting
@REM set "LOG_FILE=%LOG%\docking_log_%STAMP%.txt"

@REM echo [INFO] Pipeline started. Logging to %LOG_FILE%

@REM :: CALL the logic block and redirect its output
@REM call :main_logic > "%LOG_FILE%" 2>&1

@REM echo [INFO] Pipeline Finished.
@REM pause
@REM exit /b

@REM :: ====================================================
@REM :: EVERYTHING BELOW THIS LINE GOES INTO THE LOG
@REM :: ====================================================
@REM :main_logic
@REM echo Run started at: %date% %time%

:: Verify paths were loaded [cite: 2]
echo Using MGL python: %MGL_PYTHON%
echo Using PyMOL: %PYMOL_EXE%
echo Using MGL: %MGL_PYTHON%
echo Utilities are in: %UTILS%
echo Using Vina: %VINA%
echo Using conda: %CONDA_BAT%
echo Using python3: %ANACONDA_PYTHON%

:: Folder names in your current working directory, receptor, sdf, var, and scripts folders need to exist
:: put all sdf ligand files downloaded from Pubchem to sdf folder 
:: put all clean protein targets .pdb files to receptor folder
:: scripts folder should contain the customised python file convert_sdf_to_pdb.py
:: variables folder should contain the variables.txt file, which contains the centroid and dimensions
set "RECEPTOR_DIR=.\receptor" 
set "LIGAND_DIR=.\ligand"
set "SCR_DIR=.\scripts"
set "VAR=.\variables"

set "OUTPUT_DIR=.\output"
set "RECP_OUT=.\receptor_out"
set "LIG_OUT=.\ligand_out"

:: Verify if the MGL path and PyMOL are in place
if not exist "%MGL_PYTHON%" (
    echo [ERROR] Could not find python.exe at: "%MGL_PYTHON%"
    echo Please check the MGL_PATH variable at the top of this script.
    pause
    exit /b
)
if not exist "%PYMOL_EXE%" (
    echo [ERROR] Could not find PyMOLWIN.exe [cite: 2]
    echo Please check the PyMOL installation.
    pause
    exit /b
)

:: Create output directories if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%RECP_OUT%" mkdir "%RECP_OUT%"
if not exist "%LIG_OUT%" mkdir "%LIG_OUT%"

echo ========================================
echo STEP 1: Converting SDF to PDB (PyMOL)
echo ========================================
:: -c means run in command-line mode (no GUI)
:: -r runs the python script we just created
"%PYMOL_EXE%" -c -k -r "%SCR_DIR%\convert_sdf_to_pdb.py"

echo.
echo ========================================
echo STEP 2: Preparing Receptors (PDBQT)
echo ========================================

:: --- PROCESS PROTEINS ---
for %%P in ("%RECEPTOR_DIR%\*.cif") do (
    set "FILE_EXT=%%~xP"
    set "BASENAME=%%~nP"
    set "FULL_PATH=%%~fP"
    
    if /I "!FILE_EXT!"==".cif" (
        echo [CIF DETECTED] Aligning and converting !BASENAME!.cif to PDB...
        
        :: 1. Load TARGET 
        :: 2. Load the current CIF
        :: 3. Superimpose CIF to TARGET
        :: 4. Save the aligned object as PDB
        "%PYMOL_EXE%" -c -d "load %TARGET%, ref; load %%~fP, obj; super obj, ref; save %RECEPTOR_DIR%\!BASENAME!.pdb, obj" >nul
        
        :: Update the path to point to the newly created, ALIGNED PDB
        set "FULL_PATH=%RECEPTOR_DIR%\!BASENAME!.pdb"
    )
)

set "FILE_COUNT=0"
for %%A in ("%RECEPTOR_DIR%\*.cif") do set /a FILE_COUNT+=1
:: Small pause to let the OS release the file handle 
:: Calculate timeout: 1/5 second per file, minimum 5 seconds, change denominator to change the time of waiting
set /a "TIMEOUT_VAL=%FILE_COUNT% * 1 / 2"
if %TIMEOUT_VAL% LSS 5 set "TIMEOUT_VAL=5"

for /L %%i in (1,1,%TIMEOUT_VAL%) do (
    <nul set /p "=."
    timeout /t 1 /nobreak >nul
)

echo.

for %%P in ("%RECEPTOR_DIR%\*.pdb") do (
    :: Define the expected output path for checking
    set "OUT_FILE=%RECP_OUT%\%%~nP.pdbqt"
    set "OUT_FILE_A=%RECP_OUT%\%%~nP_A.pdbqt"
    if exist "!OUT_FILE!" (
        echo [SKIP] Receptor %RECEPTOR_DIR%\%%~nxP already prepared.
    ) else if exist "!OUT_FILE_A!" (
        echo [SKIP] Receptor %RECEPTOR_DIR%\%%~nxP already prepared.
    ) else (
        echo [PROTEIN] Preparing: %%~nxP
        :: Call the python helper to check/split and prepare pdbqt
        "%ANACONDA_PYTHON%" "%SCR_DIR%\split_check.py" --o "%RECP_OUT%" --r "%%~fP" --p "%MGL_PYTHON%" --u "%UTILS%"
    )
)

echo.
echo ========================================
echo STEP 3: Preparing Ligands (PDBQT)
echo ========================================
:: --- PROCESS LIGANDS ---
for %%L in ("%LIGAND_DIR%\*.pdb") do (
    :: Define the expected output path for checking
    set "OUT_FILE=%LIG_OUT%\%%~nL.pdbqt"

    :: CHECK 1: Skip if already exists
    if exist "!OUT_FILE!" (
        echo [SKIP] Ligand %%~nxL already prepared.
    ) else (
        echo [LIGAND] Preparing: %%~nxL
        copy "%%~fL" ".\temp.pdb" >nul
        :: Small pause to let the OS release the file handle (prevents MolKit crashes)
        timeout /t 1 /nobreak >nul
        "%MGL_PYTHON%" "%UTILS%\prepare_ligand4.py" -l ".\temp.pdb" -o "%LIG_OUT%\%%~nL.pdbqt"
        del ".\temp.pdb"
    
        :: CHECK 2: Verify generation and break if failed
        if not exist "!OUT_FILE!" (
            echo.
            echo [FATAL ERROR] Failed to generate "!OUT_FILE!"
            echo Stopping pipeline to prevent further errors.
            exit /b 1
        )
        echo [SUCCESS] Generated: %%~nL.pdbqt
    )
)

echo.
echo ========================================
echo Preparation Complete! Check the '%RECP_OUT%' and '%LIG_OUT%' folders.
echo ========================================
pause

echo.
echo ========================================
echo STEP 4: AutoDock with Vina 
echo ========================================
:: --- DOCK WITH PROCESSED RECEPTORS AND LIGANDS ---
for %%R in ("%RECP_OUT%\*.pdbqt") do (
    
    :: Create a subfolder named after the receptor
    set "CURRENT_RECP_DIR=%OUTPUT_DIR%\%%~nR"
    if not exist "!CURRENT_RECP_DIR!" mkdir "!CURRENT_RECP_DIR!"
    
    for %%L in ("%LIG_OUT%\*.pdbqt") do (
        :: Define the final result path: Output\ReceptorName\Receptor_Ligand_out.pdbqt
        set "FINAL_RESULT=!CURRENT_RECP_DIR!\%%~nR_%%~nL_out.pdbqt"

        if exist "!FINAL_RESULT!" (
            echo [SKIP] Receptor %%~nR with ligand %%~nL already docked. 
        ) else (
            echo ----------------------------------------
            echo [DOCKING] %%~nR + %%~nL 
            
            :: Run Vina and tell it exactly where to save the output file (--out)
            "%VINA%" --receptor "%%~fR" --ligand "%%~fL" --config "%VAR%\variables.txt" --out "!FINAL_RESULT!"
            
            :: CHECK: Verify if Vina actually produced the file
            if not exist "!FINAL_RESULT!" (
                echo [ERROR] Vina failed to dock %%~nL into %%~nR
            ) else (
                echo [SUCCESS] Saved to !FINAL_RESULT!
            )
        )
    )
    echo Receptor %%~nR docking completed. [cite: 19]
)

echo.
echo ========================================
echo Docking Complete! Check the '%OUTPUT_DIR%' folders.
echo Then you can continue with automated_analysis.bat.
echo ========================================

@REM goto :eof

pause