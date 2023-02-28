import os
import numpy as np
import math as m
import pandas as pd
from sklearn.linear_model import LinearRegression

def extend_new_slope(cslope=None,
					 mat_dic=None,
					 jobnum=None,
					 path_dic=None):
	"""
	[5/9/22]
	BASED ON PROJECT MATERIAL_ANALYSIS FILE MATERIAL_CHECK.PY LINES 168-193
	PURPOSE IS TO USE KNOWN INTERPOLATED TRUE STRAIN-TRUE STRESS (UP TO UTS POINT)
	AND EXTEND BEYOND UTS POSITION FOR ANY GIVEN 'M' VALUE THAT HAS NOT PREVIOUSLY
	BEEN ASSESSED.
	NECESSARY BECAUSE BAYESIAN OPTIMISATION WILL EVENTUALLY USE 'M' PARAMETER VALUES
	THAT EXIST OUTSIDE THE 50 MPA INCREASES MANUALLY ASSESSED IN PREVIOUS WORK.
	fpath_ts: FILE PATH TO CSV FILE OF INTERPOLATED TRUE STRAIN-TRUE STRESS UP TO UTS
	cslope: CURRENT SLOPE VALUE BEING ASSESSED (M)
	mat_dic: DICTIONARY OF PREVIOUSLY ASCERTAINED MATERIAL PROPERTIES
	jobnum: COUNTER FOR JOB NUMBER
	pathdic: DICTIONARY OF RELEVANT FILE PATHS
	"""
	# ##REMOVE SLOPES KEYWORD IF IN MATDIC
	mat_dic.pop('SLOPE', None)
	# ##CALCULATE Y INTERCEPT
	c = mat_dic['TRUE_STRESS'] - (cslope * mat_dic['TRUE_STRAIN'])
	# ##READ IN TRUE STRESS-TRUE STRAIN DATA
	df = pd.read_csv(mat_dic['TRUE_TO_UTS'])
	# ##SET STRAIN RANGE TO BE AT LEAST 1000 ELEMENTS IN SIZE
	estrain = np.linspace(df['TRUE_STRAIN'].iloc[-1] + 1e-4, 2, num=1000).reshape(-1, 1)
	estress = (cslope * estrain) + c
	# ##COMBINE ORIGINAL AND EXTENDED DATA TO GET THE FULL MATERIAL PROPERTIES FOR ABAQUS
	df = pd.DataFrame(data={'TRUE_STRAIN': np.concatenate((df['TRUE_STRAIN'].values, estrain.flatten()), axis=0),
							'TRUE_STRESS': np.concatenate((df['TRUE_STRESS'].values, estress.flatten()), axis=0)})
	# ##ABAQUS REQUIRES STRAIN AND STRESS TO START FROM YIELD POSITION
	# ## WE NEED TO MODIFY THE TRUE STRESS - TRUE STRAIN TO TRUE STRESS - PLASTIC STRAIN
	plastic = df[df['TRUE_STRESS'] >= mat_dic['SIGMA_Y']].copy()
	# ##MODIFY STRAIN TO BE ZERO AT YIELD STRESS
	plastic['PLASTIC_STRAIN'] = plastic['TRUE_STRAIN'] - (plastic['TRUE_STRESS'] / mat_dic['E'])
	# ##RESET STRAIN TO BE ZERO AT YIELD
	plastic['PLASTIC_STRAIN'] = plastic['PLASTIC_STRAIN'] - plastic['PLASTIC_STRAIN'].iloc[0]
	# ##REPLACE ANY NEGATIVE STRAINS WITH VERY LOW STRAIN
	plastic['PLASTIC_STRAIN'] = np.where(plastic['PLASTIC_STRAIN'] < 0, 1E-20, plastic['PLASTIC_STRAIN'])
	# ##DROP TRUE STRAIN
	plastic.drop('TRUE_STRAIN', axis=1, inplace=True)
	# ##SAVE ABAQUS DATA TO CSV FILE
	fpath = os.path.join(path_dic['curr_results'], 'ABA_JOB%s.csv'
						 % (str(int(jobnum))))
	plastic.to_csv(fpath, index=False)
	# ##ADD PATH TO MAT_DIC
	mat_dic['SLOPE']=cslope
	mat_dic['plastic_properties']=fpath
	return mat_dic