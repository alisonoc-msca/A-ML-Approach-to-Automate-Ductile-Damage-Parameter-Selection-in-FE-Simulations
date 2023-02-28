import sys
import os
import numpy as np
import math as m
import csv
import json

from abaqus import *
from abaqusConstants import *
from caeModules import *
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from regionToolset import *

properties_file = sys.argv[-3] # ##PLASTIC PROPERTIES UP TO UTS ONLY
sim_num = sys.argv[-2] # ##JOB NUMBER
jfile = sys.argv[-1] # ##DICTIONARY OF SPECIMEN INFO

def read_material_properties(properties_file):
    file = open(properties_file, 'r')
    # ##EACH LINE RETURNED AS STRING WITH \N
    lines = file.readlines()
    # ##REMOVE HEADERS
    lines = lines[1:]
    f = []
    for cline in lines:
        # ##GET THE STRING OF EACH LINE
        cline = cline.rstrip().format(cline)
        # ##SPLIT THE STRING INTO X, Y COMPONENTS
        xy_list = cline.split(',')
        # ##FLOAT VALUES AND ROUND TO SIGNIF FIGURE
        xy_list = tuple([float(i) for i in xy_list])
        f.append(xy_list)
    return f

def load_json_file(j_file):
    with open(j_file) as json_file:
        return json.load(json_file)

# ##READ IN DICTIONARY OF DATA FROM TXT FILE (CANNOT PASS VIA CLI)
data_dic = load_json_file(jfile)
# ##READ THE PLASTIC PROPERTIES
plastic_properties = read_material_properties(properties_file)


########################################################
# START BUILD
########################################################
# SET JOURNAL OPTIONS
session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)
myViewport = session.Viewport(name='Viewport: 1')
myModelString = 'MODEL_' + str(sim_num)
########################################################
# CREATE MODEL
########################################################
myModel = mdb.Model(name=myModelString)
########################################################
# CREATE SKETCH OF PART
########################################################
rodSketch = myModel.ConstrainedSketch(name='rodProfile', sheetSize=200)
# ##THERE IS NO POINT TO MODELLING THE ENTIRE LOADING BAR GEOM. WE SHOULD REMOVE THREADED SECTION.
virt_length = data_dic['SPECIMEN_LENGTH'] - (data_dic['THREADED_LENGTH']*2)
# ##FOR AXISYM MODELS YOU MUST HAVE A CONSTRUCTION LINE
rodSketch.ConstructionLine(point1=(0, 0),
                           point2=(0, virt_length))
# ##AXI LINE VERTICAL
rodSketch.Line(point1=(0, 0),
               point2=(0, virt_length/2))
# ##HORIZONTAL UPPER
rodSketch.Line(point1=(0, virt_length/2),
               point2=(data_dic['CONN_DIAMETER']/2, virt_length/2))
# ##USE TRIG CALCULATE THE ENDPOINT OF THE ARC ON THE SECOND POINT (KNOW X=2.5 BUT DON'T KNOW Y)
# ##GET X DISTANCE BETWEEN POINT1 AND POINT2
x_dist = (data_dic['CONN_DIAMETER']/2) - (data_dic['GAUGE_DIAMETER']/2)
y_dist = data_dic['GAUGE_LENGTH']/2
hyp = data_dic['ROUND_RADIUS']
adj = data_dic['ROUND_RADIUS'] - x_dist
# ##IF X DIST IS POSITIVE THEN USE COS
if x_dist > 0:
    theta = np.arccos((adj/hyp))
    y_coord = y_dist + (hyp * np.sin((theta)))
else:
    theta = np.arcsin((adj/hyp))
    y_coord = y_dist + (hyp * np.cos((theta)))
# ##RHS VERTICAL CONNECTION SECTION
rodSketch.Line(point1=(data_dic['CONN_DIAMETER']/2, y_coord),
               point2=(data_dic['CONN_DIAMETER']/2, virt_length/2))
