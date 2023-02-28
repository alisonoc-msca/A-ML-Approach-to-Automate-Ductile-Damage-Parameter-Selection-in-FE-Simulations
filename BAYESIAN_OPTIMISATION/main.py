import collections
import os
import pandas as pd
from datetime import date
from B_SCR.Continious_Bayesian_Optimisation import BayesianOptimization
from B_SCR.Acquisition_utilies import AcquisitionUtilities
from B_SCR.general_functions import new_dir_add_dic, merge_dicts, load_json_file, check_existing_data
from B_SCR.general_functions import write_json_file, set_optimiser_target
from B_SCR.DoE import create_taguchi_array
from B_SCR.virtual_experiment import virtual_experiment_from_array, virtual_experiment_from_new_point
from B_SCR.error_function import read_sim_results
from B_SCR.results_plots import plot_mape_v_sim_num, plot_mape_v_sim_time, top_three, plot_energy
from B_SCR.termination_function import *
from sklearn.preprocessing import MinMaxScaler

""" 
THIS PROJECT ANALYSES ABAQUS EXPLICIT USING BAYESIAN OPTIMISATION
"""
# ##GET TODAYS DATE
today = date.today().strftime("%Y%m%d")
# ##CREATE DICTIONARY OF PATHS TO RELEVANT DIRECTORIES AND FILES
path_dic = {'cwd': os.getcwd(),
			'project_dir': os.path.join(os.getcwd(), '../'),
			'material_analysis': os.path.join(os.getcwd(), '../../MATERIAL_ANALYSIS/OUTPUT'),
			'raw_data': os.path.join(os.getcwd(), 'A_RAW_DATA')}
# ##DICTIONARY HOLDING GEOMETRICAL DATA
geom_dic = {'GAUGE_LENGTH': 25.,
			'GAUGE_DIAMETER': 4.,
			'CONN_DIAMETER': 5.,
			'SPECIMEN_LENGTH': 72.,
			'ROUND_RADIUS': 3.,
			'THREADED_LENGTH': 15}
#################################
## SET GTN PARAMETER BOUNDS
################################
damage_dic = {'Q1': (0.9, 1.6),
			  'Q2': (0.9, 1.1),
			  'Q3': (0.9 ** 2, round(1.6 ** 2, 2)),
			  'EN': (0.25, 0.4),
			  'SN': (0.1, 0.2),
			  'FN': (0.03, 0.09),
			  'F': (0.0013, 0.0015)}
# ##HEADERS FOR CSV OUTPUT FILE
csv_headers = ['JOB_NUM', 'Q1', 'Q2', 'Q3', 'EN', 'SN', 'FN',
			   'F', 'M', 'ORIG_MAPE', 'MAPE1', 'MAPE2', 'WMAPE', 'KAPPA', 'SIM_TIME']
# ##CREATE RESULTS SUBDIRECTORY
path_dic = new_dir_add_dic(dic=path_dic,
						   key='results',
						   path=path_dic['cwd'],
						   dir_name='RESULTS',
						   exist_ok=True)
