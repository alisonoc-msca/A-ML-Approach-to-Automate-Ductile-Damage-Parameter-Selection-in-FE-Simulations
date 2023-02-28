# ##ABAQUS REQUIREMENTS
import visualization
from abaqus import *
from abaqusConstants import *
from odbAccess import *
# ##AOC IMPORTS
import os
import sys
import numpy as np
import csv

"""
THIS IS A PYTHON V2.7 SCRIPT TO EXTRACT DATA FROM ABAQUS STANDARD ODB FILE OF UNIAXIAL TENSILE TEST.
NOTE: DISPLACEMENT U2 IS TAKEN FROM REFERENCE POINT NODE KINEMATICALLY COUPLED TO MODEL SURFACE
DISPLACEMENT U1 IS TAKEN FROM NODE LOCATED AT THE CENTRAL GAUGE SECTION NEAR THE X-AXIS SYMMETRY PLANE
REACTION FORCE RF2 IS TAKEN AS THE SUM OF THE REACTION FORCE AT EACH NODE ON THE X-SYMMETRY PLANE
U1,U2, RF2 ARE TAKEN AS FUNCTIONS OF TIME AS PER ABAQUS EXTRACTION METHOD. 
THE FINAL DICTIONARY EXPORTED AS CSV FILE CONTAINS RF2, U2 ONLY.
THE NECK DIAMETER IS EXPORTED VIA SYSTEM COMMANDS TO OTHER CODE.
NECK DIAMATER IS MULTIPLIED BY TWO PRIOR TO EXPORTING (TO ACCOUNT FOR SYMMETRY)
"""

def get_fieldnames(var_keys, xyData_keys):
	"""
	:param var_keys: list of dictionary key items
	:param xyData_keys:  list of xy data objects from abaqus
	:return: collate similar items
	"""
	field_dic = {}  # DICTIONARY TO HOLD NAME OF ITEM (U, RF ETC) AND LIST OF FIELDNAMES ASSOCIATED WITH THAT ITEM
	for k in var_keys:  # FOR EVERY ITEM (U, RF)
		list_field = [key for key in xyData_keys if k in key]  # INITIALISE EMPTY LIST TO HOLD FIELDNAMES
		# ADD THE LIST TO THE FIELDNAME DICTIONARY
		field_dic[k] = list_field
	return field_dic


def write_csv_py27(dir, title, dic):
	'''
	:param dir: directory in which results should be located
	:param title: filename for the result
	:param dic: data
	:return:
	'''
	my_pth = os.path.join(dir, title)
	# SET HEADERS
	headers = dic.keys()
	# SET DATA
	rowList = list(dic.values())
	data = np.array(rowList).T
	with open(my_pth, 'wb', ) as A:
		writer = csv.writer(A)
		writer.writerow(headers)
		for i in data:
			writer.writerow(i)

# ##SET JOB NAME FROM SYS ARGUMENT
job_name = sys.argv[-1]
# job_name = 'JOB1'

# ##SET JOURNAL OPTIONS
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)

# OPEN ODB AND SET FILE
curr_odb = openOdb(path=os.path.join(os.getcwd(), job_name + '.odb'), readOnly=True)
# STEP OBJECT ONLY WANT DATA FROM LAST STEP (WHERE DISPLACEMENT IS APPLIED, IGNORE INITIAL STEP)
mySteps = curr_odb.steps
numSteps = len(mySteps)
lastStepKey = mySteps.keys()[-1]
lastStep = mySteps[lastStepKey]
# DEFINE THE INSTANCE THAT WE'RE INTERESTED IN
instanceKey = curr_odb.rootAssembly.instances.keys()[0]  # RETURNS THE NAME OF THE INSTANCE
instance = curr_odb.rootAssembly.instances[instanceKey]  # RETURNS INSTANCE OBJECT
# ##DEFINE THE ITEMS WE WANT TO EXTRACT
variable_dic = {'UX': {'SET': 'BOTTOM_EDGE_VERTICE',
					   'VARIABLE': 'U1',
					   'S1': 'Spatial displacement: ',
					   'S2': ' at Node ',
					   'S3': ' in NSET '},
				'RF': {'SET': 'BOTTOM_EDGE',
					   'VARIABLE': 'RF2',
					   'S1': 'Reaction force: ',
					   'S2': ' at Node ',
					   'S3': ' in NSET '},
				'UY': {'SET': 'LOADING_POINT',
					   'VARIABLE': 'U2',
					   'S1': 'Spatial displacement: ',
					   'S2': ' at Node ',
					   'S3': ' in NSET '},
				}
