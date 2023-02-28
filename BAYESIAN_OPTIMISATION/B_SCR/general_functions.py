import os
import itertools
import json
import numpy as np
import pandas as pd
from B_SCR.csv_functions import init_data_storage

def product_dic(**kwargs):
	"""
    Use itertools to get dictionary of all possible combinations
    of keys/values
    :param kwargs:dictionary to be iterated
    :return: expanded dictionary
    """
	keys = kwargs.keys()
	vals = kwargs.values()
	a = {}
	for num, item in enumerate(itertools.product(*vals)):
		a[num] = dict(zip(keys, item))
	return a


def merge_dicts(dic1, dic2):
	"""
    Combine two dictionaries into single dictionary
    :param dic1:
    :param dic2:
    :return: Combined dictionary
    """
	z = dic1.copy()
	z.update(dic2)
	return z


def write_json_file(dic, pth, filename):
	"""
    WRITE DICTIONARY DATA TO TEXT FILE
    :param dic: dictionary to be written
    :param pth: path to save location
    :param filename: filename to save item
    :return: file path
    """
	with open(os.path.join(pth, filename), 'w') as file:
		json.dump(dic, file, indent=4)
	return os.path.join(pth, filename)


def load_json_file(j_file):
	"""
    Read txt file as dictionary item
    :param j_file: file path plus filename
    :return: dictionary
    """
	with open(j_file) as json_file:
		return json.load(json_file)


def write_text_file(data=None, root=os.getcwd(), filename=None):
	""" WRITE TO TXT FILE RETURN FILE PATH"""
	with open(os.path.join(root, filename), 'w') as file:
		for item in data:
			file.write('%s\n' % (item))
	return os.path.join(root, filename)


def read_text_file(root=os.getcwd(), filename=None):
	""" READ TEXT FILE LINE BY LINE"""
	with open(os.path.join(root, filename), 'r') as file:
		output = file.readlines()
		return [i.splitlines()[0] for i in output]


def new_dir_add_dic(dic, key, path, dir_name, exist_ok=False):
	"""
    CREATE A NEW DIRECTORY AND ADD PATH TO DICTIONARY OF PATHS RETURN UPDATED PATH DICTIONARY
    :param dic: DICTIONARY OF PATHS
    :param key: KEY TO ACCESS THE NEW PATH
    :param path: PATH TO SAVE LOCATION
    :param dir_name: NAME THE DIRECTORY
    :param exist_ok: CHECK WHETHER DIRECTORY EXISTS
    :return: UPDATED DIRECTORY OF PATHS
    """
	""" """
	full_path = os.path.join(path, dir_name.upper())
	# ##MAKE THE DIRECTORY
	try:
		os.makedirs(full_path, exist_ok=exist_ok)
	except FileExistsError:
		name = file_exists_error(full_path, path)
		full_path = os.path.join(path, name)
		os.makedirs(full_path, exist_ok=True)
	# ##ADD THE PATH TO PATH DIC
	dic.update({key: full_path})
	return dic


def file_exists_error(path, root):
	"""
    IF DIRECTORY EXISTS WITH THAT NAME THEN
    APPEND A NUMBER TO THE DIRECTORY NAME
    :param path: PATH TO EXISTING DIRECTORY (INCL DIRECTORY NAME)
    :param root: PATH WITHOUT DIRECTORY NAME
    :return: NEW DIRECTORY NAME WITH APPENDED VALUE
    """
	""" IF DIRECTORY ALREADY EXISTS ADD A NUMBER"""
	# ##CHECK IF DATE FOLDER IS EMPTY
	files = os.listdir(path)
	# ## IF FILES WE NEED NEW DIRECTORY
	if files:
		# ##GET FOLDER NAME (CURRENT DATE)
		base_name = path[path.rfind('\\') + 1:]
		# ##GET ALL FOLDERS IN THE ROOT DIRECTORY (ONE LEVEL UP FROM DATE FOLDER)
		folder_list = [d for r, d, f in os.walk(root) if base_name in d][0]
		# ##SEARCH FOR GREATEST EXISTING INDEXER
		index_list = [int(f[f.rfind('_') + 1:]) for f in folder_list if '_' in f and base_name in f]
		if index_list:
			max_index = max(index_list)
			# ## LATEST FOLDER
			name = base_name + '_' + str(max_index)
			latest_folder = os.path.join(root, name)
			# ##CHECK FOR FILES IN THE LATEST FOLDER (I.E. HIGHEST _X FOLDER)
			files = os.listdir(latest_folder)
			# ##IF THERE ARE FILES WE NEED A NEW FOLDER
			if files:
				val = max_index + 1
				name = base_name + '_' + str(val)
		else:
			# ##NEW NAME
			name = base_name + '_1'
	else:
		name = path[path.rfind('\\') + 1:]
	return name


def bounds_select_features(bounds_path=os.getcwd(),
						   feature_list=None):
	""" FUNCTION TO RETURN MODIFIED BOUNDS
    BASED ON FEATURE SELECTION.
    1. ONLY SELECTED FEATURES WILL ITERATE
    2. UNSELECTED FEATURES WILL RETURN MEAN VALUE
    """
	pbounds = load_json_file(bounds_path)
	stable = {}
	ndic = {}
	for k, v in pbounds.items():
		if k in feature_list:
			ndic[k] = v
		else:
			stable[k] = np.round(sum(v) / len(v), 4)
	return ndic, stable


