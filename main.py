# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts, University of Applied Sciences Wismar, RG CEA'

import sys
from time import strftime
import subprocess
import multiprocessing as mp
import os
import shutil

from functionsSimulink import *
from functionsOpenModelica import *
from functionsDymola import *

__version__ = strftime("%Y"+"."+"%m"+"."+"%d") #for development
#__version__ = str(1.0)

"""
This program is written in Python3 with the Qt5 bindings PyQt5
The project has been started using Python3.4.1 and PyQt5.5 and is running with current versions of Python3 and PyQt5.

Start the Execution Unit SESEuPy, it is assumed that the models created with SESMoPy are located in the folder passed as first argument.
The second argument (optional) is either True or False depending on whether the models shall be deleted after simulation. True = delete models after simulation
python3 main.py ~/HDD/Promotion/SES_Tests/BuildTest_models
python3 main.py ~/HDD/Promotion/SES_Tests/BuildTest_models True|False
"""


#simulation of the model: function for needed steps in sequential and parallel
def toExecuteSequentialOrParallel(q, mAPD, i, sFO):
    modelFileToExecute = mAPD.get("models")[i]
    print("Executing the model " + os.path.basename(modelFileToExecute))
    print("The main process ID is " + str(os.getppid()) + ". The process ID (of the current simulation run) is " + str(os.getpid()) + ".")

    resultfile = sFO.runSimulation(sFO, modelFileToExecute, mAPD)
    result = sFO.getResults(sFO, resultfile)
    q.put([modelFileToExecute, result]) #put result in queue