# ##CREATE ARC
rodSketch.ArcByCenterEnds(center=((data_dic['GAUGE_DIAMETER']/2 + data_dic['ROUND_RADIUS']), data_dic['GAUGE_LENGTH']/2),
                          point1=(data_dic['GAUGE_DIAMETER']/2, data_dic['GAUGE_LENGTH']/2),
                          point2=(data_dic['CONN_DIAMETER']/2, y_coord),
                          direction=CLOCKWISE)
# ##NOTE: MODIFIED 7/10/22 TO INTRODUCE NOTCH TO THE GEOMETRY
# ##STARTER NOTCH GEOMETRY
h, w = 0.025, 0.025
# ##HORIZONTAL LOWER
rodSketch.Line(point1=(0, 0),
               point2=(data_dic['GAUGE_DIAMETER']/2 - w , 0))
rodSketch.Line(point1=(data_dic['GAUGE_DIAMETER']/2 - w , 0),
               point2=(data_dic['GAUGE_DIAMETER']/2, h))
# ##RHS VERTICAL GAUGE SECTION
rodSketch.Line(point1=(data_dic['GAUGE_DIAMETER']/2, h),
               point2=(data_dic['GAUGE_DIAMETER']/2, data_dic['GAUGE_LENGTH']/2))
########################################################
# CREATE PART FROM SKETCH
########################################################
myPart = myModel.Part(name='ROD',
                      dimensionality=AXISYMMETRIC,
                      type=DEFORMABLE_BODY)
myPart.BaseShell(sketch=rodSketch)
myPart = myModel.parts['ROD']
########################################################
# PARTITION THE GAUGE SECTION REGION
########################################################
# ##GAUGE SECTION (UNDER ARC)
s = myModel.ConstrainedSketch(name='partition', sheetSize=200)
s.Line(point1=(0, data_dic['GAUGE_LENGTH']/2),
       point2=(data_dic['GAUGE_DIAMETER']/2, data_dic['GAUGE_LENGTH']/2))
myPart.PartitionFaceBySketch(faces=myPart.faces,
                             sketch=s)
# ##LOADING ROD SECTION (OVER ARC)
s = myModel.ConstrainedSketch(name='partition', sheetSize=200)
s.Line(point1=(0, y_coord),
       point2=(data_dic['CONN_DIAMETER']/2, y_coord))
myPart.PartitionFaceBySketch(faces=myPart.faces,
                             sketch=s)
########################################################
# CREATE REFERENCE POINT FOR LOADING
########################################################
load_point = myPart.DatumPointByCoordinate(coords=(0, (virt_length/2 + 2), 0))
myPart.ReferencePoint(point=myPart.datums[load_point.id])
########################################################
# CREATE SETS
########################################################
# ##LOADING POINT
load_point = myPart.Set(name='LOADING_POINT',
                        referencePoints=myPart.referencePoints.values())
# ##SYM PLANE
myPart.Set(name='BOTTOM_EDGE',
           edges=myPart.edges.findAt(((1, 0, 0),),))
# ##COUPLE EDGE (COUPLE LOADING POINT TO TOP SURFACE)
myPart.Set(name='COUPLE_EDGE',
           edges=myPart.edges.findAt(((1, virt_length/2, 0),),))
# ##NECKING
myPart.Set(name='BOTTOM_EDGE_VERTICE',
           vertices=myPart.vertices.findAt(((data_dic['GAUGE_DIAMETER']/2 - w, 0, 0),)))
# ALL FACES
set_allfaces = myPart.Set(name='ALL_FACES',
                          faces=myPart.faces)
########################################################
# CREATE AND ASSIGN MATERIAL PROPERTIES
########################################################
material = myModel.Material(name='P91')
material.Density(table=((7.8e-6, ), ))
material.Elastic(table=((data_dic['E'], 0.3),))
# ##SWAP COLUMNS OF ARRAY
material.Plastic(table=plastic_properties)
# ## GTN PARAMETERS
material.PorousMetalPlasticity(relativeDensity=(1 - data_dic['F']),
                               table=((data_dic['Q1'],
                                       data_dic['Q2'],
                                       data_dic['Q3']),))
