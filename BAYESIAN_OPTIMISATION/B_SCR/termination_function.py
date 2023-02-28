import pandas as pd
import numpy as np
from B_SCR.Acquisition_utilies import AcquisitionUtilities


def doe_termination_check(phasei=None,
                          df_path=None,
                          target=None):

    # ##SET TERMINATE TO FALSE THIS IS TO BE ASSESSED BASED ON DF RESULTS
    terminate = False
    # ##READ IN THE OUTPUT FILE
    df = pd.read_csv(df_path)
    # ##IF PHASES THEN LIMIT THE DATA CONSIDERED TO RELEVANT PHASE ONLY
    if phasei:
        # ##GET ONLY THE PHASE THAT YOU'RE CURRENTLY INVESTIGATING
        df = df[df['PHASE'] == phasei]
    min_mape = df[target].sort_values(ascending=True).iloc[0]
    # if min_mape <= 1.0:
    #     terminate = True
    return terminate

def termination_check(iterator=None,
                      df=None,
                      utility=None,
                      target=None):
    """
    FUNCTION TO DEFINE WHETHER SIMULATION SHOULD EXIT PRIOR TO MAXIMUM NUMBER OF ITERATIONS
    :param iterator: JOB ITERATOR NUMBER, COUNTING NUMBER OF MAIN JOBS (I.E. AFTER INTITAL JOBS)
    :param df: DICTIONARY OF RESULTS FOR ALL ITERATIONS TO DATE
    :param utility: CURRENT AQUISITION FUNCTION IN USE
    :param target: STRING REPRESENTING THE TARGET COLUMN UNDER CONSIDERATION
    :return:
    """

    terminate = False
    # ##MINIMUM MAPE
    min_mape = df[target].sort_values(ascending=True).iloc[0]
    curr_mape = df[target].iloc[-1]
    prev_mape = df[target].iloc[-2]

    curr_kappa = utility.kappa

    # # ###MAKE NEW KAPPA A FUNCTION OF MAPE
    # # ##if current mape is lower than previous mape and the mape is greater than 10
    # # ##then lower kappa by a function of the mape value
    # if (curr_mape < prev_mape) and curr_mape > 5:
    #     nkappa = curr_kappa - (curr_kappa * (curr_mape/100)) # ##LIMIT MAPE TO ZERO AND 1
    # # ##EVERY 20th increment should be exploratory
    # elif iterator % 20 == 0:
    #     nkappa = 2.5
    # # ##else if current mape is greater than previous mape but mape is greater than 5%
    # # ##set kappa to explore
    # elif (curr_mape > prev_mape) and (curr_mape > 5):
    #     nkappa = 2.5
    # # ##else if current mape is greater than previous iteration and mape is less than 5%
    # # ##increase kappa value by 20% from previous kappa
    # elif (curr_mape > prev_mape) and (curr_mape < 5):
    #     nkappa = nkappa * 1.2
    # # ##ROUND KAPPA SO THAT ITS A SINGLE DIGIT VALUE
    # if 'nkappa' in locals():
    #     if nkappa > 2.5:
    #         nkappa = 2.5
    #     elif nkappa < 0.5:
    #         nkappa = 0.5
    #     else:
    #         nkappa = np.round(nkappa, 2)

    # ###IF MAPE AT ANY POINT IS LESS THAN 3% EXIT THE OPTIMISER
    if min_mape <= 2.0:
        terminate = True
    try:
        utility = AcquisitionUtilities(aq_type="UCB", kappa=nkappa, xi=0)
    except:
        utility = AcquisitionUtilities(aq_type="UCB", kappa=2.500, xi=0)

    return terminate, df, utility
