import pandas as pd
import glob, os

from res_type_parsers import res_to_func_dict

import ipdb


# Get a list of results
results_dir = '../results/'
res_files = glob.glob(os.path.join(results_dir, '*.txt'))
output_dir = '../results/parsed_results/'
os.makedirs(output_dir, exist_ok=True)

# Get unique result types by parsing the file names
# All file names have the format:
# <result_type>_<model_name>_<result_type>.txt
base_names = [os.path.basename(f) for f in res_files]
split_names = [f.split('_', 2) for f in base_names]

res_types = [r[0] for r in split_names]
model_types = [r[1] for r in split_names]
out_types = [r[2].replace('.txt', '') for r in split_names]

unique_res_types = set(res_types)
res_df_dict = {res_type: [] for res_type in unique_res_types}

# Read in the results
# We store each result type in a separate dataframe for parsing later
for res_file, res_type, model_type, out_type in zip(res_files, res_types, model_types, out_types):
    # Read the results
    res_df = pd.read_csv(res_file, sep='\t')

    # Add columns for all of the metadata
    res_df['modelname'] = model_type
    res_df['out_type'] = out_type

    res_df_dict[res_type].append(res_df)


# Concatenate the results for each result type into a single dataframe
for res_type, res_df_list in res_df_dict.items():
    res_df_dict[res_type] = pd.concat(res_df_list)

# Parse the results
for res_type, res_df in res_df_dict.items():
    # Get the parsing function for this result type
    parse_func = res_to_func_dict[res_type]

    # Parse the results
    parsed_res = parse_func(res_df)

    # Write the parsed results to a file
    parsed_res.to_csv(os.path.join(output_dir, f'{res_type}_parsed-averages.txt'), sep='\t')


ipdb.set_trace() 