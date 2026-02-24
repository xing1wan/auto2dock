import os
import csv
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


def batch_superimpose(input_folder, settings_path, output_folder):
    # Get target path from settings
    target_pdb_path = get_setting(settings_path, "TARGET")

    if not target_pdb_path or not os.path.exists(target_pdb_path):
        print(f"Error: Target path '{target_pdb_path}' not found in settings or disk.")
        return
    
    # 1. Setup
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 0. COMPLETELY WIPE PYMOL STATE
    # This clears all objects, selections, and internal memory buffers
    cmd.reinitialize()

    # 1. Load the target and give it a UNIQUE internal name to avoid deletion
    target_internal_name = "REFERENCE_TARGET"
    
    # Clear existing object with this name just in case
    if target_internal_name in cmd.get_object_list():
        cmd.delete(target_internal_name)
        
    cmd.load(target_pdb_path, target_internal_name)
    print(f"Target loaded as: {target_internal_name}")

    files = [f for f in os.listdir(input_folder) if f.endswith(('.pdb'))]
    results = []

    # NEW: Track processed base names to avoid duplicates
    processed_ids = set()

    for f in files:
        file_path = os.path.join(input_folder, f)
        pdb_id = f.split('.')[0]

        # Skip if the file is actually the target file itself
        if pdb_id == target_internal_name:
            continue

        # Skip if we've already processed this ID (handles .ent vs .pdb)
        if pdb_id in processed_ids:
            print(f"Skipping duplicate: {f} (ID {pdb_id} already processed)")
            continue
        
        # Load mobile protein
        cmd.load(file_path, pdb_id)
        # Add to processed list after successful load
        processed_ids.add(pdb_id)

        # 2. Safety Check: Ensure the target still exists in the session
        if target_internal_name not in cmd.get_object_list():
            print(f"Error: {target_internal_name} was lost! Reloading...")
            cmd.load(target_pdb_path, target_internal_name)

        try:
            # Perform alignment
            aln = cmd.super(pdb_id, target_internal_name)
            matching_resi = aln[4]
            
            # Calculate threshold: 60% of target chain A length
            ref_ca_count = cmd.count_atoms(f"{target_internal_name} and chain A and polymer.protein and name CA")
            min_length = ref_ca_count * 0.4

            # if matching resi is too short, do not append rmsd result
            rmsd = aln[0]
            
            if matching_resi < min_length:
                print(f"Skipping {f}: too short atoms aligned ({matching_resi} < {min_length:.0f})")
                cmd.delete(pdb_id)
                continue
            
            results.append({
                "reference": pdb_id, 
                "target": os.path.basename(target_pdb_path).split('.')[0],
                "RMSD": round(rmsd, 3)
            })
            print(f"Aligned {pdb_id}: RMSD = {rmsd:.3f}")

        except Exception as e:
            print(f"Could not align {pdb_id}: {e}")
            results.append({"reference": pdb_id, "target": "N/A", "RMSD": "Error"})

        # Delete only the mobile object
        cmd.delete(pdb_id)

    # 3. Save to CSV
    target_name = os.path.splitext(os.path.basename(target_pdb_path))[0]
    # Define the final CSV path inside that folder
    output_csv = os.path.join(output_folder, f"{target_name}_RMSD.csv")
    # output_csv = os.path.join(output_folder, target_name, "_RMSD.csv")
    with open(output_csv, mode='w', newline='') as csvfile:
        fieldnames = ['reference', 'target', 'RMSD']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nDone! CSV saved to: {output_csv}")

# --- CONFIGURATION ---
# 1. Ensure your target protein is already loaded in PyMOL
# 2. Update the target_name to match the object name in PyMOL
settings_path = "./variables/settings.txt"
input_dir = "./pdb_clean/"
output_folder = "./prep_results"

batch_superimpose(input_dir, settings_path, output_folder)