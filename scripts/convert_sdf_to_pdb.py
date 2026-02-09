import os
import sys
from pymol import cmd

def convert():
    sdf_dir = './sdf'
    ligand_dir = './ligand'

    if not os.path.exists(ligand_dir):
        os.makedirs(ligand_dir)

    files = [f for f in os.listdir(sdf_dir) if f.endswith('.sdf')]

    for f in files:
        name = os.path.splitext(f)[0]
        output_path = os.path.join(ligand_dir, name + ".pdb")
        
        if os.path.exists(output_path):
            # Added flush=True to ensure it prints to the .bat window immediately
            print(f"Skipping: {name}.pdb already exists.", flush=True)
            continue

        try:
            cmd.load(os.path.join(sdf_dir, f), "tmp_obj")
            cmd.save(output_path, "tmp_obj")
            cmd.delete("tmp_obj")
            
            if os.path.exists(output_path):
                print(f"Converted: {f}", flush=True)
            else:
                print(f"FAILED: {f} (File not created)", flush=True)
        except Exception as e:
            print(f"ERROR processing {f}: {str(e)}", flush=True)

convert()