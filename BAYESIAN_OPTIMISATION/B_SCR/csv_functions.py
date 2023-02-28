import os
import csv
import pandas as pd
import numpy as np


def rate_of_change(i, headers, today, bayes_dic, **path_dic):
    # ##CONVERT DIC TO DF
    df = pd.DataFrame.from_dict(bayes_dic, orient='columns')
    # ##CALCULATE RATE OF CHANGE FOR 3 PREVIOUS ITERATIONS AND FROM BEGINNING
    df['ROC_BEGIN'] = ((df['MAPE'] - df['MAPE'].iloc[0]) /
                       (df['JOB_NUM'] - df['JOB_NUM'].iloc[0]))
    df['ROC_THREE'] = ((df['MAPE'] - df['MAPE'].shift(2)) /
                       (df['JOB_NUM'] - df['JOB_NUM'].shift(2)))
    # ##UPDATE BAYES DIC
    new_dic = df.to_dict('list')
    if i == 0:
        init_dic_csv(os.path.join(path_dic['curr_results'], 'OUTPUTS_' + today + '.csv'),
                 new_dic)
    else:
        append_data(path_dic['output_results'], headers, df.iloc[-1])
    # ##CONVERT BACK TO DIC FOR POSTERITY
    return new_dic, path_dic


def init_data_storage(path, headers):
    with open(path, 'w+', newline="") as csvfile:
        filewriter = csv.writer(csvfile)
        filewriter.writerow(headers)
        csvfile.close()


def append_data(path, headers, dic):
    """
    APPEND DATA TO EXISTING CSV FILE
    :param path: path to file
    :param headers: column headers, note: used to track DIC values
    :param dic: dictionary of current values
    :return: nothing
    """
    with open(path, 'a', newline="") as csvfile:
        filewriter = csv.writer(csvfile)
        # ##ROW IS WRITTEN IN ORDER OF HEADERS
        filewriter.writerow([dic.get(h, None) for h in headers])
        csvfile.close()

def overwrite_data(path, headers, dic):
    with open(path, 'w', newline="") as csvfile:
        filewriter = csv.writer(csvfile)
        # ##ROW IS WRITTEN IN ORDER OF HEADERS
        filewriter.writerow([dic.get(h, None) for h in headers])
        csvfile.close()

def init_dic_csv(path, dic):
    with open(path, 'w+', newline="") as csvfile:
        writer = csv.writer(csvfile)
        keys = dic.keys()
        writer.writerow(keys)
        writer.writerows(zip(*[dic[k] for k in keys]))