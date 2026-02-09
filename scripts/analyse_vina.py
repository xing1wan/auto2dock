import argparse
import os
import math
import csv
from pymol import cmd

def get_centroid_from_file(var_file):
    """Parses your variables.txt to extract the centroid coordinates."""
    # Assuming variables.txt has lines like: center_x = -0.559
    coords = {}
    with open(var_file, 'r') as f:
        for line in f:
            if '=' in line:
                key, val = line.split('=')
                coords[key.strip()] = float(val.strip())
    return (coords['center_x'], coords['center_y'], coords['center_z'])

def batch_analyze_vina(output_parent_dir, receptor_pdb_dir, crystal_template_path, centroid_coords, results_base_dir):
    """
    output_parent_dir: The 'output' folder from your .bat script
    receptor_pdb_dir: The 'receptor' folder containing original .pdb files
    crystal_template_path: Path to your reference crystal structure
    """

    cx, cy, cz = centroid_coords

    if not os.path.exists(results_base_dir):
        os.makedirs(results_base_dir) 
    
    # 1. Scan the output directory for receptor subfolders
    if not os.path.exists(output_parent_dir):
        print(f"Error: Output directory {output_parent_dir} not found.")
        return

    subfolders = [f.path for f in os.scandir(output_parent_dir) if f.is_dir()]
    print(f"Found {len(subfolders)} receptor folders. Starting analysis...\n")

    for folder in subfolders:
        master_results = []
        try:
            cmd.reinitialize()
            receptor_name = os.path.basename(folder)
            
            # Find the original PDB receptor for alignment (DOCK_PROT)
            # We look for ReceptorName.pdb in the receptor_pdb_dir
            ref_prot_path = os.path.join(receptor_pdb_dir, receptor_name + ".pdb")
            if not os.path.exists(ref_prot_path):
                print(f"Skipping {receptor_name}: Original PDB not found at {ref_prot_path}")
                continue

            # Identify all docked ligand files (*_out.pdbqt)
            dock_files = [f for f in os.listdir(folder) if f.endswith('_out.pdbqt')]
            if not dock_files:
                print(f"No docking results found in {receptor_name} folder.")
                continue

            # Load Receptor and Template for alignment
            cmd.load(ref_prot_path, "DOCK_PROT")
            cmd.load(crystal_template_path, "CRYSTAL_TEMPLATE")
            cmd.super("CRYSTAL_TEMPLATE", "DOCK_PROT")
            cmd.remove("hydrogens")

            # Identify the reference ligand in the Template (Looking for 12 or 16 atoms)
            myspace = {'ligands': []}
            cmd.iterate("CRYSTAL_TEMPLATE and hetatm", "ligands.append((resn, resi))", space=myspace)
            template_lig_sel = None
            for resn, resi in set(myspace['ligands']):
                if cmd.count_atoms(f"CRYSTAL_TEMPLATE and resi {resi} and resn {resn}") in [12, 16]:
                    template_lig_sel = f"CRYSTAL_TEMPLATE and resi {resi} and resn {resn}"
                    break

            if not template_lig_sel:
                print(f"Warning: No valid reference ligand found in template for {receptor_name}.")
                tx, ty, tz = (0, 0, 0) # Fallback if no template ligand
            else:
                t_coords = cmd.get_coords(template_lig_sel, 1)
                tx = sum(p[0] for p in t_coords) / len(t_coords)
                ty = sum(p[1] for p in t_coords) / len(t_coords)
                tz = sum(p[2] for p in t_coords) / len(t_coords)

            # Process each docked ligand file in this receptor folder
            for dock_file in dock_files:
                ligand_name = dock_file.replace(f"{receptor_name}_", "").replace("_out.pdbqt", "")
                vina_path = os.path.join(folder, dock_file)

                # Extract Affinities from PDBQT Remarks
                affinities = []
                with open(vina_path, 'r') as f:
                    for line in f:
                        if "REMARK VINA RESULT" in line:
                            affinities.append(float(line.split()[3]))

                # Load poses into PyMOL
                obj_name = f"lig_{ligand_name}"
                cmd.load(vina_path, obj_name)
                cmd.split_states(obj_name)
                cmd.delete(obj_name)
                
                poses = cmd.get_object_list(f"{obj_name}_*")
                for i, pose in enumerate(poses):
                    # Get ligand residues
                    pose_space = {'names': []}
                    cmd.iterate(pose, "names.append(resn)", space=pose_space)
                    if not pose_space['names']: continue
                    resn_p = pose_space['names'][0]

                    # Centroid and Stats
                    p_coords = cmd.get_coords(pose, 1)
                    if p_coords is not None:
                        px = sum(p[0] for p in p_coords) / len(p_coords)
                        py = sum(p[1] for p in p_coords) / len(p_coords)
                        pz = sum(p[2] for p in p_coords) / len(p_coords)
                        
                        dist_cent = math.sqrt((px-cx)**2 + (py-cy)**2 + (pz-cz)**2)
                        dist_temp = math.sqrt((px-tx)**2 + (py-ty)**2 + (pz-tz)**2) if template_lig_sel else "N/A"
                        rg = math.sqrt(sum((p[0]-px)**2 + (p[1]-py)**2 + (p[2]-pz)**2 for p in p_coords) / len(p_coords))
                        
                        # Polar Contacts
                        contact_space = {'residues': []}
                        cmd.iterate(f"byres (DOCK_PROT within 3.5 of {pose})", 
                                    "residues.append(f'{resn}{resi}')", space=contact_space)
                        unique_res = sorted(list(set(contact_space['residues'])), key=lambda x: int(''.join(filter(str.isdigit, x))))
                        polar_res = ", ".join(unique_res)

                        master_results.append({
                            "receptor": receptor_name,
                            "ligand": ligand_name,
                            "pose": i + 1,
                            "affinity": affinities[i] if i < len(affinities) else "N/A",
                            "dist_to_centroid": round(dist_cent, 3),
                            "dist_to_template": round(dist_temp, 3) if isinstance(dist_temp, float) else "N/A",
                            "radius_of_gyration": round(rg, 3),
                            "contacts": polar_res
                        })
                cmd.delete(f"{obj_name}_*")
            print(f"Processed: {receptor_name}")

            # Save to CSV
            if master_results:
                csv_name = f"{receptor_name}_docking_results.csv"
                csv_path = os.path.join(results_base_dir, csv_name)
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=master_results[0].keys())
                    writer.writeheader()
                    writer.writerows(master_results)
                print(f"\nAnalysis complete. Results saved to {csv_path}")
        
        except Exception as e:
            print(f"Error processing folder {folder}: {e}")
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--o", required=True, help="Output parent directory")
    parser.add_argument("--r", required=True, help="Receptor PDB directory")
    parser.add_argument("--t", required=True, help="Template PDB path")
    parser.add_argument("--R", required=True, help="Results base directory")
    parser.add_argument("--var", required=True, help="Path to variables.txt")
    args = parser.parse_args()

    # Extract centroid from the file passed in the --var argument
    MY_CENTROID = get_centroid_from_file(args.var)
    
    # Use args.o, args.r, etc., in your existing analysis logic...
    batch_analyze_vina(args.o, args.r, args.t, MY_CENTROID, args.R)

if __name__ == "__main__":
    main()