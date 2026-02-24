import os
import argparse
from rcsbapi.search import TextQuery
import urllib.request

def download_from_rcsb(search_term, output_folder):
    # 1. Ensure output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created folder: {output_folder}")

    print(f'Searching RCSB for: "{search_term}"...')

    # 2. Perform the search
    # This searches the 'text' attribute which covers titles, abstracts, and descriptions
    query = TextQuery(value=search_term)
    
    # Executing the search and getting list of IDs
    results = list(query())
    
    if not results:
        print("No results found for that search term.")
        return
    
    num_found = len(results)
    print(f"\n[SEARCH RESULTS] Found {num_found} matches.")

    # 2. Interactive User Input
    print("-" * 30)
    print("Options:")
    print(" - Enter 'y' to download ALL results.")
    print(" - Enter a specific number (e.g., '10') to download the first X results.")
    print(" - Enter 'n' or any other key to cancel.")
    print("-" * 30)
    
    user_choice = input("Your choice: ").strip().lower()

    # 3. Determine how many to download
    if user_choice == 'y':
        ids_to_download = results
    elif user_choice.isdigit():
        limit = int(user_choice)
        ids_to_download = results[:limit]
    else:
        print("Download cancelled.")
        return

    total_to_process = len(ids_to_download)
    print(f"Processing {total_to_process} files...\n")

    count = 0
    for pdb_id in ids_to_download:
        # Standard PDB file URL
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        file_path = os.path.join(output_folder, f"{pdb_id}.pdb")
        
        if os.path.exists(file_path):
            print(f"[{pdb_id}] Already exists, skipping.")
            continue
            
        try:
            urllib.request.urlretrieve(url, file_path)
            print(f"[{pdb_id}] Downloaded successfully.")
            count += 1
        except Exception as e:
            print(f"[{pdb_id}] Failed to download: {e}")

    print(f"\nFinished! Downloaded {count} new files to {output_folder}")

def main():
    parser = argparse.ArgumentParser(description="Download PDBs via RCSB Text Search")
    parser.add_argument("query", help='Text to search for (e.g. "glucose oxidase")')
    parser.add_argument("--out", default="./pdb", help="Output directory (default: ./pdb)")
    
    args = parser.parse_args()
    download_from_rcsb(args.query, args.out)

if __name__ == "__main__":
    main()