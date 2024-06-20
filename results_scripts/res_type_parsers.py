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
    # TODO: figure out how we're supposed to make use of this triangular
    # setup for columns/scores in the results
    # For now, just take the average of all of the columns 
    # (hacky way of iding columns for now)

    metric_cols = [col for col in res_df.columns if 'vs' in col.lower()]

    # TODO: remove this hack to short-circuit the tensor bug temporarily
    metric_cols = [col for col in metric_cols if res_df[col].dtype != 'object']
    import warnings
    warnings.warn(Warning("The tensor bug for P2G results has been short-circuited."))

    metric_dfs = []

    for metric_col in metric_cols:
        metric_res = parse_from_col(res_df, metric_col)
        metric_dfs.append(metric_res)

    return pd.concat(metric_dfs, axis=1)


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
}