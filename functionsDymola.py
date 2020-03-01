# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import math
import subprocess
import ast
import csv
import platform

class functionsDymola():

    #run the system
    def runSimulation(self, modelfilepathname, mAPD):
        #set the system
        syst = platform.system()

        #old approach: for every simulation an own folder is created in which the simulation takes place
        #for FMI each basic model is exported as FMU and the FMUs form the modelbase, the modelname one FMU belongs to is written in brackets in the config file
        """
        #create a folder in which the simulation will take place
        simpath = os.path.splitext(modelfilepathname)[0]
        if not os.path.exists(simpath):
            os.makedirs(simpath)
        #copy the model in the newly created folder
        modelfilename = os.path.basename(modelfilepathname)
        newmodelfilepathname = os.path.join(simpath, modelfilename)
        #shutil.move(modelfilepathname, newmodelfilepathname)
        shutil.copyfile(modelfilepathname, newmodelfilepathname)
        #copy the modelbase in the newly created folder
        modelbasefilespathname = mAPD.get("modelbase")
        newmodelbasefilespathname = []
        interface = "native"
        for modelbasefilepathname in modelbasefilespathname:
            if not modelbasefilepathname[0] == "(":  # native interface is used
                modelbasefilename = os.path.basename(modelbasefilepathname)
                newmodelbasefilepathname = os.path.join(simpath, modelbasefilename)
                newmodelbasefilespathname.append(newmodelbasefilepathname)
                shutil.copyfile(modelbasefilepathname, newmodelbasefilepathname)
            else:   #FMI interface is used
                interface = "FMI"
                formodel, mbpathname = modelbasefilepathname.split(") ")
                formodel = formodel[1:]
                if os.path.basename(formodel) == modelfilename:
                    modelbasefilename = os.path.basename(mbpathname)
                    copyfolder = os.path.split(mbpathname)[0]
                    newmodelbasefilepathname = os.path.join(simpath, os.path.split(copyfolder)[1], modelbasefilename)
                    newmodelbasefilespathname.append(newmodelbasefilepathname)
                    newcopyfolder = os.path.join(simpath, os.path.split(copyfolder)[1])
                    if os.path.exists(newcopyfolder):
                        shutil.rmtree(newcopyfolder)
                    shutil.copytree(copyfolder, newcopyfolder)

        #create a script (batch file) for executing the simulation
        scriptfilepathname = os.path.splitext(newmodelfilepathname)[0] + ".mos"
        modelName = os.path.splitext(os.path.basename(modelfilepathname))[0]
        nSteps = math.ceil(float(mAPD.get("stoptime"))/float(mAPD.get("maxstep")))  #use number of steps instead of max step size
        with open(scriptfilepathname, "w") as fileobject:
            simpath = simpath.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
            fileobject.write("cd(\"" + simpath + "\");\n")
            for newmodelbasefilepathname in newmodelbasefilespathname:
                newmodelbasefilepathname = newmodelbasefilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
                fileobject.write("openModel(\"" + newmodelbasefilepathname + "\");\n")
            #fileobject.write("cd(\"" + simpath + "\");\n")
            newmodelfilepathname = newmodelfilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
            fileobject.write("openModel(\"" + newmodelfilepathname + "\");\n")
            fileobject.write("Modelica.Utilities.System.setWorkDirectory(\"" + simpath + "\");\n")
            fileobject.write("simulateModel(problem=\"" + modelName + "\", startTime=" + mAPD.get("starttime") + ", ")
            fileobject.write("method=\"" + mAPD.get("solver") + "\", numberOfIntervals=" + str(nSteps) + ", ")
            fileobject.write("stopTime=" + mAPD.get("stoptime") + ", resultFile=\"" + modelName + "\");\n")
            fileobject.write("Modelica.Utilities.System.exit();\n")
        """

        #new approach: the simulation takes place in the modelfolder and not in an own directory

        #create a script (batch file) for executing the simulation
        simpath = os.path.split(modelfilepathname)[0]
        scriptfilepathname = os.path.splitext(modelfilepathname)[0] + ".mos"
        modelName = os.path.splitext(os.path.basename(modelfilepathname))[0]
        nSteps = math.ceil((float(mAPD.get("stoptime")) - float(mAPD.get("starttime"))) / float(mAPD.get("maxstep")))  # use number of steps instead of max step size
        with open(scriptfilepathname, "w") as fileobject:
            #change the directory for the simulation to the modelfolder
            simpath = simpath.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
            if syst != "Windows":
                simpath = simpath.replace("\\", "/")
            fileobject.write("cd(\"" + simpath + "\");\n")
            #go through the modelbase entries and append them to load
            modelbasefilespathname = mAPD.get("modelbase")
            for modelbasefilepathname in modelbasefilespathname:
                if mAPD.get("interface") == "native":  # for the native interface the modelbase files need to be loaded
                    modelbasefilepathname = modelbasefilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
                    if syst != "Windows":
                        modelbasefilepathname = modelbasefilepathname.replace("\\", "/")
                    fileobject.write("openModel(\"" + modelbasefilepathname + "\");\n")
                else:   #for FMI the whole model is an FMU (which is imported in Dymola and therefore is a .mo file) needs to be loaded, the modelname one FMU belongs to is written in brackets in the config file
                    formodel, mbpathname = modelbasefilepathname.split(") ")  #the entry in the config file
                    formodel = formodel[1:]
                    mbpathname = mbpathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
                    modelfilename = os.path.basename(modelfilepathname)  #the model to simulate
                    if os.path.basename(formodel) == modelfilename:
                        if syst != "Windows":
                            mbpathname = mbpathname.replace("\\", "/")
                        fileobject.write("openModel(\"" + mbpathname + "\");\n")
            #add the model to load
            modelfilepathnameDy = modelfilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
            if syst != "Windows":
                modelfilepathnameDy = modelfilepathnameDy.replace("\\", "/")
            fileobject.write("openModel(\"" + modelfilepathnameDy + "\");\n")
            #configuration and simulation execution
            fileobject.write("Modelica.Utilities.System.setWorkDirectory(\"" + simpath + "\");\n")
            fileobject.write("simulateModel(problem=\"" + modelName + "\", startTime=" + mAPD.get("starttime") + ", ")
            fileobject.write("method=\"" + mAPD.get("solver") + "\", numberOfIntervals=" + str(nSteps) + ", ")
            fileobject.write("stopTime=" + mAPD.get("stoptime") + ", resultFile=\"" + modelName + "\");\n")
            fileobject.write("Modelica.Utilities.System.exit();\n")

        #now run the script - start and wait until done
        retcode = subprocess.call(["dymola", "-nowindow", scriptfilepathname])

        #child = subprocess.Popen(["dymola", "-nowindow", scriptfilepathname], stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  #try with subprocess.Popen, but no success when executed in parallel
        #(stdout, stderr) = child.communicate()
        #retcode = stdout.decode()
        #if retcode == "":
            #retcode = str(0)

        print("The simulation of the model " + modelName + " was executed by Dymola returning " + str(retcode) + ".")

        #the result is given as .mat file -> export as csv using the program alist.exe shipped with Dymola (in the same directory as Dymola.exe)
        #alist.exe -h lists help, just convert signals of interest
        try:
            signalsToConvertList = ast.literal_eval(mAPD.get("nsigana"))
            signalsToConvertListOrig = signalsToConvertList[:]  # make a copy
            """
            #old (before exporting a whole model as FMU)
            if mAPD.get("interface") == "FMI":  #for FMI the blocknames have an attached 1 -> this needs to be done to the signals to convert as well
                for sig in range(len(signalsToConvertList)):
                    signalsToConvertList[sig] = signalsToConvertList[sig].split(".")[0] + "1." + signalsToConvertList[sig].split(".")[1]
            """
            if mAPD.get("interface") == "FMI":  # for FMI the signals are like this: "sourceSys.y" becomes to "<modelname>.sourceSysOut" -> this needs to be done to the signals to convert as well
                for sig in range(len(signalsToConvertList)):
                    for modelbasefilepathname in modelbasefilespathname:
                        formodel, mbpathname = modelbasefilepathname.split(") ")    #the entry in the config file
                        formodel = formodel[1:]
                        modelfilename = os.path.basename(modelfilepathname) #the model to simulate
                        if os.path.basename(formodel) == modelfilename:
                            mbname = os.path.splitext(os.path.basename(mbpathname))[0]
                            blockToConvert = signalsToConvertList[sig].split(".")[0]
                            portToConvert = signalsToConvertList[sig].split(".")[1]
                            signalsToConvertList[sig] = mbname + "1." + blockToConvert + "_" + portToConvert + "_Out"
            matresfile = os.path.splitext(modelfilepathname)[0] + ".mat"
            csvresfile = os.path.splitext(modelfilepathname)[0] + ".csv"
            convertString = "alist "
            for var in signalsToConvertList:
                convertString = convertString + "-e " + str(var) + " "  #the time is appended automatically
            convertString = convertString + matresfile + " " + csvresfile
            retcode = subprocess.call(convertString)
            #for FMI change the original signalnames in the csv resultfile back again (they were changed for simulation with FMI)
            if mAPD.get("interface") == "FMI":
                #read the csvresfile
                reader = csv.reader(open(csvresfile, 'r'))
                lines = list(reader)
                #manipulate the csvresfile
                for line in lines:
                    for l in range(len(line)):
                        if "." in line[l]:  # only continue if the element valuesLineSignalsToKeep[vLSK] contains a dot at all
                            for sTKLO in signalsToConvertListOrig:
                                try:
                                    signOrig = sTKLO.split(".")[0] + "_" + sTKLO.split(".")[1] + "_Out"
                                    signChan = line[l].split(".")[1]
                                    if signOrig == signChan:
                                        line[l] = sTKLO
                                except:
                                    pass
                #write the csvresfile
                writer = csv.writer(open(csvresfile, 'w', newline=''))
                writer.writerows(lines)
            print("The output of the simulation of the model " + modelName + " was converted to csv by Dymola's alist.exe returning " + str(retcode) + ".")
        except:
            csvresfile = ""

        #return the results file
        return csvresfile

    #get the results
    def getResults(self, resultsfile):
        try:
            with open(resultsfile, 'r') as rf:
                reader = csv.reader(rf)
                signalValuesList = list(reader)
            return signalValuesList
        except:
            return []