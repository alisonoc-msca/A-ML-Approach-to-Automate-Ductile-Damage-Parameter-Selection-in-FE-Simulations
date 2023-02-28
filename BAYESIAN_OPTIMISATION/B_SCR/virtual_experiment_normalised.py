import os
import pandas as pd
import numpy as np
from B_SCR.abaqus_functions import FEA_Function
from B_SCR.clean_fea_dir import delete_unwanted
from B_SCR.csv_functions import append_data
from B_SCR.material_properties import extend_new_slope
from B_SCR.general_functions import merge_dicts, write_json_file, load_json_file, read_sim_time, set_optimiser_target
from B_SCR.error_function import read_sim_results
from B_SCR.termination_function import doe_termination_check, termination_check
from B_SCR.results_plots import plot_energy

def virtual_experiment_from_array(recalc_mape=None,
								  phasei=None,
								  target=None,
								  inc_num=None,
								  completed_jobs=None,
								  optimizer=None,
								  df=None,
								  pdata=None,
								  iter_dic=None,
								  aba_dic=None,
								  slope_dic=None,
								  csv_head=None,
								  scaler=None,
								  path_dic=None):
	"""" FUNCTION TO RUN VIRTUAL EXPERIMENT FROM DATAFRAME OF POINTS
	TYPICALLY USED FOR DOE EXPERIMENTS
	recalc_mape: Boolean whether to recalculate MAPE
	phasei: counter for phase (identify section of code)
	target: the MAPE to be targeted (MAPE1 or MAPE2)
	inc_num: counter for job number
	completed_jobs: list of jobs previously completed (odbs available)
	optimizer: current optimiser
	df: dataframe of points to be assessed (iterable parameters)
	pdata: dataframe of known data from previously preformed simulations
	iter_dic: k,v pairs for parameters
	aba_dic: dictionary of k,v geometry information
	slope_dic: dictionary of k, v material properties information
	csv_head: headers for storing csv data,
	scaler: scaler used to transform data to normalised
	path_dic: dictionary of paths
	"""

	# ###SPECIAL CONDITION: DATA HAS ALREADY BEEN RUN FOR THIS ARRAY RECALCULATE MAPE ON REQUEST
	if df.empty:
		# ##GET VALUES FROM PDATA
		prev_results = pdata[pdata['JOB_NUM'].isin(completed_jobs)]
		for rw, vals in prev_results.iterrows():
			job_name = 'JOB%s' % (str(int(vals['JOB_NUM'])))
			# vals = vals[[k for k in iter_dic.keys()]]
			# vdic = vals.to_dict()
			# ##ONLY RECALCULATE MAPE IF REQUESTED
			if recalc_mape == True:
				# ##CALCULATE MAPE
				omape, mape1, mape2, avg_mape, path_dic = read_sim_results(result_path=path_dic[job_name + '_fvd'],
																		   exp_path=aba_dic['RAW_DATA'],
																		   uts_disp=aba_dic['ENG_DISPLACEMENT'],
																		   pad_value='zeros',
																		   job_name=job_name,
																		   **path_dic)
				opt_target = set_optimiser_target(target_header=target,
												  original_mape=omape,
												  pre_uts_mape=mape1,
												  post_uts_mape=mape2,
												  weighted_mape=avg_mape)
			else:
				opt_target = set_optimiser_target(target_header=target,
												  original_mape=pdata['ORIG_MAPE'].iloc[rw],
												  pre_uts_mape=pdata['MAPE1'].iloc[rw],
												  post_uts_mape=pdata['MAPE2'].iloc[rw],
												  weighted_mape=pdata['WMAPE'].iloc[rw])
			normalised = scaler.transform([vals, ])
			optimizer.register(params=normalised[0], target=opt_target)
	# ##SET THE INCREMENT NUMBER TO LAST DOE VALUE
	else:
		# ##FOR EVERY ROW IN THE DF
		for rw, vals in df.iterrows():
			# ##INCREMENT JOB NUMBER COUNTER
			inc_num += 1
			job_name = 'JOB%s' % (inc_num)
			# ##UPDATE ABA_DIC WITH ITERABLE GTN PARAMETERS
			aba_dic.update(vals.to_dict())
			##################################################
			# ##FIND THE SLOPE VALUE IN MAT DIC (IF IT EXISTS)
			# ##OR CREATE NEW P-DELTA FROM REQUESTED SLOPE
			###################################################
			pl_dic = {}
			try:
				pl_dic['ABAQUS_PLASTIC'] = slope_dic[aba_dic['M']]['ABAQUS_PLASTIC']
				path_dic['plastic_properties'] = pl_dic['ABAQUS_PLASTIC']
			except:
				try:
					# ##SOURCE DATA FROM SLOPE DIC IF AVAILABLE
					pl_dic = extend_new_slope(cslope=slope_dic[aba_dic['M']],
											  mat_dic=aba_dic,
											  jobnum=inc_num,
											  path_dic=path_dic)
					path_dic['plastic_properties'] = pl_dic['ABAQUS_PLASTIC']
				except:
					# ##SLOPE NOT PREVIOULSY CALCULATED
					pl_dic = extend_new_slope(cslope=aba_dic['M'],
											  mat_dic=aba_dic,
											  jobnum=inc_num,
											  path_dic=path_dic)
					path_dic['plastic_properties'] = pl_dic['plastic_properties']
			# ##ADD MATERIAL DATA TO ABA DIC
			aba_dic = merge_dicts(aba_dic, pl_dic)
			# ##CALL ABAQUS
			odb_list = [f for f in os.listdir(path_dic['curr_results']) if '.odb' in f and not '.odb_f' in f]
			if 'JOB%s.odb' % (inc_num) not in odb_list:
				# ##WRITE THE JSON FILE
				json_filename = write_json_file(dic=aba_dic,
												pth=path_dic['curr_results'],
												filename='JOB%s_JSON.txt' % (inc_num))
				etime, path_dic, job_name = FEA_Function(inc_num,
														 json_filename,
														 **path_dic)
			# ##CALCULATE MAPE
			omape, mape1, mape2, avg_mape, path_dic = read_sim_results(result_path=path_dic[job_name + '_fvd'],
																	   exp_path=aba_dic['RAW_DATA'],
																	   uts_disp=aba_dic['ENG_DISPLACEMENT'],
																	   pad_value='zeros',
																	   job_name=job_name,
																	   **path_dic)
			opt_target = set_optimiser_target(target_header=target,
											  original_mape=omape,
											  pre_uts_mape=mape1,
											  post_uts_mape=mape2,
											  weighted_mape=avg_mape)
			# ##NORMALISE THE VALUES
			normalised = scaler.transform([vals, ])
			optimizer.register(params=normalised[0], target=opt_target)
			# ##IF DATA NOT IN OUTPUTS THEN ADD IT
			if inc_num not in pdata['JOB_NUM']:
				# ##READ SIMULATION TIME FROM STA FILE
				etime = read_sim_time(filepath=os.path.join(path_dic['curr_results'],
																	 'JOB%s.sta' % (inc_num)))

				# ##STORE DATA IN OUTPUT CSV
				append_data(path_dic['output_results'], csv_head, {'PHASE': phasei,
																   'JOB_NUM': inc_num,
																   'M': aba_dic['M'],
																   'ORIG_MAPE': omape,
																   'MAPE1': mape1,
																   'MAPE2': mape2,
																   'WMAPE': avg_mape,
																   'SIM_TIME': etime,
																   **aba_dic})
			# ##TRY TO PLOT ENERGY
			if os.path.isfile(os.path.join(path_dic['curr_results'],
										   'JOB%s_ENERGY.csv') % (inc_num)):
				plot_energy(job_iteration=inc_num,
							path_dic=path_dic)
	# ##WRITE PATH DIC TO FILE
	write_json_file(dic=path_dic, pth=path_dic['curr_results'], #
					filename='PATH_DIC.txt')

	# ##CHECK FOR WHETHER TERMINATION IS REQUIRED
	terminate = doe_termination_check(phasei=None,
									  df_path=path_dic['output_results'],
									  target=target)


	return inc_num, optimizer, terminate