def percentage_dic(percentage=None, **dic):
	""" FUNCTION TO ITERATE DICTIONARY
    KEYS AND MODIFY BOUNDS TO BE PERCENTAGE OF MEAN VALUE"""
	new_dic = {}
	for k, v in dic.items():
		# ##GET MEAN VALUE
		mean = np.mean(v)
		# ##FIND THE PERCENTAGE MOVEMENT
		perc = mean * (percentage / 100)
		# ## GET NEW MIN MAX ADD TO DIC
		new_dic[k] = (mean - perc, mean + perc)
	return new_dic


def check_existing_data(dirpth=None,
						res_filname=None,
						csv_headers=None,
						path_dic=None):
	"""
    CHECK WHETHER SOME ANALYSES HAVE ALREADY BEEN CONDUCTED
    1. LIST ALL CSVS IN DIR
    2. LIST ALL ODBS IN DIR
    3. IF CSV OR ODB EMPTY THEN INIT RESULTS CSV
    4. ELSE READ IN EXISTING RESULTS AND PATH_DIC
    :return: DF OF MASTER RESULTS
    """
	# ##READ ALL ODBS IN DIRECTORY
	odb_list = [f for f in os.listdir(dirpth) if '.odb' in f]
	# ##ODB HAVE DATA
	if odb_list:
		# ##FIND THE RESULTS CSV
		try:
			# ##READ IN MASTER RESULTS
			df = pd.read_csv(os.path.join(dirpth, res_filname))
			# ##READ IN PREVIOUSLY DEFINED PATH DICTIONARY
			path_dic = load_json_file(os.path.join(dirpth, 'PATH_DIC.txt'))
			# ##SET PATH TO OUTPUT FILE
			path_dic['output_results'] = os.path.join(dirpth, res_filname)
		except:
			# ##SET PATH TO OUTPUT FILE
			path_dic['output_results'] = os.path.join(dirpth, res_filname)
			# ##INITIALISE A CSV FILE FOR STORING OUTPUT RESULTS
			init_data_storage(path_dic['output_results'], csv_headers)
			df = pd.read_csv(path_dic['output_results'])
	else:
		# ##SET PATH TO OUTPUT FILE
		path_dic['output_results'] = os.path.join(dirpth, res_filname)
		# ##INITIALISE A CSV FILE FOR STORING OUTPUT RESULTS
		init_data_storage(path_dic['output_results'], csv_headers)
		df = pd.read_csv(path_dic['output_results'])

	path_dic = check_csv_files_path(dirpath=path_dic['curr_results'],
									path_dic=path_dic)
	return df, path_dic

def check_csv_files_path(dirpath=None,
						 path_dic=None,):
	"""


	:param dir: DIRECTORY OF INTEREST
	:param path_dic: DICTIONARY OF PATHS
	:return: MODIFIED PATH DICTIONARY
	"""
	# ##GET LD_DATA
	ld = [f for f in os.listdir(dirpath) if 'LD_DATA' in f and not 'EXP' in f]
	extrap = [f for f in os.listdir(dirpath) if 'SIM' in f and not 'EXP' in f]

	for f in ld:
		name = f[:f.find('_')] + '_fvd'
		path_dic[name] = os.path.join(dirpath, f)

	for f in extrap:
		name = f[:f.find('_')] + '_fvd_extrap'
		path_dic[name] = os.path.join(dirpath, f)

	# ##WRITE THE PATH DIC
	write_json_file(dic=path_dic,
					pth=dirpath,
					filename='PATH_DIC.txt')

	return path_dic
def read_sim_time(filepath):
	"""
	FUNCTION TO READ SIMULATION TIME FROM ABAQUS .dat FILE
	:param: filepath -path to dat file
	:return: float of simulation time
	"""

	with open(filepath) as f:
		lines = f.readlines()
		for l in lines:
			if 'WALLCLOCK' in l:
				sim_time = l[l.rfind(' '):l.rfind('\n')]
				break
		if 'sim_time' in locals():
			sim_time = float(sim_time)
		else:
			sim_time = 'unknown'
			print('Wallclock time not found setting arbitrary value')

	return sim_time

def set_optimiser_target(target_header=None,
						 original_mape=None,
						 pre_uts_mape=None,
						 post_uts_mape=None,
						 weighted_mape=None):
	"""
	Function to ensure the same target mape is used for bayesian optimiser selection
	:param target_header: string header representing the target mape we want to study
	:param original_mape: MAPE calculated for the entire fvd curve
	:param pre_uts_mape: MAPE calculated for fvd curve up to UTS only
	:param post_uts_mape: MAPE calculated for post-UTS region of fvd curve
	:param weighted_mape: Weighted MAPE where post-UTS region is classed as twice as important compared to pre-UTS region
	:return: MAPE calculation to be applied to bayesian optimiser
	"""

	# ##SET WHAT MINIMISER SHOULD BE USED IN THE BO OPTIMISER
	if target_header=='ORIG_MAPE':
		opt_target = original_mape
	elif target_header == 'MAPE1':
		opt_target = pre_uts_mape
	elif target_header == 'MAPE2':
		opt_target = post_uts_mape
	elif target_header == 'WMAPE':
		opt_target = weighted_mape

	return opt_target


