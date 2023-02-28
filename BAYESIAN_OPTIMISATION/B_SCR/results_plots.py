import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as style
import pandas as pd
import itertools

marker = itertools.cycle(('s', '+', 'o', '*', 'x', 'v', 'D'))
style.use('tableau-colorblind10')
plt.rcParams["figure.figsize"] = (6, 6)
##set font size
font = {'family': 'sans-serif',
		'weight': 'normal',
		'size': 14}
plt.rc('font', **font)

def plot_mape_v_sim_time(df=None,
						 target=None,
						 path_dic=None):
	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)
	for i, rw in df.iterrows():
		ax[0].scatter(rw['SIM_TIME'] / 60,
					  rw[target],
					  marker=next(marker),
					  label='JOB%s' % (int(rw['JOB_NUM'])))

	# AXES LIMITS
	ax[0].set_xlim([0, (max(df['SIM_TIME'] / 60)) * 1.1])
	ax[0].set_ylim([0, df[target].max() * 1.1])

	# AT LEAST FIVE TICK MARKS ON X AND Y AXES
	ax[0].xaxis.set_major_locator(plt.MaxNLocator(6))
	ax[0].yaxis.set_major_locator(plt.MaxNLocator(6))

	# AXES LABELS
	ax[0].set_xlabel('Time, minutes')
	ax[0].set_ylabel('Mean absolute percentage error (%s), %%'
					 % (target))
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(1.1, 1),
				 loc='upper left',
				 ncol=6,
				 borderaxespad=0,
				 frameon=False)
	# save figure
	plt.savefig(os.path.join(path_dic['curr_results'],
							 'MAPE_V_SIM_TIME.png'),
				dpi=300,
				bbox_inches='tight')
	plt.close('all')


def plot_mape_v_sim_num(df=None,
						target=None,
						path_dic=None):
	"""

	:param df: dataframe of bo results
	:param target: the target you want to plot
	:param path_dic: dictionary of path locations for saving
	:return: .png plot
	"""

	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)

	for i, rw in df.iterrows():
		ax[0].scatter(rw['JOB_NUM'],
					  rw[target],
					  marker=next(marker),
					  label='JOB%s' % (int(rw['JOB_NUM'])))

	# AXES LIMITS
	ax[0].set_xlim([0, (max(df['JOB_NUM'])) * 1.25])
	ax[0].set_ylim([0, df[target].max() * 1.25])

	# AT LEAST FIVE TICK MARKS ON X AND Y AXES
	ax[0].xaxis.set_major_locator(plt.MaxNLocator(6))
	ax[0].yaxis.set_major_locator(plt.MaxNLocator(6))

	# AXES LABELS
	ax[0].set_xlabel('Iteration number')
	ax[0].set_ylabel('Mean absolute percentage error (%s), %%'
					 % (target))
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(1.1, 1),
				 loc='upper left',
				 ncol=6,
				 borderaxespad=0,
				 frameon=False)
	# save figure
	plt.savefig(os.path.join(path_dic['curr_results'],
							 'MAPE_V_SIM_NUM.png'),
				dpi=300,
				bbox_inches='tight')
	plt.close('all')


def top_three(df=None,
			  target=None,
			  path_dic=None):
	"""
	Function to plot top three optimiser results against experimental data
	:param df: OUTPUT.csv
	:param target: The MAPE target (i.e string of MAPE1, MAPE2 or AVG_MAPE)
	:param path_dic: Dictionary of paths to relevant files
	:return: savefigure do not return object
	"""

	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)

	# ##USING PATH DIC FIND GET RELEVANT DATA
	exp_df = pd.read_csv(path_dic['exp_fvd_extrap'])

	# ##PLOT EXPERIMENTAL
	# ##PLOT DATA
	ax[0].plot(exp_df['U'],
			   exp_df['RF'],
			   linestyle='None',
			   marker='o',
			   markevery=0.05,
			   color='k',
			   label='Experimental')

	# ##SORT OUTPUTS USING MAPE COLUMN AND RESET INDEX
	sorted = df.sort_values(by=[target],
							axis=0,
							ascending=True).reset_index(drop=True)

	# ##GET TOP THREE RESULTS
	best = sorted.iloc[0:3]

	for i, rw in best.iterrows():
		best_df = pd.read_csv(path_dic['JOB%s_fvd_extrap' % (int(rw.loc['JOB_NUM']))])
		# ##PLOT SIMULATION DATA
		ax[0].plot(best_df['U'],
				   best_df['RF'],
				   linestyle='--',
				   label='JOB%s MAPE:%s %%' % (int(rw.loc['JOB_NUM']), round(rw.loc[target], 2)))

	# AXES LIMITS
	ax[0].set_xlim([0, exp_df['U'].max() * 1.1])
	ax[0].set_ylim([0, exp_df['RF'].max() * 1.1])

	# AT LEAST FIVE TICK MARKS ON X AND Y AXES
	ax[0].xaxis.set_major_locator(plt.MaxNLocator(6))
	ax[0].yaxis.set_major_locator(plt.MaxNLocator(6))

	# AXES LABELS
	ax[0].set_xlabel('Displacement, mm')
	ax[0].set_ylabel('Force, kN')
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(1, 0),
				 loc='lower right',
				 ncol=1,
				 borderaxespad=0,
				 frameon=False)
	# save figure
	plt.savefig(os.path.join(path_dic['curr_results'],
							 'TOP_THREE.png'),
				dpi=300,
				bbox_inches='tight')
	plt.close('all')


