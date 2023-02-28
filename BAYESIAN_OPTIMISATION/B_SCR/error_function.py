import os
import pandas as pd
import numpy as np
from scipy import interpolate
from scipy.signal import savgol_filter
from B_SCR.results_plots import plot_fvd_exp_v_sim
from B_SCR.plots import compare_sim_smooth
from B_SCR.general_functions import write_json_file




def mean_abs_pe(target, forecast):
    '''
    FUNCTION TO CALCULATE MEAN ABSOLUTE PERCENTAGE ERROR (MAPE)
    FOR THE ENTIRE DF
    '''
    # ##CALCULATE THE MAPE FOR EACH POINT IN THE SERIES
    series_mape = 100 * abs(((target - forecast) / target))
    # ##GET THE AVERAGE MAPE OVER THE SERIES SIZE
    total_mape = np.sum(series_mape) / series_mape.size
    return total_mape


def post_uts_mape(target=None, forecast=None):
	'''
	FUNCTION TO CALCULATE MEAN ABSOLUTE PERCENTAGE ERROR (MAPE).
	1. INTERPOLATION CAUSES FORECAST TO BE LONGER THAN TARGET SO WE REMOVE EXTRA DATA
	2. CALCULATE THE NORMALISED MAPE VALUE
	3. IDENTIFY WHERE SIMULATION RF IS LOWER THAN EXPERIMENTAL RF
	4. FOR POST UTS WE CALCULATE PERCENTAGE PENALTY BASED ON NUMBER OF CELLS WHERE RF IS LOWER
	5. CALCULATE THE MAPE FROM NORMALISED VALUES (WHOLE CURVE - SERIES MAPE)
	6. CALCULATE THE MAPE FOR THE SUMMED AND AVERAGED VALUES
	7. CALCULATE TOTAL MAPE BY ADDING PENALTY TO THE SUMMED MAPE.
	NOTE: CALCULATION CONFIRMED MANUALLY TO BE ACCURATE.
	'''
	# ##INTERPOLATION SOMETIMES RESULTS IN FORECAST LONGER THAN TARGET
	# ##DROP ANY ITEMS FROM FORECAST THAT EXCEED THE MAX OF TARGET
	forecast = forecast[:len(target)]
	# ##CALCULATE THE NORMALISED DIFFERENCE
	norm = (target - forecast) / target
	# ##FIND WHERE VALUES OF FORECAST ARE LESS THAN TARGET
	lower = np.where(forecast < target, True, False)
	# ##COUNT THE NUMBER OF CELLS IN POST WHERE TRUE
	count_post_low = np.count_nonzero(lower)
	# ##COUNT THE NUMBER OF CELLS IN THE POST ARRAY
	count_post = len(lower)
	# ##CALCULATE THE PENALTY PERCENTAGE
	try:
		percent_penalty = 100 * (count_post_low / count_post)
	except:
		percent_penalty = 0.0
	series_mape = 100 * abs(norm.dropna())
	# ##GET THE AVERAGE MAPE OVER THE SERIES SIZE
	sum_mape = np.sum(series_mape) / series_mape.size
	# ##ADD PENALTY TO TOTAL MAPE
	# total_mape = sum_mape + percent_penalty
	# ##NO PENALTY FACTOR
	total_mape = sum_mape
	return total_mape


def pre_uts_mape(target=None, forecast=None):
	'''
	FUNCTION TO CALCULATE MEAN ABSOLUTE PERCENTAGE ERROR (MAPE) PRE-UTS.
	1. CALCULATE THE NORMALISED MAPE VALUE
	2. CALCULATE THE MAPE FROM NORMALISED VALUES (WHOLE CURVE - SERIES MAPE)
	3. CALCULATE THE MAPE FOR THE SUMMED AND AVERAGED VALUES
	'''
	# ##CALCULATE THE NORMALISED DIFFERENCE
	norm = (target - forecast) / target
	series_mape = 100 * abs(norm.dropna())
	# ##GET THE AVERAGE MAPE OVER THE SERIES SIZE
	sum_mape = np.sum(series_mape) / series_mape.size
	return sum_mape


def split_df_by_uts(df=None, uts=None):
	""" FUNCTION TO RETURN DF VALUES UP TO UTS ONLY"""

	# ##FIND CLOSEST MATCH TO UTS FORCE
	ind = df['U'].sub(uts).abs().idxmin()
	pre = df[df.index <= ind]
	post = df[df.index >= ind]
	return pre, post


