import sys
import os
import subprocess
import time
from B_SCR.error_function import *
from B_SCR.general_functions import write_json_file
from B_SCR.clean_fea_dir import delete_unwanted


def caller_type(cae, *args):
    # ##DIFFERENTIATE BETWEEN CAE AND VIEWER
    if cae:
        caller = 'abaqus cae noGui='
    else:
        caller = 'abaqus viewer database=' + args[0] + ' noGui='
    return caller


def build_command_string(script, cae, *args):
    # ## GET THE CAE/VIEWER CALLER
    caller = caller_type(cae, *args)
    caller = caller + script
    # ##STRING ALL ARGUMENTS AS INDIVIDUAL ITEMS
    str_args = [str(arg) for arg in args]
    if args:
        # ##CREATE COMMAND INITIALISER WITH CALLER
        c = ['cmd.exe', '/C', caller, '--']
        # ##APPEND STRING ARGS TO COMMAND LIST
        for arg in str_args:
            c.append(arg)
    else:
        c = ['cmd.exe', '/C', caller]
    # ##RETURN COMMAND LIST
    return c


def call_cae(cwd, aba_dir, script, *args):
    # SET CAE TO TRUE
    cae = True
    # CHANGE TO OUTPUT DIRECTORY
    os.chdir(aba_dir)
    # ##BUILD COMMAND STRING
    command = build_command_string(script, cae, *args)
    # ##RUN SUBPROCESS COMMAND
    p1 = subprocess.run(command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True)
    # ##RETURN TO ORIGINAL WORKING DIRECTORY (MAIN FILE)
    os.chdir(cwd)
    if p1.stdout == None or p1.stdout == '':
        # ##RETURN JOB NAME
        job_name = p1.stderr[p1.stderr.rfind('\n'):].strip('\n')
    else:
        abaqus_err = p1.stderr[:p1.stderr.find('\n')].strip('\n')
        p1.returncode = 1
        if 'server' in abaqus_err:
            print('Exit with error - please turn on Forticlient')
        # ##RETURN JOB NAME
        job_name = p1.stderr[p1.stderr.rfind('\n'):].strip('\n')
        print('JOB %s EXITED WITH ERROR' %(job_name))
        print(p1.stderr)
    return job_name, p1.returncode


def call_viewer(cwd, aba_dir, script, *args):
    # SET CAE TO FALSE
    cae = False
    # CHANGE TO OUTPUT DIRECTORY
    os.chdir(aba_dir)
    # ##BUILD COMMAND STRING
    command = build_command_string(script, cae, *args)
    # ##RUN SUBPROCESS COMMAND
    p1 = subprocess.run(command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True)
    # ##RETURN TO ORIGINAL WORKING DIRECTORY (MAIN FILE)
    os.chdir(cwd)
    # ##GET SYS WRITE OUT VALUES
    if p1.stdout == None or p1.stdout == '':
        output = p1.stderr.splitlines()
        # ##RETURN RESULTS FILENAME
        res_fname = output[-2]
        # ##RETURN NECK DIAMETER RESULTS
        neck_diameter = output[-1]
        return p1.returncode, res_fname, neck_diameter
    else:
        return p1.returncode


def FEA_Function(*c, **path_dic):
    ''' FUNCTION TO BUILD, EXECUTE AND POST-PROCESS ABAQUS MODELS
    *c: list of arguments
    **path_dic: dictionary of paths'''
    stime = time.time()
    print('FEA iteration %s is now starting' % (c[0]))
    # ##BUILD AND EXECUTE MODEL
    job_name, rc_cae = call_cae(path_dic['cwd'],
                                path_dic['curr_results'],
                                path_dic['build'],
                                path_dic['plastic_properties'],
                                *c)
    # ##IF THE MODEL IS COMPLETE
    if rc_cae == 0:
        print('%s has completed now post-processing' % (job_name))
        # ##POST-PROCESS ODB
        rc_odb, res_fname, neck_diameter = call_viewer(path_dic['cwd'],
                                                       path_dic['curr_results'],
                                                       path_dic['postp'],
                                                       job_name)
        # ##ADD FVD RESULTS TO PATH DICTIONARY
        path_dic[job_name + '_fvd'] = os.path.join(path_dic['curr_results'], res_fname)
        # ##WRITE PATH DIC TO RESULTS FILE
        write_json_file(dic=path_dic,
                        pth=path_dic['curr_results'],
                        filename='PATH_DIC.txt')
        # ##CONVERT NECK DIAMETER TO FLOAT VALUE
        try:
            neck_diameter = float(neck_diameter)
        except:
            print('Error neck diameter is %s this cannot be converted to float' % (neck_diameter))
            # ##change the rc_odb to error
            rc_odb = 1
        etime = time.time() - stime
        print('%s post-processing complete, abaqus analysis took %s seconds' % (job_name, etime))
    # ##MODEL DID NOT COMPLETE
    else:
        sys.exit()
    # ##CLEANUP RESULTS DIRECTORY
    delete_unwanted(path_dic['curr_results'])
    return etime, path_dic, job_name
