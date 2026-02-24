import os
import csv
import shutil
import re
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


def select_best_receptor(results_dir, clean_dir, settings_path, receptor_out, reference_out):
    if not os.path.exists(receptor_out):
        os.makedirs(receptor_out)
    if not os.path.exists(reference_out):
        os.makedirs(reference_out)

    # 1. Setup paths and settings
    rmsd_csv = next((os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('_RMSD.csv')), None)
    inventory_csv = os.path.join(results_dir, "top_match_ligands_inventory.csv")
    ligand_str = get_setting(settings_path, "TARGET_LIGANDS")
    
    if not all([rmsd_csv, inventory_csv, ligand_str]):
        print("[ERROR] Required files or TARGET_LIGANDS setting missing.")
        return

    target_ligands = {l.strip() for l in ligand_str.split(',')}
    
    # 2. Identify PDBs that actually contain the target ligands [cite: 9]
    valid_pdb_ids = set()
    with open(inventory_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ligand_name'] in target_ligands:
                valid_pdb_ids.add(row['pdb_id'])

    # 3. Find the one with the lowest RMSD among those valid PDBs [cite: 5, 8]
    best_pdb = None
    lowest_rmsd = float('inf')

    with open(rmsd_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pdb_id = row['reference']
            rmsd_val = float(row['RMSD'])
            if pdb_id in valid_pdb_ids and rmsd_val < lowest_rmsd:
                lowest_rmsd = rmsd_val
                best_pdb = pdb_id

    # 4. Copy to receptor folder
    if best_pdb:
        if not os.path.exists(receptor_out):
            os.makedirs(receptor_out)
        
        src = os.path.join(clean_dir, f"{best_pdb}.pdb")
        dst = os.path.join(reference_out, f"{best_pdb}.pdb")
        dst2 = os.path.join(receptor_out, f"{best_pdb}.pdb")
        # A. Copy the original clean PDB to the reference folder
        shutil.copy2(src, dst)
        print(f"[INFO] Original clean PDB copied to: {dst}")

        # B. Use PyMOL to create a single-chain version for docking
        try:
            cmd.reinitialize()
            cmd.load(src, "best_receptor")
            
            # Identify the first chain
            chains = cmd.get_chains("best_receptor")
            if chains:
                first_chain = chains[0]
                
                # Remove everything except the first chain
                # This deletes other protein chains, ligands, ions, and water
                cmd.remove(f"best_receptor and organic")
                
                # Save the stripped structure to dst2
                cmd.save(dst2, "best_receptor")
                print(f"[SUCCESS] Cleaned receptor (Chain {first_chain} only) saved to: {dst2}")
            else:
                print(f"[ERROR] No chains found in {best_pdb}")
                
        except Exception as e:
            print(f"[ERROR] PyMOL cleaning failed: {e}")
        finally:
            cmd.delete("best_receptor")

        print(f"[SUMMARY] Best Receptor identified: {best_pdb} (RMSD: {lowest_rmsd})")
    else:
        print("[WARNING] No PDB found that matches both RMSD criteria and contains target ligands.")

    # 5. Update the lines using a flexible search
    with open(settings_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        updated = False
        if re.match(rf"^\s*REF_PDB\s*=", line, re.IGNORECASE):
                new_lines.append(f"REF_PDB={dst}\n")
                updated = True
        if not updated:
            new_lines.append(line)

    #6. Write back to settings.txt
    with open(settings_path, 'w') as f:
        f.writelines(new_lines)

    print(f"Updated settings.txt: REF_PDB={best_pdb}")

if __name__ == "__main__":
    select_best_receptor("./prep_results", "./pdb_clean", "./variables/settings.txt", "./receptor", "./reference")