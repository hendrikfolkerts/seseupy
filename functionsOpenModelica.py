# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import math
import subprocess
import ast
import csv

class functionsOpenModelica():

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
        #copy the modelbases in the newly created folder
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
            fileobject.write("loadModel(Modelica);\n")
            for newmodelbasefilepathname in newmodelbasefilespathname:
                fileobject.write("loadFile(\"" + newmodelbasefilepathname + "\");\n")
            fileobject.write("loadFile(\"" + newmodelfilepathname + "\");\n")
            fileobject.write("simulate(" + modelName + ", startTime=" + mAPD.get("starttime") + ", ")
            fileobject.write("method=\"" + mAPD.get("solver") + "\", numberOfIntervals=" + str(nSteps) + ", ")
            fileobject.write("outputFormat=\"csv\", ")
            fileobject.write("stopTime=" + mAPD.get("stoptime") + ", fileNamePrefix=\"" + modelName + "\");\n")

        #now run the script - start and wait until done
        retcode = subprocess.call(["omc", scriptfilepathname])
        print("The simulation of the model " + modelName + " was executed by OpenModelica returning " + str(retcode) + ".")

        #just keep the signals of interest
        signalsToKeepList = ast.literal_eval(mAPD.get("nsigana"))
        csvresfile = os.path.splitext(newmodelfilepathname)[0] + "_res.csv"
        newcsvresfile = os.path.splitext(newmodelfilepathname)[0] + ".csv"
        with open(csvresfile, 'r') as inp, open(newcsvresfile, 'w', newline='') as out:
            reader = csv.reader(inp)
            writer = csv.writer(out)
            #get the column numbers to keep
            firstline = next(reader)
            columnsToKeep = [0] #keep column 0 definitely (time)
            for sig in range(len(firstline)):
                if firstline[sig] in signalsToKeepList:
                    columnsToKeep.append(sig)
            #return to the beginning of the file to read first line again (for writing the header now)
            inp.seek(0)
            #now write the resultfile
            for row in reader:
                valuesLineSignalsToKeep = []
                for ci in range(len(row)):
                    if ci in columnsToKeep:
                        valuesLineSignalsToKeep.append(row[ci])
                writer.writerow(valuesLineSignalsToKeep)
        print("The output of the simulation of the model " + modelName + " was reduced only keeping signals of interest.")

        #return the results file
        return newcsvresfile

    #get the results
    def getResults(self, resultsfile):
        with open(resultsfile, 'r') as rf:
            reader = csv.reader(rf)
            signalValuesList = list(reader)
        return signalValuesList