# ##MAX NUMBER OF SIMULATIONS
not_exceed = 200
# ##FOR STANDARD AND EXPLICIT
analysis_list = ['EXPLICIT']
# ###RECALCULATE MAPE
recalc_mape = False
# ##PARAMETER TO BE MINIMISED
target_minimizer = 'ORIG_MAPE'
print('The target to be minimised is: %s' % (target_minimizer))
doe_array='L12.csv'
for anatype in analysis_list:
	if anatype == 'STANDARD':
		path_dic['build'] = os.path.join(os.getcwd(), 'B_SCR/aba_build_std.py')
		path_dic['postp'] = os.path.join(os.getcwd(), 'B_SCR/aba_pp_std.py')
	else:
		path_dic['build'] = os.path.join(os.getcwd(), 'B_SCR/aba_build_expl.py')
		path_dic['postp'] = os.path.join(os.getcwd(), 'B_SCR/aba_pp_expl.py')
	# ##CREATE SUBDIRECTORY FOR ANALYSIS TYPE
	path_dic = new_dir_add_dic(dic=path_dic,
							   key='analysis_type',
							   path=path_dic['results'],
							   dir_name=anatype,
							   exist_ok=True)
	# ##GET THE MATERIAL NAME FROM RAW DATA IN MATERIAL ANALYSIS
	listmat = [f for f in os.listdir(path_dic['material_analysis']) if os.path.isdir(os.path.join(path_dic['material_analysis'], f))]
	# ##FOR DEBUGGING PURPOSES WE WILL INITIALISE ONLY 1 MATERIAL
	listmat = [listmat[1]]
	for imat, material in enumerate(listmat):
		print('THIS IS AN ABAQUS %s ANALYSIS' % (anatype))
		print('MATERIAL: %s' % (material))
		# ##CREATE MATERIALS SUBDIRECTORY
		path_dic = new_dir_add_dic(dic=path_dic,
								   key='curr_results',
								   path=path_dic['analysis_type'],
								   dir_name=material,
								   exist_ok=True)
		# ##READ IN DICTIONARY ON MATERIAL PROPERTIES
		mat_dic = load_json_file(os.path.join(os.path.join(path_dic['material_analysis'], material),
											  material + '_properties.txt'))
		# ##MODIFY MAT_DIC TO HAVE MATERIAL PROPS AND SLOPES AS SEPARATE ITEMS
		slope_dic = {float(k): v for k, v in mat_dic['SLOPE'].items()}
		# ##MERGE LARGEST AND SMALLEST SLOPES INTO DAMAGE DIC
		damage_dic['M'] = (min(slope_dic.keys()), max(slope_dic.keys()))
		# ##REMOVE SLOPE KEY FROM MAT_DIC
		mat_dic = {k: v for k, v in mat_dic.items() if not k == 'SLOPE'}
		# ##CREATE ABAQUS DICTIONARY WITH GEOMETRY AND MATERIAL INFORMATION
		gen_aba_dic = merge_dicts(geom_dic, mat_dic)
		# ##GET THE EXPERIMENTAL RAW DATA
		exp_df = pd.read_csv(mat_dic['RAW_DATA'])
		# ##CHECK FOR EXISTING ODB DATA
		output_df, path_dic = check_existing_data(dirpth=path_dic['curr_results'],
												  res_filname='OUTPUT.csv',
												  csv_headers=csv_headers,
												  path_dic=path_dic)
		# ##CHECK IF OUTPUT IS FINISHED
		if not output_df.empty:
			if output_df['JOB_NUM'].iloc[-1] == not_exceed:
				continue
		# ##WRITE THE PATH TO FILE
		write_json_file(dic=path_dic, pth=path_dic['curr_results'], filename='PATH_DIC.txt')
		# ##SET TAGUCHI ARRAY VALUES
		ctag, mcount, pcomplete = create_taguchi_array(fpth_tag_order=os.path.join(path_dic['raw_data'], doe_array),
													   fpth_results=path_dic['output_results'],
													   iter_dic=damage_dic,
													   fixed_dic=None,
													   iter_num=int(0),
													   phaseiter=None)
		############################################
		# ##RUN DOE FOR CTAG ARRAY OR CONDUCT MAPE CALCULATION
		############################################
		mcount, optimizer1, terminate = virtual_experiment_from_array(recalc_mape=recalc_mape,
																	  phasei=None,
																	  target=target_minimizer,
																	  inc_num=mcount,
																	  completed_jobs=pcomplete,
																	  optimizer=BayesianOptimization(f=None,
																									 pbounds=damage_dic,
																									 random_state=1),
																	  df=ctag,
																	  pdata=output_df,
																	  iter_dic=damage_dic,
																	  aba_dic=gen_aba_dic,
																	  slope_dic=slope_dic,
																	  csv_head=csv_headers,
																	  path_dic=path_dic)
		############################################
		# ##ARE IF NON-DOE DATA NEED TO BE REGISTERED
		############################################
		# ##REDUCE OUTPUT RESULTS TO NON-DOE DATA ONLY
		non_doe = pd.read_csv(path_dic['output_results']).iloc[
				  len(pd.read_csv(os.path.join(path_dic['raw_data'], doe_array))):, :]
		for rwi, rw in non_doe.iterrows():
			# ##RECALCULATE MAPE
			job_num = int(rw['JOB_NUM'])
			job_name = 'JOB%s' % (job_num)
			aba_dic = load_json_file(os.path.join(path_dic['curr_results'], '%s_JSON.txt' % (job_name)))
			if recalc_mape:
				omape, mape1, mape2, avg_mape, path_dic = read_sim_results(result_path=path_dic[job_name + '_fvd'],
																		   exp_path=aba_dic['RAW_DATA'],
																		   uts_disp=aba_dic['ENG_DISPLACEMENT'],
																		   pad_value='zeros',
																		   job_name=job_name,
																		   **path_dic)
				if anatype == 'EXPLICIT':
					plot_energy(job_iteration=job_num, path_dic=path_dic)

				opt_target = set_optimiser_target(target_header=target_minimizer,
												  original_mape=omape,
												  pre_uts_mape=mape1,
												  post_uts_mape=mape2,
												  weighted_mape=avg_mape)
				# ##REGISTER THE UPDATED MAPE CALCULATION
				optimizer1.register(params=[rw[k] for k in sorted(damage_dic.keys())], target=opt_target)
			else:
				opt_target = set_optimiser_target(target_header=target_minimizer,
												  original_mape=rw['ORIG_MAPE'],
												  pre_uts_mape=rw['MAPE1'],
												  post_uts_mape=rw['MAPE2'],
												  weighted_mape=rw['WMAPE'])
				# ##REGISTER THE UPDATED MAPE CALCULATION
				optimizer1.register(params=[rw[k] for k in sorted(damage_dic.keys())], target=opt_target)
			print('Iteration %s of maximum %s' % (job_num, not_exceed))
		# if (non_doe[target_minimizer]<3).any():
		# 	terminate = True
		if (terminate == False):
			# ##########################
			# ## USE BO TO SELECT NEW POINTS
			# ##########################
			start = mcount  # ##COUNTER FOR THIS SPECIFIC LOOP
			max_simulations = start + (200-start)
			for i in range(start, min(max_simulations, not_exceed), 1):
				i += 1
				# ##SET THE UTILITY FOR PARAMETER SELECTION FOR START ITERATION TO 2.5
				if i == start + 1:
					curr_utility = AcquisitionUtilities(aq_type='UCB', kappa=2.500, xi=0)
				# ##USE MODIFIED KAPPA UTILITY
				else:
					curr_utility = utility1
				print('ITERATION NUM %s of maximum %s' % (i, not_exceed))
				mcount, optimizer1, utility1, terminate, path_dic = virtual_experiment_from_new_point(inc_num=i,
																									  doe_inc=len(pd.read_csv(os.path.join(path_dic['raw_data'], doe_array))),
																									  target=target_minimizer,
																									  optimizer=optimizer1,
																									  utility= curr_utility,
																									  pdata=pd.read_csv(path_dic['output_results']),
																									  fixed_dic=None,
																									  mat_dic=mat_dic,
																									  aba_dic=gen_aba_dic,
																									  csv_head=csv_headers,
																									  path_dic=path_dic)
				# ##WRITE OUT PATH DIC
				write_json_file(dic=path_dic, pth=path_dic['curr_results'], filename='PATH_DIC.txt')
				# ##EXIT EARLY
				if (terminate == True) or (i == min(max_simulations, not_exceed)):
					break

		# ##PLOT DATA
		plot_mape_v_sim_time(df=pd.read_csv(path_dic['output_results']),
							 target=target_minimizer,
							 path_dic=path_dic)
		plot_mape_v_sim_num(df=pd.read_csv(path_dic['output_results']),
							target=target_minimizer,
							path_dic=path_dic)
		top_three(df=pd.read_csv(path_dic['output_results']),
				  target=target_minimizer,
				  path_dic=path_dic)
