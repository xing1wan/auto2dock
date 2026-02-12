import argparse
import os
from pymol import cmd


def get_setting(settings_path, key):
    """Generic parser to get values from settings.txt."""
    try:
        with open(settings_path, 'r') as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=")[1].strip()
    except Exception as e:
        print(f"Error reading setting {key}: {e}")
    return None



def clean_and_rename_pdbs(input_folder, output_folder, settings_path):
    # 1. Setup
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get target path from settings
    target_pdb_path = get_setting(settings_path, "TARGET")
    if not target_pdb_path or not os.path.exists(target_pdb_path):
        print(f"Error: Target path '{target_pdb_path}' not found in settings or disk.")
        return
    
    # Load the target ONCE to establish the length threshold
    target_internal_name = "REFERENCE_TARGET"
    cmd.delete("all")
    cmd.load(target_pdb_path, target_internal_name)
    
    # Calculate threshold: 60% of target chain A length
    ref_ca_count = cmd.count_atoms(f"{target_internal_name} and chain A and polymer.protein and name CA")
    min_length = ref_ca_count * 0.6
    print(f"Target CA count: {ref_ca_count}. Min threshold: {min_length:.1f}")

    files = [f for f in os.listdir(input_folder) if f.endswith('.ent')]

    for f in files:
        try:
            # DO NOT reinitialize here, just delete previous temporary objects
            temp_obj = "temp_load"
            cmd.delete(temp_obj) 
            
            file_path = os.path.join(input_folder, f)
            cmd.load(file_path, temp_obj)

            # 2. Identify the first chain
            chains = cmd.get_chains(temp_obj)
            if not chains:
                print(f"Skipping {f}: No chains found.")
                continue
            
            first_chain = chains[0]
            
            # 3. Check length
            residue_count = cmd.count_atoms(f"{temp_obj} and chain {first_chain} and polymer.protein and name CA")
            
            if residue_count < min_length:
                print(f"Skipping {f}: Chain {first_chain} too short ({residue_count} < {min_length:.0f})")
                cmd.delete(temp_obj)
                continue

            # 4. Processing
            new_filename = f.replace('pdb', '', 1) if f.startswith('pdb') else f
            pdb_id = new_filename.split('.')[0]
            
            # Rename and Clean
            cmd.set_name(temp_obj, pdb_id)
            cmd.remove(f"{pdb_id} and not chain {first_chain}")
            cmd.remove(f"{pdb_id} and solvent")
            cmd.remove(f"{pdb_id} and h.") # Optional: remove hydrogens to keep files small

            # 5. Save
            output_path = os.path.join(output_folder, f"{pdb_id}.pdb")
            cmd.save(output_path, pdb_id)
            print(f"Successfully processed: {pdb_id} (Chain {first_chain}, {residue_count} residues)")
            
            # Clean up for next iteration
            cmd.delete(pdb_id)

        except Exception as e:
            print(f"Critical error processing {f}: {e}")


# if __name__ == "__main__":
#     import sys
#     # sys.argv[0] is the script name
#     # sys.argv[1] is input_folder
#     # sys.argv[2] is output_folder
#     # sys.argv[3] is target_pdb_path
    
#     if len(sys.argv) >= 4:
#         # Note: PyMOL passes some internal args first, 
#         # so we check for the expected number of arguments.
#         input_dir = sys.argv[1]
#         output_dir = sys.argv[2]
#         settings_path = sys.argv[3]
#         clean_and_rename_pdbs(input_dir, output_dir, settings_path)
#     else:
#         print("Error: Missing arguments for 01_clean_pdbs.py")

# --- EXECUTION ---
# --- CONFIGURATION ---
input_dir = "./pdb"
output_dir = "./pdb_clean"
settings_path = "./variables/settings.txt"


clean_and_rename_pdbs(input_dir, output_dir, settings_path)