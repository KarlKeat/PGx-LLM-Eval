import pandas as pd
import ipdb


# Functions to parse each of the results types (P2G, D2P, etc.)
# Each of these will return values for each LLM
# and each output type ("unk_results" or "results")
# All of the res_dfs are assumed to be the same format as those
# output by the test run scripts with two additional columns
# indicating the model name ('modelname') and the output type ('out_type')



def parse_from_col(res_df, col_name):
    """
    Generic parsing function that takes a column name
    and returns results for that column
    """
    mean_val = res_df.groupby(['modelname', 'out_type'])[col_name].mean()
    std_val = res_df.groupby(['modelname', 'out_type'])[col_name].std()

    mean_val.rename(f'{col_name}_mean', inplace=True)
    std_val.rename(f'{col_name}_std', inplace=True)

    return pd.concat([mean_val, std_val], axis=1)


def parse_p2g(res_df):
    """
    Phenotype to Guideline (P2G) parsing function
    Results for P2G have many columns, three for each of the
    scoring methods (BERTScore, BLEU, etc.) comparing the 
    LLM answer to concurring, reference, and incorrect recommendations
    """
    # Average of all the columns
    # (useful since this is what we want for GPT4 at least)
    metric_cols = [col for col in res_df.columns if 'vs' in col.lower()]

    metric_dfs = []

    for metric_col in metric_cols:
        metric_res = parse_from_col(res_df, metric_col)
        metric_dfs.append(metric_res)

    all_metric_df = pd.concat(metric_dfs, axis=1)


    # Add in approach for parsing P2G results
    # by finding the "win rate" - aka
    # how often the LLM's answer was more similar to the reference
    # than to the discordant answer

    # Get unique scoring aproaches in metrics columns
    unique_scorers = [mname.split('_llm_')[0] for mname in metric_cols]
    unique_scorers = sorted(list(set(unique_scorers)))

    # Hack - remove the gpt4 scorer since it's not a standard scorer
    # and what we'd want to do is covered in its "mean" function
    unique_scorers = [scorer for scorer in unique_scorers if 'gpt4' not in scorer]


    # Function to compute the win rate for a given scorer
    # grouped by modelname and out_type
    def calc_win_rate(scorer_name, results_df, col_1="llm_vs_ref", col_2="llm_vs_discordant"):
        results_df_gb = results_df.groupby(['modelname', 'out_type'])

        def win_rate_func(group, scorer_name=scorer_name, col_1=col_1, col_2=col_2):
            wins = (group[f"{scorer_name}_{col_1}"] >= group[f"{scorer_name}_{col_2}"])
            return pd.Series({f'{scorer_name}_winrate_mean': wins.mean(), 
                              f'{scorer_name}_winrate_std': wins.std()})

        llm_winrates = results_df_gb.apply(win_rate_func)

        return llm_winrates
    
    # Calculate win rates for each scorer
    winrate_dfs = [calc_win_rate(scorer, res_df) for scorer in unique_scorers]
    winrate_dfs = pd.concat(winrate_dfs, axis=1)

    return pd.concat([winrate_dfs, all_metric_df], axis=1)


def parse_score(res_df):
    """
    Generic parsing function for all results
    that have a singular score column
    Just wraps `parse_from_col`
    """
    return parse_from_col(res_df, 'score')


def parse_prec_recall(res_df):
    """
    Generic parsing function for all results
    that have a precision and recall column
    Just wraps `parse_from_col` twice and concatenates
    """
    prec_res = parse_from_col(res_df, 'precision')
    recall_res = parse_from_col(res_df, 'recall')

    return pd.concat([prec_res, recall_res], axis=1)
    

def parse_d2g(res_df):
    """
    Drug to Gene (D2G) parsing function
    Results for D2G use precision and recall
    BUT they also have a "mode" column
    that indicates whether the question was asked as
    a researcher or clinician, so we need to stratify
    for that as well
    """
    unique_modes = res_df['mode'].unique()

    mode_dfs = []

    for mode_name in unique_modes:
        mode_df = res_df[res_df['mode'] == mode_name]
        mode_res = parse_prec_recall(mode_df)
        mode_res['mode'] = mode_name
        mode_res = mode_res.set_index('mode', append=True)

        mode_dfs.append(mode_res)

    return pd.concat(mode_dfs)


def parse_refusal(res_df):
    """
    Refusal parsing function
    Results for Refusal operate with two columns
    "refused" and "refused_no_opt_out"
    where we will just take the means of those columns
    with two additional grouping columns
    of "category" and "is_misspecified"
    """
    unique_cat_misspec_combos = res_df.groupby(['category', 'is_misspecified']).groups.keys()

    combo_dfs = []

    for combo_tuple in unique_cat_misspec_combos:
        cat, misspec = combo_tuple

        combo_df = res_df[(res_df['category'] == cat) & (res_df['is_misspecified'] == misspec)]
        combo_res_opt = parse_from_col(combo_df, 'refused')
        combo_res_noopt = parse_from_col(combo_df, 'refused_no_opt_out')

        combo_res = pd.concat([combo_res_opt, combo_res_noopt], axis=1)

        combo_res['category'] = cat
        combo_res['is_misspecified'] = misspec
        combo_res = combo_res.set_index('category', append=True)
        combo_res = combo_res.set_index('is_misspecified', append=True)

        combo_dfs.append(combo_res)

    return pd.concat(combo_dfs)




# Dict that maps strings to functions
res_to_func_dict = {
    'PhenoToGuideline': parse_p2g,
    'DiplotypeToPhenotype': parse_score,
    'AlleleFunction': parse_score,
    'AlleleFrequency': parse_score,
    'PhenoToCategory': parse_score,
    'DrugToGenes': parse_d2g,
    'GeneToDrugs': parse_prec_recall,
    'AlleleDefinition': parse_prec_recall,
    'Refusal': parse_refusal,
}