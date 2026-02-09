import os
import shutil
import argparse
import glob
import subprocess

def check_for_alt_confs(pdb_path):
    """Checks the 17th character of ATOM/HETATM lines for alternate locations."""
    with open(pdb_path, 'r') as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                # PDB standard: index 16 is the alternate location indicator
                if len(line) > 16 and line[16] != ' ':
                    return True
    return False

def prepare_receptor_with_fix(output_dir, receptor_pdb, mgl_python, mgl_utils_dir):
    receptor_filename = os.path.basename(receptor_pdb)
    receptor_stem = os.path.splitext(receptor_filename)[0]
    
    # Define paths for MGL utility scripts
    split_script = os.path.join(mgl_utils_dir, "prepare_pdb_split_alt_confs.py")
    prep_script = os.path.join(mgl_utils_dir, "prepare_receptor4.py")
    
    target_pdb = receptor_pdb

    if check_for_alt_confs(receptor_pdb):
        print(f"[INFO] Alternate locations found. Copying {receptor_filename} to root for MolKit...")
        
        # --- WORKAROUND: Copy to root for MolKit compatibility ---
        shutil.copyfile(receptor_pdb, f"./{receptor_filename}")
        
        # Run split utility in the current folder
        subprocess.run([mgl_python, split_script, "-r", receptor_filename], check=True)
        
        # Resulting file will be 'receptor_A.pdb' in root
        temp_conformer_a = f"{receptor_stem}_A.pdb"
        final_conformer_a = os.path.join(os.path.dirname(receptor_pdb), temp_conformer_a)
        
        if os.path.exists(temp_conformer_a):
            shutil.move(temp_conformer_a, final_conformer_a)
            target_pdb = final_conformer_a
            print(f"[SUCCESS] Conformation A {os.path.basename(final_conformer_a)} moved to {os.path.dirname(final_conformer_a)}")
        # 2. Cleanup: Remove all other conformers (B, C, etc.) from the root
        # This matches anything like xxx_*.pdb in the current folder
        other_conformers = glob.glob(f"./{receptor_stem}_*.pdb")
        for f in other_conformers:
            try:
                if not f.endswith("_A.pdb"): os.remove(f)
                print(f"[CLEANUP] Removed extra conformer(s) from root: {f}")
            except:
                pass
        
        # Cleanup root copies
        if os.path.exists(receptor_filename): os.remove(receptor_filename)
        
    else:
        print(f"[INFO] No alternate locations detected in {os.path.basename(receptor_pdb)}.")
    
    # Run final preparation
    final_filename_only = os.path.basename(target_pdb)
    final_stem = os.path.splitext(final_filename_only)[0]
    output_pdbqt = os.path.join(output_dir, f"{final_stem}.pdbqt")
    print(f"[INFO] Preparing final receptor: {output_pdbqt}")

    subprocess.run([mgl_python, prep_script, "-r", target_pdb, "-o", output_pdbqt, 
                    "-A", "hydrogens", "-U", "waters", "-U", "nphs"], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--o", required=True, help="Output parent directory")
    parser.add_argument("--r", required=True, help="Receptor PDB")
    parser.add_argument("--p", required=True, help="MGL python path")
    parser.add_argument("--u", required=True, help="MGL utilities24 path")
    args = parser.parse_args()
    
    # Use args.o, args.r, etc., in your existing analysis logic...
    prepare_receptor_with_fix(args.o, args.r, args.p, args.u)

if __name__ == "__main__":
    main()


# if __name__ == "__main__":
#     # Example usage: python auto_prepare_receptor.py receptor/3o5b.pdb
#     if len(sys.argv) < 2:
#         print("Usage: python auto_prepare_receptor.py <path_to_pdb>")
#         sys.exit(1)
        
#     # These paths should ideally come from your exe.txt or environment variables
#     MGL_PY = r"C:\Program Files (x86)\MGLTools-1.5.7\python.exe"
#     MGL_UTILS = r"C:\Program Files (x86)\MGLTools-1.5.7\Lib\site-packages\AutoDockTools\Utilities24"
    
#     prepare_receptor_with_fix(sys.argv[1], MGL_PY, MGL_UTILS)