# ##EXTRACT ITEMS OF INTEREST AND HOLD IN DICTIONARY
# FOR EACH KEY, VALUE PAIR IN THE DICTIONARY
for k, v in variable_dic.items():
	# GET THE SET AS OBJECT
	cSet = instance.nodeSets[v['SET']]
	# COUNT NUMBER OF NODES
	numNodes = len(cSet.nodes)
	# FOR EVERY NODE IN THE SET EXTRACT HISTORY DATA
	for nodeInd in range(0, numNodes, 1):
		xyObject = session.XYDataFromHistory(name=k + '_NODE_' + str(cSet.nodes[nodeInd].label),
											 odb=curr_odb,
											 outputVariableName=v['S1'] + v['VARIABLE'] + v['S2'] +
																str(cSet.nodes[nodeInd].label) +
																v['S3'] + v['SET'],
											 steps=(lastStepKey,), )
# ##GET LIST OF DIC KEYS
var_keys = variable_dic.keys()
# ##LIST OF XY DATA OBJECT KEYS (WE NEED TO SUM SOME OF THE XY DATA OBJECTS PRIOR TO EXPORTING)
xyData_keys = session.xyDataObjects.keys()
# ## COLLATE SIMILAR ITEMS, RETURN DIC KEY IT ITEM OF INTEREST AND VALUE IS LIST OF SIMILAR XY DATA OBJECTS
field_dic = get_fieldnames(var_keys, xyData_keys)
# ##SORT THE RESULTS INTO FORMAT (SUMMATION)
results_dic = {}  # EMPTY DIC TO HOLD RESULTS
for k in field_dic.keys():
	# ## GET X DATA FROM THE FIRST XYDATA OBJECT REMAINS IDENTICAL FOR SUBSEQUENT FIELDNAMES/ITEMS
	# ## LIST OF TIME VALUES
	xData = [i[0] for i in session.xyDataObjects[field_dic[k][0]]]
	# ## EMPTY LIST TO HOLD YDATA VALUES THIS WILL BE POPULATED AS SHOWN BELOW
	yData = []
	# ## IF DICTIONARY LIST ONLY HAS ONE ITEM THEN THERE IS SINGLE XY PAIR AND WE CAN GRAB Y
	if len(field_dic[k]) == 1:
		# LIST OF Y VALUES
		yData = [i[1] for i in session.xyDataObjects[field_dic[k][0]]]
	# ## IF DICTIONARY LIST HAS MORE THAN ONE ITEM THEN
	# ## WE WANT TO FIND EACH X AND GET ALL Y VALUES ASSOCIATED WITH THAT X VALUE
	elif len(field_dic[k]) > 1:
		for i in range(0, len(xData), 1):  # indexer to access specific X time data
			yAtX = []  # EMPTY LIST TO HOLD Y VALUES TO BE SUMMED
			for fieldName in field_dic[k]:  # LOOP ALL FIELDNAMES
				field = session.xyDataObjects[fieldName]  # access the object
				yAtX.append(field[i][1])
			# NOW WE SUM THE YATX LIST AND HOLD THE SUMMED VALUE IN THE YDATA LIST
			yData.append(abs(sum(yAtX)))
	# ##HOLD RESULTS IN RESULTS DICTIONARY
	# ##ONLY HOLD VALUES IF FIELD DICTIONARY HAS SOME XYDATAOBJECTS
	if field_dic[k]:
		# ##WHERE X IS TIME AND Y ARE VALUES
		results_dic[k] = {'X': xData, 'Y': yData}
# ##FORMAT THE RESULTS DICTIONARY OUTPUT FORCE VERSUS DISPLACEMENT IN Y-DIR (ELONGATION)
final = {'RF': results_dic['RF']['Y'], 'U': results_dic['UY']['Y']}
# ##CALCULATE THE FINAL NECK DIAMETER
final_neck = (min(results_dic['UX']['Y']) + 2) * 2
# ##WRITE THE LOAD-DISP DATA (FINAL DIC) TO CSV
res_filename = job_name + '_LD_DATA.csv'
write_csv_py27(os.getcwd(), res_filename, final)
# ##RETURN FILENAME AND THE NECK DIAMETER TO MAIN SCRIPT
sys.__stderr__.write(res_filename)
sys.__stderr__.write('\n')
sys.__stderr__.write(str(final_neck))