material.porousMetalPlasticity.VoidNucleation(table=((data_dic['EN'],
                                                      data_dic['SN'],
                                                      data_dic['FN']),))
########################################################
# CREATE AND ASSIGN MATERIAL SECTION
########################################################
myModel.HomogeneousSolidSection(material='P91',
                                name='P91',
                                thickness=None)
myPart.SectionAssignment(region=myPart.sets['ALL_FACES'],
                         sectionName='P91',
                         thicknessAssignment=FROM_SECTION)
########################################################
# INSTANCE THE PART IN THE ASSEMBLY
########################################################
myAssembly = myModel.rootAssembly
myAssembly.DatumCsysByDefault(CARTESIAN)
rodInstance = myAssembly.Instance(dependent=OFF,
                                  name='ROD',
                                  part=myPart)
########################################################
# CREATE STEP 1: INITIALISE BCs
########################################################
# FIX BOTTOM EDGE (SYMETRY) IN U2 DIR
myModel.DisplacementBC(createStepName='Initial',
                       distributionType=UNIFORM, name='X_SYM',
                       region=rodInstance.sets['BOTTOM_EDGE'],
                       u1=UNSET,
                       u2=SET,
                       u3=UNSET,
                       ur1=UNSET,
                       ur2=UNSET,
                       ur3=UNSET)
# ##COUPLE THE TOP EDGE AND THE LOADING POINT
myModel.Coupling(name='KIN_COUPLE',
                 controlPoint=rodInstance.sets['LOADING_POINT'],
                 surface=rodInstance.sets['COUPLE_EDGE'],
                 influenceRadius=WHOLE_SURFACE,
                 couplingType=KINEMATIC,
                 u1=ON,
                 u2=ON,
                 ur3=ON)
# ##RESTRAIN LOADING POINT IN THE X AND Z DIRECTIONS
myModel.DisplacementBC(createStepName='Initial',
                       distributionType=UNIFORM,
                       name='CONSTRAIN_LOADING',
                       region=rodInstance.sets['LOADING_POINT'],
                       u1=SET,
                       u2=SET,
                       ur3=SET,
                       )
########################################################
# CREATE STEP 2: APPLY VERTICAL DISPLACEMENT
########################################################
myModel.ExplicitDynamicsStep(name='DISPLACEMENT',
                            previous='Initial',
                            massScaling=((SEMI_AUTOMATIC,
                                          MODEL,
                                          AT_BEGINNING,
                                          10.0,
                                          1e-5,
                                          BELOW_MIN,
                                          0,
                                          0,
                                          0.0,
                                          0.0,
                                          0,
                                          GLOBAL_NONE), ),
                            improvedDtMethod=ON)
# ##CREATE AMPLITUDE FOR DISPLACEMENT
myModel.TabularAmplitude(data=((0.0, 0.0), (1.0, 1.0)),
                         name='AMPLITUDE',
                         smooth=SOLVER_DEFAULT,
                         timeSpan=TOTAL)
# ##ADD DISPLACEMENT
myModel.DisplacementBC(createStepName='DISPLACEMENT',
                       distributionType=UNIFORM,
                       name='DISPLACEMENT',
                       region=rodInstance.sets['LOADING_POINT'],
                       u1=0,
                       u2=data_dic['MAX_DISPLACEMENT'],
                       ur3=0,
                       amplitude='AMPLITUDE')
########################################################
# CREATE FIELD OUTPUT REQUEST
########################################################
myFieldOutput = myModel.fieldOutputRequests['F-Output-1']
myFieldOutput.setValues(variables=('S',
                                   'LE',
                                   'PEEQ',
                                   'U',
                                   'RF',
                                   'COORD'))
