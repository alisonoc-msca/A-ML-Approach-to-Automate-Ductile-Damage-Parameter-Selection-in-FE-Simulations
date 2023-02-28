import os
import pandas as pd
import numpy as np
from B_SCR.pandas_functions import get_unique_rows


def create_taguchi_array(fpth_tag_order=None,
                         fpth_results=None,
                         iter_dic=None,
                         fixed_dic=None,
                         iter_num=None,
                         phaseiter=None):
    """
    FUNCTION TO CREATE A TAGUCH ARRAY OF VALUES REMOVING NON-UNIQUE (ALREADY CONDUCTED)
    VIRTUAL EXPERIMENTS.
    fpth_tag_order = filepath to taguchi layout [csv file with 1's, 2's etc]
    results_df = read in results to date from 'OUTPUTS.csv'
    iter_dic = dictionary of k, v for iterable parameters
    fixed_dic = dictionary of k, v for fixed parameters
    iter_num: updated job counter
    phaseiter: phase of BO identifier
    :return: dataframe of iterable parameters (simulations to be conducted)
    pcomplete: list of simulation numbers already conducted relevant to this array.
    """
    # ##READ IN BLANK TAGUCHI ARRAY
    tag_df = pd.read_csv(fpth_tag_order)
    # ##ASS THE MAXIMUM LEVEL FOR EACH PARAMETER
    max_levels={}
    for k in iter_dic.keys():
        max_levels[k] = int(max(tag_df[k]))
    # ##CREATE A COPY OF THE TAGUCHI ARRAY FOR MODIFICATION
    ctag = tag_df.copy()
    # ##SET THE COLUMNS AS ITERABLE PARAMETER KEYS
    ctag.columns = iter_dic.keys()
    # ## CREATE DICTIONARY FOR MAPPING VALUES WHEN YOU HAVE UNKNOWN NUMBER OF LEVELS
    map_dic={}
    for k in iter_dic.keys():
        # ##USE BOUNDARYS TO ASSESS LEVELS
        min_bound = iter_dic[k][0]
        max_bound = iter_dic[k][1]
        # ##RANGE
        bound_rng = np.linspace(start=min_bound,
                                stop=max_bound,
                                num=max_levels[k])
        # ##CREATE DICTIONARY OF MAPPING VALUES
        for myi, val in enumerate(bound_rng):
            if not k in map_dic.keys():
                map_dic[k] = {int(myi + 1) : round(val, 4)}
            else:
                map_dic[k].update({int(myi + 1) : round(val, 4)})
    # ##MAP VALUES TO CTAG ARRAY
    for k in map_dic:
        ctag[k] = ctag[k].map(map_dic[k])
    # ##ADD THE FIXED DATA POINT TO THE CTAG DF
    if fixed_dic:
        for k, v in fixed_dic.items():
            ctag[k] = v
    # ##CHECK THAT SIMULATIONS IN CTAG ARE UNIQUE
    # ##READ IN RESULTS TO DATE
    results_df = pd.read_csv(fpth_results)
    # ## REMOVE IDENTICAL PARAMS ALREADY RUN CHANGE PHASE NUMBER IF RESULTS DATA MATCHES A NEW REQUESTED EXPERIMENT
    ctag, iter_num, pcomplete = get_unique_rows(df1=results_df,
                                                df2=ctag,
                                                iter_num=iter_num,
                                                phaseiter=phaseiter,
                                                export_path=fpth_results)
    if fixed_dic:
        # ##DROP NON ITERABLE PARAMETERS FROM CTAG
        ctag = ctag.drop(fixed_dic.keys(), axis=1)
    return ctag, iter_num, pcomplete