def ExecutionUnit(modelfolder, deleteModelFolders=False):
    # read the configuration file and create a dictionary of the config file
    conffile = os.path.join(modelfolder, "config.txt")
    modelsAndParamDict = {}
    modelnameparamlines = []
    modellines = []
    mblines = []
    simulator = ""
    execution = ""
    sesvar = []
    try:
        with open(conffile) as fileobject:  # it is closed after finishing the block, even if an exception is raised
            config = fileobject.read()
        configsplit = config.split("\n")

        for co in configsplit:
            if co[0:8] == "SESVAR: ":
                sesvar.append(co[8:])
            elif co[0:16] == "MODELNAMEPARAM: ":
                modelnameparamlines.append(co[16:])
            elif co[0:7] == "MODEL: ":
                modellines.append(co[7:])
                modelsAndParamDict.update({"models": modellines})  # list of models including their path as in the configuration file   ["/Path/to/Model1.slx", "/Path/to/Model1.slx", ...]
            elif co[0:11] == "SIMULATOR: ":
                simulator = co[11:]  # "Simulink", "OpenModelica" or "Dymola"
            elif co[0:11] == "INTERFACE: ":
                modelsAndParamDict.update({"interface": co[11:]})
            elif co[0:11] == "MODELBASE: ":
                mblines.append(co[11:])
                modelsAndParamDict.update({"modelbase": mblines})  # complete paths to the files containing the modelbase
            elif co[0:11] == "STARTTIME: ":
                modelsAndParamDict.update({"starttime": co[11:]})  # starttime of the simulation
            elif co[0:8] == "SOLVER: ":
                modelsAndParamDict.update({"solver": co[8:]})  # e.g. "ode45" for Simulink and "dassl" for OpenModelica or Dymola
            elif co[0:10] == "STOPTIME: ":
                modelsAndParamDict.update({"stoptime": co[10:]})  # stoptime of the simulation
            elif co[0:9] == "MAXSTEP: ":
                modelsAndParamDict.update({"maxstep": co[9:]})  # maximum stepwidth for the simulation
            elif co[0:10] == "EXECTYPE: ":
                execution = co[10:]  # the execution can be "sequential" or "parallel"
            elif co[0:9] == "NSIGANA: ":
                modelsAndParamDict.update({"nsigana": co[9:]})  # the names of the signals to analyze in the simulation output (for OpenModelica & Dymola)
    except:
        modelsAndParamDict = {}
        print("The configuration file for the model execution could not be read. Is the folder correct? Please look at the documentation!")

    # check if all necessary entries are found
    executable = True
    if not modelsAndParamDict.get("models"):
        executable = False
    elif simulator == "":
        executable = False
    elif modelsAndParamDict.get("interface") == "native" and not modelsAndParamDict.get("modelbase"):
        executable = False
    elif not modelsAndParamDict.get("starttime"):
        executable = False
    elif not modelsAndParamDict.get("solver"):
        executable = False
    elif not modelsAndParamDict.get("stoptime"):
        executable = False
    elif not modelsAndParamDict.get("maxstep"):
        executable = False
    elif execution == "":
        executable = False
    elif not modelsAndParamDict.get("nsigana") and (simulator == "OpenModelica" or simulator == "Dymola"):
        executable = False

    # check some values, whether they have the right format
    if executable:
        try:
            float(modelsAndParamDict.get("starttime"))
            float(modelsAndParamDict.get("stoptime"))
            float(modelsAndParamDict.get("maxstep"))
        except:
            executable = False

    # execute, if executable
    if not executable:  # it may not be empty
        print("The models cannot be executed, since the models and parametrizations cannot be found or are not correct, e.g. the simulation starttime, the simulation stoptime or the maximal stepsize cannot be interpreted as float.")
        return []
    else:
        # create an object of the right functions to use
        simulatorFunObj = None
        if simulator == "Simulink":
            simulatorFunObj = functionsSimulink
        elif simulator == "OpenModelica":
            simulatorFunObj = functionsOpenModelica
        elif simulator == "Dymola":
            simulatorFunObj = functionsDymola
        else:
            print("No supported simulator!")

        # try to find the simulator to use on the disk
        simulatorFound = True
        if simulator == "Simulink":
            # subprocess.check_output(["matlab", "-nodesktop", "-nosplash", "-r", "ver('simulink')"], shell=True)
            print("Currently it can not be checked automatically whether Simulink is installed.")
            print("Please make sure that Simulink is installed by starting Matlab and using the command ver('simulink') in the Matlab command window in case there are problems during execution.")
            print("For Windows, please make sure, that the bin folder of Matlab is on the path of the user / system and restart this program.")
            print("For Linux, please make sure, that Matlab can be started with the command 'matlab' from the Shell. Otherwise place a symbolic link to the Matlab executable with the name 'matlab' in the /usr/bin folder.\n")
        elif simulator == "OpenModelica":
            try:
                subprocess.check_output(["omc", "--version"], shell=True)
            except:
                simulatorFound = False
                print("The selected simulator can not be found.")
                print("For Windows, please make sure, that the bin folder of OpenModelica is on the path of the user / system and restart this program.")
                print("For Linux, please make sure, that the OpenModelica command 'omc' is startable from the Shell. Otherwise place a symbolic link to the omc executable with the name 'omc' in the /usr/bin folder.\n")
        elif simulator == "Dymola":
            # subprocess.check_output(["dymola", "-nowindow"], shell=True)
            print("Currently it can not be checked automatically whether Dymola is installed.")
            print("In case there are problems during execution:")
            print("For Windows, please make sure, that the bin or bin64 folder of Dymola is on the path of the user / system and restart this program.")
            print("For Linux, please make sure, that Dymola can be started with the command 'dymola' from the Shell. Otherwise place a symbolic link to the Dymola executable with the name 'dymola' in the /usr/bin folder.\n")

        # simulate the models
        if simulatorFound:

            #Dymola cannot be executed in parallel (probably because Dymola itself starts several parallel processes -> in Windows PowerShell: dymola -nowindow ScriptToExecute.mos | Out-Null -> in Windows Command: START /WAIT dymola -nowindow ScriptToExecute.mos -> in Python seems to be impossible)
            if simulator == "Dymola" and execution == "parallel":
                execution = "sequential"
                print("Currently simulation with Dymola cannot be executed in parallel. Switching to sequential execution for Dymola.\n")

            #prepare the execution
            q = mp.Queue()  # queue for the results
            numToExecute = len(modelsAndParamDict.get("models"))
            processes = []  # list of processes -> needed for joining later

            if execution == "sequential":
                for i in range(numToExecute):
                    toExecuteSequentialOrParallel(q, modelsAndParamDict, i, simulatorFunObj)
            elif execution == "parallel":
                mp.set_start_method('spawn', force=True)
                for i in range(numToExecute):
                    p = mp.Process(target=toExecuteSequentialOrParallel, args=(q, modelsAndParamDict, i, simulatorFunObj,))
                    processes.append(p)
                    p.start()

            # get the results from the queue
            results = []
            resultsOk = True
            for i in range(numToExecute):
                resFromQueue = q.get()
                if resFromQueue:
                    results.append(resFromQueue)
                else:
                    resultsOk = False

            #make sure the child processes terminate and go on with the parent
            for p in processes:
                p.join()

            if resultsOk:
                print("\nThe simulation is finished.\n")

                # create resultfile
                resultfile = modelfolder+".csv"

                #write the first line -> modelname (and path, if the model will not be deleted)
                fileobject = open(resultfile, "w")
                modelnameparamlinessort = []    #sorted modelnameparamlines according to the order in results
                for i in range(len(results)):   #first line
                    #get the modelname (and path, if the model will not be deleted) to write
                    if deleteModelFolders:  # the simulation folders (and so the model) are deleted anyway, so do not write the whole path to the modelfile in the result
                        mn = os.path.basename(results[i][0])
                        mc = os.path.splitext(mn)[0]
                    else:
                        mn = results[i][0]
                        mc = os.path.splitext(os.path.basename(mn))[0]
                    fileobject.write(mn)
                    #sort the modelnameparamlines according to the order in results
                    for k in range(len(modelnameparamlines)):
                        if mc == modelnameparamlines[k].split(" ")[0]:
                            modelnameparamlinessort.append(modelnameparamlines[k])
                    #write the commas depending on the number of
                    for j in range(len(results[i][1][0])-1):
                        fileobject.write(",")
                    fileobject.write(";")
                fileobject.write("\n")

                #write the parameterization
                sesvarstr = "SESvar"
                for i in range(len(sesvar)):
                    sesvarstr = sesvarstr + " #" + sesvar[i].replace(" = ","=")
                for i in range(len(modelnameparamlinessort)):
                    fileobject.write(modelnameparamlinessort[i])
                    for j in range(len(results[i][1][0])-2):
                        fileobject.write(",")
                    fileobject.write(',' + sesvarstr)
                    fileobject.write(";")
                fileobject.write("\n")

                #write the headings and the simulation results
                for j in range(len(results[0][1])):   #third line and rest
                    line = ""
                    for i in range(len(results)):
                        line = line + ",".join(results[i][1][j]) + ";"
                    fileobject.write(line + "\n")

                fileobject.close()

                #delete the simulation folder
                if modelsAndParamDict.get("interface") == "FMI" and deleteModelFolders:
                    print("The modelfolders cannot be deleted by SESEuPy when using FMI.\n")
                elif deleteModelFolders:
                    shutil.rmtree(modelfolder)

                print("SESEuPy has finished all work.\nRESULTFILE: " + resultfile)

            else:
                print("Not OK - An error during simulation occurred. The simulation directories were not deleted. The last one should contain the model not being able to be executed.\n"
                      "In case the simulation is done with Simulink, try to execute the created .m script in Matlab and find the errors.\n"
                      "In case the simulation is done with OpenModelica, execute the created .mos script from the command/shell using the command 'omedit scriptname.mos'."
                      "In case the simulation is done with Dymola, execute the created .mos script from the command/shell using the command 'dymola scriptname.mos'.")

        else:
            print("Not OK - Simulator not found!")

