# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import math
import subprocess
import ast
import csv

class functionsDymola():

    #run the system
    def runSimulation(self, modelfilepathname, mAPD):
        #create a folder in which the simulation will take place
        simpath = os.path.splitext(modelfilepathname)[0]
        if not os.path.exists(simpath):
            os.makedirs(simpath)
        #move the model in the newly created folder
        modelfilename = os.path.basename(modelfilepathname)
        newmodelfilepathname = os.path.join(simpath, modelfilename)
        shutil.move(modelfilepathname, newmodelfilepathname)
        #copy the modelbase in the newly created folder
        modelbasefilespathname = mAPD.get("modelbase")
        newmodelbasefilespathname = []
        for modelbasefilepathname in modelbasefilespathname:
            modelbasefilename = os.path.basename(modelbasefilepathname)
            newmodelbasefilepathname = os.path.join(simpath, modelbasefilename)
            newmodelbasefilespathname.append(newmodelbasefilepathname)
            shutil.copyfile(modelbasefilepathname, newmodelbasefilepathname)

        #create a script (batch file) for executing the simulation
        scriptfilepathname = os.path.splitext(newmodelfilepathname)[0] + ".mos"
        modelName = os.path.splitext(os.path.basename(modelfilepathname))[0]
        nSteps = math.ceil(float(mAPD.get("stoptime"))/float(mAPD.get("maxstep")))  #use number of steps instead of max step size
        with open(scriptfilepathname, "w") as fileobject:
            fileobject.write("cd(\"" + simpath + "\");\n")
            for newmodelbasefilepathname in newmodelbasefilespathname:
                fileobject.write("openModel(\"" + newmodelbasefilepathname + "\");\n")
            #fileobject.write("cd(\"" + simpath + "\");\n")
            fileobject.write("openModel(\"" + newmodelfilepathname + "\");\n")
            fileobject.write("Modelica.Utilities.System.setWorkDirectory(\"" + simpath + "\");\n")
            fileobject.write("simulateModel(problem=\"" + modelName + "\", startTime=" + mAPD.get("starttime") + ", ")
            fileobject.write("method=\"" + mAPD.get("solver") + "\", numberOfIntervals=" + str(nSteps) + ", ")
            fileobject.write("stopTime=" + mAPD.get("stoptime") + ", resultFile=\"" + modelName + "\");\n")
            fileobject.write("Modelica.Utilities.System.exit();\n")

        #now run the script - start and wait until done
        retcode = subprocess.call(["dymola", "-nowindow", scriptfilepathname])
        print("The simulation of the model " + modelName + " was executed by Dymola returning " + str(retcode) + ".")

        #the result is given as .mat file -> export as csv using the program alist.exe shipped with Dymola (in the same directory as Dymola.exe)
        #alist.exe -h lists help, just convert signals of interest
        signalsToConvertList = ast.literal_eval(mAPD.get("nsigana"))
        matresfile = os.path.splitext(newmodelfilepathname)[0] + ".mat"
        csvresfile = os.path.splitext(newmodelfilepathname)[0] + ".csv"
        convertString = "alist "
        for var in signalsToConvertList:
            convertString = convertString + "-e " + str(var) + " "  #the time is appended automatically
        convertString = convertString + matresfile + " " + csvresfile
        retcode = subprocess.call(convertString)
        print("The output of the simulation of the model " + modelName + " was converted to csv by Dymola's alist.exe returning " + str(retcode) + ".")

        #return the results file
        return csvresfile

    #get the results
    def getResults(self, resultsfile):
        with open(resultsfile, 'r') as rf:
            reader = csv.reader(rf)
            signalValuesList = list(reader)
        return signalValuesList