def interpolate_data(df, min_inc):
	''' FUNCTION TO INTERPOLATE DATA TO INCLUDE MINIMUM
	INCREMENT VALUE. RETURNS DF BASED ON INTERPOLATED VALUES.'''
	# ##REMOVE NON UNIQUE X VALUES
	df = df.drop_duplicates(subset=['U'])
	# ##IDENTIFY X, Y SERIES
	y = df['RF']
	x = df['U']
	# ##INTERPOLATE THE DATA
	func = interpolate.interp1d(x, y, kind='cubic')
	# ##EXTEND X SERIES TO HOST MINIMUM INCREMENT
	new_x = np.arange(x.values[0], x.values[-1], min_inc)
	# ##ESTIMATE Y VALUES FOR NEW X
	new_y = func(new_x)
	# ##CREATE NEW DF BASED ON NEW X/Y
	new_df = pd.DataFrame(np.column_stack((new_x, new_y)), columns=['U', 'RF']).drop_duplicates()
	# ##RETURN THE NEW DF
	return new_df


def pad_sim_data(exp_df=None, sim_df=None, pad_value='zeros'):
	""" FUNCTION TO PAD SIMULATED DATA SO THAT DISPLACEMENT OF SIMULATION
	REACHES SAME DISPLACEMENT SEEN IN EXPERIMENT.
	EXP_DF: EXPERIMENTAL DATAFRAME
	SIM_DF: SIMULATION DATAFRAME
	PAD_VALUE: FORCE VALUE TO BE PAD
	"""
	if pad_value == 'last':
		pvalue = sim_df['RF'].iloc[-1]
	elif pad_value == 'zeros':
		pvalue = 0.0
	# ##WE REALLY ONLY WANT TO PAD THE FORCE FUNCTION BUT THE DISPLACEMENT MUST REMAIN CONSISTANT WITH FORCE
	# ##PAD ROWS TO EXTEND TO SAME ARRAY SIZE AS EXPERIMENTAL DF
	pad_area = [(0, exp_df.shape[0] - sim_df.shape[0])]
	# ##DISP ARRAY LINEAR RAMP UP TO EXPERIMENTAL MAX
	new_disp = np.pad(sim_df['U'].to_numpy(),
					  pad_width=pad_area,
					  mode='linear_ramp',
					  end_values=exp_df['U'].iloc[-1])
	# ##PAD FORCE ARRAY
	new_force = np.pad(sim_df['RF'].to_numpy(),
					   pad_width=pad_area,
					   mode='constant',
					   constant_values=pvalue)
	# ##NEW DF FOR SIM
	sim_df = pd.DataFrame.from_dict({'RF': new_force,
									 'U': new_disp},
									orient='columns')
	return sim_df


def filter_exp_displacement(exp_df=None,
							delta_max=None):
	# ## LIMIT EXP DATA TO DELTA MAX
	limited_df = exp_df[exp_df['U'] <= delta_max]

	return limited_df


def explicit_filter_simdata(df=None,
							polyorder=3,
							deriv=0,
							mode='interp',
							jobname=None,
							paths=None):
	"""
	Function to smooth 1D array of data
	One key parameter is the window length this represents
	the size of the filter window. For 'interp' mode the window
	length must be <= size of array
	:param data: 1D array of data
	:param polyorder: Num of coefficients in polynominal default value is 3
	:param deriv: Int describing derivative solution. Default zero.
	:param mode: Type of extension used for padded signal. Default to interpolation (application of polynominal)
	:return: Smoothed array of values
	"""

	# ## GET SIZE OF DATA
	size = len(df)
	# ## GET WINDOW LENGTH BASED ON CHUNK SIZE
	wl = int(size / 20)
	# ##ENSURE WINDOW LENGTH IS ODD NUMBER
	if wl % 2 == 0:
		wl = wl + 1

	smooth = savgol_filter(x=df['RF'],
						   window_length=wl,
						   polyorder=polyorder,
						   deriv=deriv,
						   mode=mode)

	for i, s in enumerate(smooth):
		if s <= 0:
			smooth[i] = 0

	# ##CREATE DF OF SMOOTH RF
	sdf = df.copy()
	sdf['RF'] = smooth

	# ##PLOT EXTRAPOLATED AND SMOOTH DATA
	compare_sim_smooth(df1=df,
					   df2=sdf,
					   job_name=jobname,
					   paths=paths)
	return sdf


