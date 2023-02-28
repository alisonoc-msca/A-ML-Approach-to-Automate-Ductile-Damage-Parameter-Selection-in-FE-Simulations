import os
import shutil

def delete_unwanted(dir_path):
	unwanted = ['.rpy', '.rpy*', '.sim', '.com', '.log', '.rec', '.rec*', '.env', '.stt', '.simlog',
				'.res', '.sel', '.mdl']
	for rm in unwanted:
		for f in os.listdir(dir_path):
			if rm in f:
				try:
					os.remove(os.path.join(dir_path, f))
				except:
					print('FILE: %s NOT REMOVED' %(os.path.join(dir_path, f)))