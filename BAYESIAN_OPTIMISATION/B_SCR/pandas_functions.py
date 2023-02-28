import os
import numpy as np
import pandas as pd

def get_unique_rows(df1=None,
					df2=None,
					iter_num=None,
					phaseiter=None,
					export_path=None):
	"""
	COMPARE TWO DATAFRAMES
	IF ROW IN DF2 MATCHES A ROW IN DF1
	DELETE THE ROW IN DF2
	:param df1: DF BEING COMPARED TO
	:param df2: DF BEING MODIFIED
	:param iter_num: job counter
	:param phaseiter: phase of BO identifier
	:param export_path: filepath (inc name) to save updated df
	:return: MODIFIED DF2, updated job counter, list of jobs numbers already completed associated with this array
	"""
	# # ## ROUND BOTH DICTIONARIES TO FIVE SIGNIF DIGITS
	df1 = round(df1, 5)
	df2 = round(df2, 5)
	# ##GET ORIGINAL COLUMN ORDER
	ocol = df2.columns
	# ##REORDER DF2 COLUMNS
	df2.columns = ['Q1', 'Q2', 'Q3', 'EN', 'SN', 'FN', 'F', 'M']
	# ##INNER JOIN TO GET ROWS THAT APPEAR IN BOTH. USE INDEX FROM DF2
	both = pd.merge(df1, df2, how='inner')
	# ##IF BOTH NOT EMPTY THEN WE NEED TO ADJUST BOTH TO REMOVE DATA ALREADY ASSESSED
	if not both.empty:
		# ##FIND ROW WITH PHASE NUMBER DIFFERENT TO CURRENT PHASE NUMBER
		# ##GET THE JOB NUMBERS MODIFY DF1 AND EXPORT
		# ##(NEED TO UPDATE THE PHASE NUMBER TO REGISTER THIS DATA IN THE OPTIMISER)
		if phaseiter:
			update_rows = both[both['PHASE'] != phaseiter]['JOB_NUM'].values
			# ##SEARCH DF1 FOR ROWS WHERE THESE JOB NUMBERS ARE TRUE AND REPLACE THE PHASE VALUE
			df1['PHASE'] = np.where(df1['JOB_NUM'].isin(update_rows), int(phaseiter), df1['PHASE'])
		# ##EXPORT EXISTING RESULTS CSV
		df1.to_csv(export_path, index=False)
		# ##UPDATE BOTH DF TO UPDATE PHASE NUMBER CHANGES FROM ORIGINAL
		both = pd.merge(df1, df2, how='inner')
	# ##NOTE: 'JOB_NUM' IS LIST OF JOBS ALREADY DONE ASSOCIATED WITH THIS TAGUCHI ARRAY
	dic = both.to_dict('list')
	# ##BOOLEAN SHOWING ROWS WHERE VALUES MATCH
	df3 = df2.isin(dic)
	# ##FIND WHERE ALL VALUES IN ROW ARE TRUE AND GET INDEX VALUES
	true = df3[df3.all(axis='columns')].index
	final = df2.copy().drop(true)
	final = final.reset_index(drop=True)
	# ##TRANSFORM FINAL TO THE CORRECT COLUMN ORDER
	final.columns = ocol
	if final.empty:
		iter_num = len(df1)
	else:
		iter_num = iter_num + len(true)
	return final, iter_num, dic['JOB_NUM']