def exp_v_simulation(i_fea=None, mape=None, **path_dic):
	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)

	# ##USING PATH DIC FIND GET RELEVANT DATA
	exp_df = pd.read_csv(path_dic['exp_fvd'], header=[0, 1]).droplevel(1, axis=1)
	# ##CONVERT TO NEWTONS
	exp_df['RF'] = exp_df['FORCE'] * 1000
	# ##USE PATH DIC TO FIND SIMULALTION
	sim_df = pd.read_csv(path_dic['JOB' + str(int(i_fea)) + '_fvd'])

	# ##PLOT DATA
	ax[0].plot(exp_df['DISPLACEMENT'],
			   exp_df['RF'] / 1000,
			   linestyle='None',
			   marker='o',
			   markevery=0.05,
			   color='k',
			   label='Experimental')
	ax[0].plot(sim_df['U'],
			   sim_df['RF'] / 1000,
			   color='k',
			   linestyle='--',
			   label='simulation')
	# ##AXES TEXT
	ax[0].text(x=0.01,
			   y=0.05,
			   s='Job number: %s Error: %s %%'
				 % (int(i_fea), round(mape, 2)),
			   horizontalalignment='left',
			   verticalalignment='center',
			   transform=ax[0].transAxes)

	# AXES LIMITS
	ax[0].set_xlim([0, exp_df['DISPLACEMENT'].max() * 1.25])
	ax[0].set_ylim([0, exp_df['FORCE'].max() * 1.25])

	# AT LEAST FIVE TICK MARKS ON X AND Y AXES
	ax[0].xaxis.set_major_locator(plt.MaxNLocator(6))
	ax[0].yaxis.set_major_locator(plt.MaxNLocator(6))

	# AXES LABELS
	ax[0].set_xlabel('Displacement, mm')
	ax[0].set_ylabel('Force, kN')
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(1.1, 1),
				 loc='upper left',
				 ncol=1,
				 borderaxespad=0)
	# save figure
	plt.savefig(os.path.join(path_dic['curr_results'],
							 'COMPARE_FVD_JOB%s.png' % (str(int(i_fea)))),
				dpi=300,
				bbox_inches='tight')
	plt.close('all')


def plot_fvd_exp_v_sim(exp_path=None,
					   sim_path=None,
					   uts_disp=None,
					   mape1=None,
					   mape2=None,
					   job_name=None,
					   savepath=None):
	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)

	# ##READ IN EXP
	exp_df = pd.read_csv(exp_path)
	ax[0].plot(exp_df['U'],
			   exp_df['RF'],
			   marker='o',
			   markevery=0.05,
			   linestyle='None',
			   color='k',
			   label='experiment')

	# ##READ IN SIMULATION
	sim_df = pd.read_csv(sim_path)
	ax[0].plot(sim_df['U'], sim_df['RF'], label=job_name)

	# ##GET MAXIMUM FORCE VALUE
	mx_p = 1.1 * max(exp_df['RF'].max(), sim_df['RF'].max())
	# ##VERTICAL LINE REPRESENTING UTS DISPLACEMENT
	ax[0].vlines(x=uts_disp, ymin=0, ymax=mx_p,
				 color='k', linestyle='--', label='UTS position')
	# ##ADD TEXT FOR MAPE1
	ax[0].text(0.25, 0.1,
			   s='MAPE1: %s%%' % (round(mape1, 2)),
			   horizontalalignment='center',
			   verticalalignment='center',
			   transform=ax[0].transAxes)
	# ##ADD TEXT FOR MAPE1
	ax[0].text(0.75, 0.1,
			   s='MAPE2: %s%%' % (round(mape2, 2)),
			   horizontalalignment='center',
			   verticalalignment='center',
			   transform=ax[0].transAxes)

	# ##AXES LABELS
	ax[0].set_xlabel('Displacement, mm')
	ax[0].set_ylabel('Force, kN')
	# ##AXES LIMITS
	ax[0].set_xlim([0, 3])
	ax[0].set_ylim([0, mx_p])
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(1.1, 1),
				 loc='upper left',
				 ncol=1,
				 borderaxespad=0,
				 frameon=False)
	# save figure
	plt.savefig(os.path.join(savepath, '%s_LD_EXP.png' % (job_name)),
				dpi=300,
				bbox_inches='tight')
	plt.close()


