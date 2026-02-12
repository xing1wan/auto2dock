import os
import csv
import glob
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

def extract_glucose_with_centroid(inventory_csv, cleaned_folder, settings_path, output_folder):
    # Ensure the output directory exists!
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    cmd.reinitialize()
    ligand_string = get_setting(settings_path, "TARGET_LIGANDS")
    target_ligands = {l.strip() for l in ligand_string.split(',')}
    target_pdb_path = get_setting(settings_path, "TARGET")

    if not target_pdb_path or not os.path.exists(target_pdb_path):
        print(f"Error: Target path not found.")
        return
    
    glucose_targets = []
    if not os.path.exists(inventory_csv):
        print(f"Error: Inventory CSV {inventory_csv} not found.")
        return

    with open(inventory_csv, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ligand_name'] in target_ligands:
                glucose_targets.append({
                    'pdb_id': row['pdb_id'], 
                    'resn': row['ligand_name'], 
                    'resi': row['residue_id'], 
                    'chain': row['chain']
                })
    
    cmd.load(target_pdb_path, "REF_TARGET")
    final_results = []

    for entry in glucose_targets:
        pdb_id = entry['pdb_id']
        file_path = os.path.join(cleaned_folder, f"{pdb_id}.pdb")
        
        if os.path.exists(file_path):
            cmd.load(file_path, pdb_id)
            # Align to target to get unified coordinates
            aln = cmd.super(pdb_id, "REF_TARGET")
            rmsd = aln[0]
            
            # Calculate Centroid of the specific ligand
            sel = f"{pdb_id} and chain {entry['chain']} and resi {entry['resi']} and resn {entry['resn']}"
            coords = cmd.get_coords(sel, 1)
            if coords is not None:
                avg_coords = coords.mean(axis=0)
                final_results.append({'pdb_id': pdb_id, 'coords': avg_coords, 'rmsd': round(rmsd, 3)})
            
            cmd.delete(pdb_id)

    if not final_results:
        print("No valid ligand coordinates found.")
        return

    # Calculate Global Centroid
    final_x = sum(r['coords'][0] for r in final_results) / len(final_results)
    final_y = sum(r['coords'][1] for r in final_results) / len(final_results)
    final_z = sum(r['coords'][2] for r in final_results) / len(final_results)

    # Save to CSV
    output_csv = os.path.join(output_folder, "unified_ligand_coords.csv")
    with open(output_csv, mode='w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['pdb_id', 'x', 'y', 'z', 'RMSD'])
        writer.writeheader()
        for r in final_results:
            writer.writerow({
                'pdb_id': r['pdb_id'], 
                'x': round(r['coords'][0], 3), 
                'y': round(r['coords'][1], 3), 
                'z': round(r['coords'][2], 3), 
                'RMSD': r['rmsd']
            })
        writer.writerow({
            'pdb_id': "centroid", 
            'x': round(final_x, 3), 
            'y': round(final_y, 3), 
            'z': round(final_z, 3), 
            'RMSD': "NA"
        })
    print(f"Success! Coordinates saved to {output_csv}")

if __name__ == "__main__":
    # Internal paths to match your workflow
    RESULTS_DIR = ".\prep_results"
    CLEAN_DIR = ".\pdb_clean"
    SETTINGS = os.path.join("variables", "settings.txt")
    INVENTORY = os.path.join(RESULTS_DIR, "top_match_ligands_inventory.csv")
    
    extract_glucose_with_centroid(INVENTORY, CLEAN_DIR, SETTINGS, RESULTS_DIR)