########################################################
# CREATE HISTORY OUTPUT REQUESTS
########################################################
# DELETE ANY EXISTING HISTORY OUTPUT REQUESTS
for hist_obj in myModel.historyOutputRequests.keys():
    del myModel.historyOutputRequests[hist_obj]
# REACTION FORCE AT ORIGIN
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='RF',
                             region=rodInstance.sets['BOTTOM_EDGE'],
                             sectionPoints=DEFAULT,
                             variables=('RF2',),
                             frequency=5)
# DISPLACEMENT FROM REF POINT NODE
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='UY',
                             region=rodInstance.sets['LOADING_POINT'],
                             sectionPoints=DEFAULT,
                             variables=('U2',),
                             frequency=5)
# horizontal displacement top right node (neck)
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='UX',
                             region=rodInstance.sets['BOTTOM_EDGE_VERTICE'],
                             sectionPoints=DEFAULT,
                             variables=('U1',),
                             frequency=5)
# STRESS S22 ON BOTTOM EDGE
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='S22',
                             region=rodInstance.sets['BOTTOM_EDGE'],
                             sectionPoints=DEFAULT,
                             variables=('S22',),
                             frequency=5)
# STRAIN BOTTOM EDGE
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='LE22',
                             region=rodInstance.sets['BOTTOM_EDGE'],
                             sectionPoints=DEFAULT,
                             variables=('LE22',),
                             frequency=5)
# PLASTIC STRAIN BOTTOM EDGE
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='PEEQ',
                             region=rodInstance.sets['BOTTOM_EDGE'],
                             sectionPoints=DEFAULT,
                             variables=('PEEQ',),
                             frequency=5)
# ##INTERNAL AND KINETIC ENERGY
myModel.HistoryOutputRequest(createStepName='DISPLACEMENT',
                             name='ENERGY',
                             region=rodInstance.sets['ALL_FACES'],
                             sectionPoints=DEFAULT,
                             variables=('ALLIE', 'ALLKE'),
                             frequency=5)
#######################################################
# APPLY MESH CONTROLS
#######################################################
# GENERAL MESH CONTROLS
myAssembly.setMeshControls(elemShape=QUAD,
                           regions=rodInstance.sets['ALL_FACES'].faces,
                           technique=STRUCTURED)

# GLOBAL MESH SEEDS
myAssembly.seedPartInstance(deviationFactor=0.1,
                            minSizeFactor=0.1,
                            regions=(rodInstance,),
                            size=0.1)

# SET ELEMENT TYPE
myElem = mesh.ElemType(elemCode=CAX4R,
                       elemLibrary=STANDARD)
myAssembly.setElementType(regions=(rodInstance.faces,),
                          elemTypes=(myElem,))

# GENERATE MESH
myAssembly.generateMesh(regions=(rodInstance,))
#######################################################
# CREATE JOB
#######################################################
curr_job = mdb.Job(atTime=None,
                   contactPrint=OFF,
                   description='',
                   echoPrint=OFF,
                   explicitPrecision=SINGLE,
                   getMemoryFromAnalysis=True,
                   historyPrint=OFF,
                   memory=90,
                   memoryUnits=PERCENTAGE,
                   model=myModel,
                   modelPrint=OFF,
                   multiprocessingMode=DEFAULT,
                   name='JOB' + str(sim_num),
                   nodalOutputPrecision=SINGLE,
                   numCpus=4,
                   numDomains=4,
                   numGPUs=0,
                   queue=None,
                   resultsFormat=ODB,
                   scratch='',
                   type=ANALYSIS,
                   userSubroutine='',
                   waitHours=0,
                   waitMinutes=0)
#######################################################
# SUBMIT JOB
#######################################################
mdb.jobs[curr_job.name].submit(consistencyChecking=OFF)  # SUBMIT JOB
mdb.jobs[curr_job.name].waitForCompletion()  # IF RUNNING LOOP DONT START NEXT TILL CURRENT FINISHED
sys.__stderr__.write(curr_job.name) # ##write the job name back to CLI