def plot_energy(job_iteration=None,
				path_dic=None):
	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)

	# ##READ IN DATA
	df = pd.read_csv(os.path.join(path_dic['curr_results'],
								  'JOB%s_ENERGY.csv') % (job_iteration))
	# ##PLOT KINETIC
	ax[0].plot(df['TIME'], df['ALLKE'], label='Kinetic')
	# ##PLOT INTERNAL
	ax[0].plot(df['TIME'], df['ALLIE'], label='Internal')

	# ##AXES LABELS
	ax[0].set_xlabel('Time, seconds')
	ax[0].set_ylabel('Energy, $kg(mm/s)^2$')
	# ##AXES LIMITS
	ax[0].set_xlim([0, df['TIME'].max() * 1.1])
	ax[0].set_ylim([0, max(df.max()) * 1.1])
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(1, 1),
				 loc='upper right',
				 ncol=1,
				 borderaxespad=0,
				 frameon=False)
	# save figure
	plt.savefig(os.path.join(path_dic['curr_results'],
							 'JOB%s_ENERGY.png' % (job_iteration)),
				dpi=300,
				bbox_inches='tight')
	plt.close()


def compare_msf(results=None,
				target=None,
				job=None,
				list_simulations=None,
				path_dic=None):
	"""
	Function to compare various MSF for explicit analyses
	:param results: dataframe of output results, required to find mape
	:param job: string representing the results header for the mape calculation
	:param job: Job number to be compared
	:param list_simulations: list of csv files for various MSF analyses
	:param path_dic: dictionary of paths
	:return: no return plot is saved to current results folder
	"""

	fig, ax2d = plt.subplots()
	ax = np.ravel(ax2d)

	# ##for each file in list sims
	# ##read in data and plot
	for f in list_simulations:
		# ## GET JOB NAME
		if 'MSF10' in f:
			job_name = f[0:f.find('MSF') + 5]
			label_name = f[7:f.find('M') + 5]
		elif 'MSF' in f:
			job_name = f[0:f.find('MSF') + 4]
			label_name = f[7:f.find('M') + 4]
		else:
			job_name = f[0:f.find('_')]
			label_name = '%s_MSF10' % (job_name)

		# ##LOCATE MAPE FROM OUTPUT FILE
		mape = results[results['JOB_NUM'] == job_name][target].iloc[0]
		# ##DEFINE PLOT LABEL
		plabel = '%s MAPE:%s %%' % (label_name, round(mape, 2))

		# ##READ SIMULATED DATA AND PLOT ON GRAPH
		df = pd.read_csv(os.path.join(path_dic['curr_results'], f))
		ax[0].plot(df['U'], df['RF'], marker=next(marker), markevery=0.3, label=plabel)

	# ##AXES LABELS
	ax[0].set_xlabel('Displacement, mm')
	ax[0].set_ylabel('Force, kN')
	# ##AXES LIMITS
	ax[0].set_xlim([0, 3])
	ax[0].set_ylim([0, df['RF'].max() * 1.1])
	# ##LEGEND
	ax[0].legend(bbox_to_anchor=(0.05, 0.0),
				 loc='lower left',
				 ncol=1,
				 borderaxespad=0,
				 frameon=False)
	# save figure
	plt.savefig(os.path.join(path_dic['curr_results'],
							 '%s_COMPARE_MSF.png' % (job)),
				dpi=300,
				bbox_inches='tight')
	plt.close()