if __name__ == '__main__':
    # for test of one directory not using the API -> comment out lines beginning with if len(sys.argv) == 3: up to line printHowToCall = True
    # comment out the lines beginning with "printHowToCall = False" until the end of this file
    #modelfolder = "C:\\Users\\win10\\Desktop\\SES_MB\\SES_Feedback_p_feedforwarde0_f_models"   #this is the path to the folder with the models created with SESMoPy, in which also the config.txt lies
    #modelDelete = False
    #ExecutionUnit(modelfolder, modelDelete)

    #get the arguments the program is called with
    printHowToCall = False
    modelfolder = ""
    modelDelete = False

    if len(sys.argv) in [2, 3]:
        modelfolder = sys.argv[1]
        if len(sys.argv) == 3:
            modelDelete = sys.argv[2]
            if modelDelete == "True":
                modelDelete = True
            elif modelDelete == "False":
                modelDelete = False
            else:
                printHowToCall = True
    else:
        printHowToCall = True

    if printHowToCall:
        print("Call the execution unit with the folder containing the models and the config.txt file as first argument. The second argument (optional) are the words True or False depending on whether you want to delete the simulation folder after modeling. True deletes the folder.\nExample: python3 main.py ~/HDD/Promotion/SES_Tests/BuildTest_models   or   python3 main.py ~/HDD/Promotion/SES_Tests/BuildTest_models True")
    else:
        # call the Execution Unit function
        ExecutionUnit(modelfolder, modelDelete)
    