import os
import pandas as pd
import re

def update_vina_variables(centroid_csv, variables_txt):
    if not os.path.exists(centroid_csv):
        print(f"Error: {centroid_csv} not found.")
        return

    # 1. Load the CSV and get the last row (centroid)
    df = pd.read_csv(centroid_csv)
    centroid_row = df.iloc[-1]
    
    # Ensure we actually have the centroid row
    if centroid_row['pdb_id'] != 'centroid':
        print("Error: Last row of CSV is not the calculated centroid.")
        return

    # Extract coordinates from the CSV
    new_vals = {
        'center_x': round(float(centroid_row['x']), 3),
        'center_y': round(float(centroid_row['y']), 3),
        'center_z': round(float(centroid_row['z']), 3)
    }

    # 2. Read the existing variables.txt
    if not os.path.exists(variables_txt):
        print(f"Error: {variables_txt} not found.")
        return

    with open(variables_txt, 'r') as f:
        lines = f.readlines()

    # 3. Update the lines using a flexible search
    new_lines = []
    for line in lines:
        updated = False
        for key in new_vals:
            # Matches 'center_x' or 'CENTER_X' with any amount of surrounding space
            if re.match(rf"^\s*{key}\s*=", line, re.IGNORECASE):
                new_lines.append(f"{key} = {new_vals[key]}\n")
                updated = True
                break
        if not updated:
            new_lines.append(line)

    # 4. Write back to variables.txt
    with open(variables_txt, 'w') as f:
        f.writelines(new_lines)

    print(f"Updated variables.txt: x={new_vals['center_x']}, y={new_vals['center_y']}, z={new_vals['center_z']}")

if __name__ == "__main__":
    # Internal paths based on your current workflow
    CENTROID_FILE = "./prep_results/unified_ligand_coords.csv"
    VARS_FILE = "./variables/variables.txt"
    
    update_vina_variables(CENTROID_FILE, VARS_FILE)