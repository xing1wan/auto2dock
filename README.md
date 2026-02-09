You need to have the following installed:
MGL, PyMOL, Vina, and anaconda

Find in MGL installation path the python.exe and Utilities24 folder, replace the texts in settings.txt
e.g.
    MGL_PYTHON=C:\Program Files (x86)\MGLTools-1.5.7\python.exe
    UTILS=C:\Program Files (x86)\MGLTools-1.5.7\Lib\site-packages\AutoDockTools\Utilities24

Find in Vina installation path the vina.exe, replace the texts in settings.txt
e.g.
    VINA=C:\Program Files (x86)\The Scripps Research Institute\Vina\vina.exe

Find in PyMOL installation path the PyMOLWin.exe, it might be slightly different, but should be one which opens PyMOL GUI, replace the texts in settings.txt
e.g.
    PYMOL_EXE=C:\Users\wanx1\AppData\Local\pymol\PyMOLWin.exe

Anaconda can be installed with Uni's software center, open cmd (win+R) then find where is conda, by typing "where conda" and enter, replace the texts in settings.txt
e.g.
    CONDA_BAT=C:\ProgramData\anaconda3\condabin\conda.bat

Similarly python3 is also coming with anaconda, replace the texts in settings.txt
e.g.
    ANACONDA_PYTHON=C:\ProgramData\anaconda3\python.exe

Replace the your own crystal reference structure in the reference folder
e.g.
    REF_PDB=.\reference\3o5b_pdb.ent