def virtual_experiment_from_new_point(phasei=None,
									  inc_num=None,
									  doe_inc=None,
									  target=None,
									  optimizer=None,
									  utility=None,
									  pdata=None,
									  fixed_dic=None,
									  mat_dic=None,
									  aba_dic=None,
									  csv_head=None,
									  scaler=None,
									  path_dic=None):
	"""
	FUNCTION TO RUN VIRTUAL EXPERIMENT USING THE OPTIMIZER TO SELECT NEW TARGETS


	"""
	job_name = 'JOB%s' % (inc_num)
	odb_list = [f for f in os.listdir(path_dic['curr_results']) if '.odb' in f]
	# ##SUGGEST NEW DATA POINT
	norm_next_point = optimizer.suggest(utility)
	# ##INVERSE TRANSFORM THE DATA
	transform = scaler.inverse_transform([np.fromiter(norm_next_point.values(), dtype=float),])
	next_point = {k:transform[0][i] for i, k in enumerate(norm_next_point.keys())}
	# ##UPDATE ABA_DIC WITH ITERABLE GTN PARAMETERS
	aba_dic.update(next_point)
	# ##EXTEND BEYOND UTS FOR GIVEN SLOPE VALUE
	pl_dic = extend_new_slope(cslope=next_point['M'],
							  mat_dic=mat_dic,
							  jobnum=inc_num,
							  path_dic=path_dic)
	# ##ADD MATERIAL DATA TO ABA DIC
	aba_dic.update(pl_dic)
	# ##ADD PLASTIC PROPERTIES TO PATH DIC
	path_dic['plastic_properties'] = aba_dic['plastic_properties']
	# ##IF THERE IS NO ODB FILE
	if 'JOB%s.odb' % (inc_num) not in odb_list:
		# ##WRITE THE JSON FILE
		json_filename = write_json_file(dic=aba_dic,
										pth=path_dic['curr_results'],
										filename='JOB%s_JSON.txt' % (inc_num))
		etime, path_dic, job_name = FEA_Function(inc_num,
												 json_filename,
												 **path_dic)
	# ##ODB EXISTS
	else:
		##############################
		## DOES THE ODB NEED TO BE REASSESSED?
		##############################
		redo = False
		#########################
		## CHECK PREVIOUS DATA MATCHES CURRENT SUGGESTION
		########################
		# ##READ IN JOB VALUES
		pjob_dic = load_json_file(os.path.join(path_dic['curr_results'],
											   'JOB%s_JSON.txt' % (inc_num)))
		for k, v in pjob_dic.items():
			# ##IF VALUE IN ABA_DIC NOT SAME AS VALUE IN PJOB THEN REDO THE ANALYSIS
			if v != aba_dic[k]:
				redo = True
		if redo == True:
			# ##WRITE THE JSON FILE
			json_filename = write_json_file(dic=aba_dic,
											pth=path_dic['curr_results'],
											filename='JOB%s_JSON.txt' % (inc_num))
			etime, path_dic, job_name = FEA_Function(inc_num,
													 json_filename,
													 **path_dic)
	# ##CALCULATE MAPE
	omape, mape1, mape2, avg_mape, path_dic = read_sim_results(result_path=path_dic[job_name + '_fvd'],
															   exp_path=aba_dic['RAW_DATA'],
															   uts_disp=aba_dic['ENG_DISPLACEMENT'],
															   pad_value='zeros',
															   job_name=job_name,
															   **path_dic)
	# ##WRITE PATH DIC TO FILE
	write_json_file(dic=path_dic, pth=path_dic['curr_results'], filename='PATH_DIC.txt')
	###########################################
	## DATA STORAGE
	############################################
	# ##IF DATA NOT IN OUTPUTS THEN ADD IT
	if inc_num not in pdata['JOB_NUM']:
		if not 'etime' in locals():
			# ##READ SIMULATION TIME FROM DAT FILE
			etime = read_sim_time(filepath=os.path.join(path_dic['curr_results'],
														'JOB%s.sta' % (inc_num)))

		# ##STORE DATA IN OUTPUT CSV
		append_data(path_dic['output_results'], csv_head, {'PHASE': phasei,
														   'JOB_NUM': inc_num,
														   'M': aba_dic['M'],
														   'ORIG_MAPE': omape,
														   'MAPE1': mape1,
														   'MAPE2': mape2,
														   'WMAPE': avg_mape,
														   'KAPPA': utility.kappa,
														   'SIM_TIME': etime,
														   **aba_dic})
	opt_target = set_optimiser_target(target_header=target,
									  original_mape=omape,
									  pre_uts_mape=mape1,
									  post_uts_mape=mape2,
									  weighted_mape=avg_mape)
	# ##ADD NEW POINT TO THE OPTIMIZER
	optimizer.register(params=norm_next_point, target=opt_target)
	# ##CHECK FOR WHETHER TERMINATION IS REQUIRED (IGNORE DOE VALUES)
	non_doe = pd.read_csv(path_dic['output_results']).iloc[doe_inc:, :]
	if len(non_doe) >=2 :
		terminate, df, utility = termination_check(iterator=inc_num,
												   df=non_doe,
												   utility=utility,
												   target=target)
	else:
		terminate = False

	# ##TRY TO PLOT ENERGY
	if os.path.isfile(os.path.join(path_dic['curr_results'],
								   'JOB%s_ENERGY.csv') % (inc_num)):
		plot_energy(job_iteration=inc_num,
					path_dic=path_dic)

	return inc_num, optimizer, utility, terminate, path_dic
