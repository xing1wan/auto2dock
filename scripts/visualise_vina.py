import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

def visualize_batch_results(results_dir):

    if not os.path.exists(results_dir):
        print("Results directory not found.")
        return

    # # Create the master plots folder under results
    # plots_base_dir = os.path.join(results_dir, "receptor_plots")
    # if not os.path.exists(plots_base_dir):
    #     os.makedirs(plots_base_dir)
    #             # Create directory for plots if it doesn't exist
    # plot_dir = './plots'
    # if not os.path.exists(plot_dir):
    #     os.makedirs(plot_dir)

    # Find all receptor CSV files
    csv_files = [f for f in os.listdir(results_dir) if f.endswith('_docking_results.csv')]
    
    for results_file in csv_files:
        full_path = os.path.join(results_dir, results_file)
        receptor_name = results_file.replace('_docking_results.csv', '')

        # if not os.path.exists(results_file):
        #     print(f"Error: {results_file} not found. Please run the analysis script first.")
        if not os.path.exists(full_path):
            print(f"Error: {full_path} not found.")
        else:
            df = pd.read_csv(full_path)

            # 2. Setup Plotting Theme
            sns.set_theme(style="whitegrid")
            
            # Updated metrics based on the analysis script output columns
            metrics = ['affinity', 'radius_of_gyration', 'dist_to_centroid', 'dist_to_template']
            titles = [
                'Binding Affinity (kcal/mol)', 
                'Radius of Gyration (Å)', 
                'Dist. to Centroid (Å)', 
                'Dist. to Crystal Ref (Å)'
            ]

            # make subfolder for each receptor
            
            plot_sub = os.path.join(results_dir, receptor_name)
            if not os.path.exists(plot_sub):
                os.makedirs(plot_sub)

            # 3. Setup Boxplots/Strip-plots
            # We use 'ligand' as the x-axis to compare different substrates
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            axes = axes.flatten()

            for i, metric in enumerate(metrics):
                # Convert dist_to_template to numeric in case it has "N/A" strings
                if metric == 'dist_to_template':
                    df[metric] = pd.to_numeric(df[metric], errors='coerce')

                sns.boxplot(
                    data=df, 
                    x='ligand', 
                    y=metric, 
                    ax=axes[i], 
                    palette="Pastel1", 
                    showfliers=False
                )

                sns.stripplot(
                    data=df, 
                    x='ligand', 
                    y=metric, 
                    ax=axes[i], 
                    color=".25", 
                    alpha=0.6, 
                    jitter=0.2
                )

                axes[i].tick_params(axis='x', rotation=90) 
                axes[i].set_title(titles[i], fontsize=14, fontweight='bold')
                axes[i].set_xlabel('Ligand Substrate', fontsize=12)
                axes[i].set_ylabel('')
                

            plt.tight_layout()
            plt.savefig(f'{plot_sub}/vina_boxplot_analysis.png', dpi=300)
            print(f"Boxplots saved to {plot_sub}/vina_boxplot_analysis.png")

            # 4. Generate Residue Distribution Heatmap
            # This uses the 'contacts' column from your updated analysis script
            res_list = []
            for _, row in df.iterrows():
                if pd.notnull(row['contacts']):
                    # Split the comma-separated residues
                    for res in str(row['contacts']).split(','):
                        res_list.append({'ligand': row['ligand'], 'residue': res.strip()})

            if res_list:
                res_df = pd.DataFrame(res_list)
                # Create a frequency table (Residue vs Ligand)
                contact_matrix = res_df.groupby(['ligand', 'residue']).size().unstack(fill_value=0)

                # Filter for the top 20 most frequent residues to keep the heatmap readable
                top_res = res_df['residue'].value_counts().head(20).index
                contact_matrix_top = contact_matrix[top_res].T

                plt.figure(figsize=(12, 10))
                sns.heatmap(contact_matrix_top, annot=True, cmap="YlGnBu", cbar_kws={'label': 'Total Hits'})
                plt.title('Polar Contact Fingerprint per Ligand', fontsize=16, fontweight='bold')
                plt.ylabel('Amino Acid Residue')
                plt.xlabel('Ligand Substrate')
                plt.savefig(f'{plot_sub}/vina_residue_heatmap.png', dpi=300)
                print(f"Heatmap saved to {plot_sub}/vina_residue_heatmap.png")
            else:
                print("No contact data available to generate heatmap.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--R", required=True, help="Docking results directory containing csv files")
    args = parser.parse_args()

    # --- RUN ---
    visualize_batch_results(args.R)


if __name__ == "__main__":
    main()