def read_sim_results(result_path=None,
					 exp_path=None,
					 uts_disp=None,
					 pad_value='zeros',
					 job_name=None,
					 **path_dic):
	''' READ SIMULATION FVD AND EXP FVD
	FIND MINIMUM INCREMENT IN EITHER SIMULATION OR EXP DATA
	FIT FORCE VALUES TO MINIMUM DISPLACEMENT INCREMENT.
	result_path: the filepath of the simulation results,
	exp_path: filepath for experimental results'''

	# ##READ SIMULATION DATA
	sim_df = pd.read_csv(os.path.join(result_path))
	# ##CONVERT SIM FORCE FROM NEWTONS TO KN
	sim_df['RF'] = sim_df['RF'] / 1000
	# ##READ EXPERIMENT DATA
	exp_df = pd.read_csv(exp_path, names=['U', 'RF'], skiprows=2)
	# ##FIND THE MINIMUM INCREMENT IN EITHER SIM_DF OR EXP_DF
	sim_inc = sim_df['U'].diff().replace(0, np.nan).min()
	exp_inc = exp_df['U'].diff().replace(0, np.nan).min()
	min_inc = round(min(sim_inc, exp_inc), 6)
	# ##INTERPOLATE THE FUNCTIONS USING SMALLEST INCREMENT
	sim_df = interpolate_data(sim_df, min_inc)
	exp_df = interpolate_data(exp_df, min_inc)
	####################################
	# EXTEND SIMULTATION TO EXPERIMENTAL DISPLACEMENT
	#####################################
	# ##IF DF HAVE DIFF DISPLACEMENTS APPEND PAD SIMULATED DATA
	if sim_df['U'].iloc[-1] <= exp_df['U'].iloc[-1]:
		sim_df = pad_sim_data(exp_df=exp_df,
							  sim_df=sim_df,
							  pad_value=pad_value)
	####################################
	# ## SMOOTH EXPLICIT DATA
	#####################################
	if 'EXPLICIT' in result_path:
		sim_df.to_csv(os.path.join(path_dic['curr_results'],
								   '%s_SIM_EXTRAP_NOSMOOTH.csv' % (job_name)), index=False)
		sim_df = explicit_filter_simdata(df=sim_df,
										 polyorder=3,
										 deriv=0,
										 mode='interp',
										 jobname=job_name,
										 paths=path_dic)
	# ##SAVE THE INTERPOLATED/EXTRAPOLATED DATA TO CSV
	sim_df.to_csv(os.path.join(path_dic['curr_results'],
							   '%s_SIM_EXTRAP.csv' % (job_name)), index=False)
	exp_df.to_csv(os.path.join(path_dic['curr_results'],
							   'EXP_EXTRAP.csv'), index=False)
	# ##ADD FILEPATH TO PATH DIC
	path_dic[job_name + '_fvd_extrap'] = os.path.join(path_dic['curr_results'], '%s_SIM_EXTRAP.csv' % (job_name))
	path_dic['exp_fvd_extrap'] = os.path.join(path_dic['curr_results'], 'EXP_EXTRAP.csv')
	#######################
	##CALCULATE SINGLE MAPE
	########################
	omape = mean_abs_pe(target=exp_df['RF'], forecast=sim_df['RF'])
	#######################
	##CALCULATE SPLIT MAPE
	########################
	# ##SPLIT THE DF BY UTS POSITION
	pre_sim, post_sim = split_df_by_uts(df=sim_df, uts=uts_disp)
	pre_exp, post_exp = split_df_by_uts(df=exp_df, uts=uts_disp)
	# ##CALCULATE THE MAPE
	mape1 = pre_uts_mape(target=pre_exp['RF'], forecast=pre_sim['RF'])
	mape2 = post_uts_mape(target=post_exp['RF'], forecast=post_sim['RF'])
	#######################
	##CALCULATE WEIGHTED MAPE
	########################
	# ##WEIGHT MAPE2 AS BEING THE MORE IMPORTANT OBJECTIVE
	avg_mape = np.mean([mape1, (2 * mape2)])

	# ##PLOT THE EXP AND SIM DATA SHOWING MAPE VALUES
	plot_fvd_exp_v_sim(exp_path=path_dic['exp_fvd_extrap'],
					   sim_path=path_dic[job_name + '_fvd_extrap'],
					   uts_disp=uts_disp,
					   mape1=mape1,
					   mape2=mape2,
					   job_name=job_name,
					   savepath=path_dic['curr_results'])

	return omape, mape1, mape2, avg_mape, path_dic
