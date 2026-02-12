import os
import csv
import glob
from pymol import cmd

def get_paths_automatically(results_base):
    """Automatically finds the _RMSD.csv file within the results folder."""
    # Search recursively for any file ending in _RMSD.csv
    search_pattern = os.path.join(results_base, "**", "*_RMSD.csv")
    files = glob.glob(search_pattern, recursive=True)
    
    if not files:
        return None
    # Returns the first matching RMSD file found
    return files[0]

def get_rmsd_threshold(settings_path):
    """Parses settings.txt to find the RMSD_CO= value."""
    try:
        with open(settings_path, 'r') as f:
            for line in f:
                if line.startswith("RMSD_CO="):
                    # Extract the value, remove whitespace, and convert to float
                    return float(line.split("=")[1].strip())
    except Exception as e:
        print(f"Warning: Could not read RMSD_CO from settings ({e}). Using default 2.0")
    return 2.0  # Default fallback

def inventory_top_matches(input_folder, cleaned_folder, output_folder, settings_path):


    # 1. Get threshold from settings
    rmsd_threshold = get_rmsd_threshold(settings_path)
    print(f"RMSD Cut-off Threshold: {rmsd_threshold}")

    # 2. Find the RMSD CSV
    rmsd_csv = get_paths_automatically(input_folder)

    top_pdb_ids = []
    try:
        with open(rmsd_csv, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rmsd_val = float(row['RMSD'])
                    if rmsd_val < rmsd_threshold:
                        top_pdb_ids.append(row['reference'])
                except (ValueError, TypeError):
                    continue
    except FileNotFoundError:
        print(f"Error: {rmsd_csv} not found.")
        return

    print(f"Found {len(top_pdb_ids)} proteins with RMSD < {rmsd_threshold}")

    # 2. Setup Ligand Inventory
    cmd.reinitialize()
    all_data = []
    
    # Metadata for categorization
    ions = ["MG", "CL", "NA", "K", "ZN", "MN", "CA"]
    buffers = ["SO4", "PO4", "EDT", "PEG", "DMS", "ACT", "GOL", "TRS"]

    # NEW: Track processed base names to avoid duplicates
    processed_ids = set()

    for pdb_id in top_pdb_ids:
        # Construct the file path (handles both .ent and .pdb)
        # Assuming the reference in CSV is the basename we created earlier
        file_path = None
        for ext in ['.ent', '.pdb']:
            temp_path = os.path.join(cleaned_folder, f"{pdb_id}{ext}")
            if os.path.exists(temp_path):
                file_path = temp_path
                break
        
        if not file_path:
            print(f"File for {pdb_id} not found in {cleaned_folder}")
            continue
                # Skip if we've already processed this ID (handles .ent vs .pdb)
        
        if pdb_id in processed_ids:
            print(f"Skipping duplicate: {file_path} (ID {pdb_id} already processed)")
            continue

        cmd.load(file_path, pdb_id)
        # Add to processed list after successful load
        processed_ids.add(pdb_id)

        # Identify all HETATMs (excluding water)
        myspace = {'ligands': []}
        cmd.iterate(f"({pdb_id} and hetatm and not solvent)", 
                    "ligands.append((resn, resi, chain))", space=myspace)
        
        unique_instances = set(myspace['ligands'])

        if not unique_instances:
            all_data.append({
                "pdb_id": pdb_id, "ligand_name": "NONE", "type": "N/A", "atom_count": 0
            })
        else:
            for resn, resi, chain in unique_instances:
                atom_count = cmd.count_atoms(f"{pdb_id} and chain {chain} and resi {resi} and resn {resn}")
                
                # Categorize
                if resn in ions:
                    l_type = "Ion"
                elif resn in buffers:
                    l_type = "Buffer/Reagent"
                else:
                    l_type = "Substrate/Analogue"

                all_data.append({
                    "pdb_id": pdb_id,
                    "ligand_name": resn,
                    "residue_id": resi,
                    "chain": chain,
                    "atom_count": atom_count,
                    "type": l_type
                })

        cmd.delete(pdb_id)

    # 3. Save filtered inventory
    # Define the final CSV path inside that folder
    output_csv = os.path.join(output_folder, "top_match_ligands_inventory.csv")
    with open(output_csv, mode='w', newline='') as csvfile:
        fieldnames = ['pdb_id', 'ligand_name', 'residue_id', 'chain', 'atom_count', 'type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Filtered inventory saved to {output_csv}")

# # --- CONFIGURATION ---
# prep_folder = "./prep_results"
# # rmsd_results = "../results/rmsd.csv"
# cleaned_dir = "./pdb_clean/"
# # final_output = "../results/top_match_ligands_inventory.csv"

# inventory_top_matches(prep_folder, cleaned_dir, prep_folder, settings_path)

if __name__ == "__main__":
    # Define your internal directory names here
    RESULTS_DIR = "./prep_results"
    CLEAN_DIR = "./pdb_clean"
    SETTINGS_FILE = os.path.join("variables", "settings.txt")
    
    inventory_top_matches(RESULTS_DIR, CLEAN_DIR, RESULTS_DIR, SETTINGS_FILE)
