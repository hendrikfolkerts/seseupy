# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import math
import subprocess
import ast
import csv
import xml.etree.ElementTree as ET

class functionsOpenModelica():

    #run the system
    def runSimulation(self, modelfilepathname, mAPD):

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
        #copy the modelbases in the newly created folder
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
            fileobject.write("loadModel(Modelica);\n")
            for newmodelbasefilepathname in newmodelbasefilespathname:
                newmodelbasefilepathname = newmodelbasefilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
                fileobject.write("loadFile(\"" + newmodelbasefilepathname + "\");\n")
            newmodelfilepathname = newmodelfilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
            fileobject.write("loadFile(\"" + newmodelfilepathname + "\");\n")
            fileobject.write("simulate(" + modelName + ", startTime=" + mAPD.get("starttime") + ", ")
            fileobject.write("method=\"" + mAPD.get("solver") + "\", numberOfIntervals=" + str(nSteps) + ", ")
            fileobject.write("outputFormat=\"csv\", ")
            fileobject.write("stopTime=" + mAPD.get("stoptime") + ", fileNamePrefix=\"" + modelName + "\");\n")
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
            fileobject.write("cd(\"" + simpath + "\");\n")
            fileobject.write("loadModel(Modelica);\n")
            #go through the modelbase entries and append them to load
            modelbasefilespathname = mAPD.get("modelbase")
            for modelbasefilepathname in modelbasefilespathname:
                if mAPD.get("interface") == "native":  # for the native interface the modelbase files need to be loaded
                    modelbasefilepathname = modelbasefilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
                    fileobject.write("loadFile(\"" + modelbasefilepathname + "\");\n")
                else:   #for FMI the whole model is an FMU (which is imported in OpenModelica and therefore is a .mo file) needs to be loaded, the modelname one FMU belongs to is written in brackets in the config file
                    formodel, mbpathname = modelbasefilepathname.split(") ")    #the entry in the config file
                    formodel = formodel[1:]
                    mbpathname = mbpathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
                    modelfilename = os.path.basename(modelfilepathname) #the model to simulate
                    if os.path.basename(formodel) == modelfilename:
                        fileobject.write("loadFile(\"" + mbpathname + "\");\n")
            #add the model to load
            modelfilepathnameOM = modelfilepathname.replace("/", "\\\\").replace("\\", "\\\\").replace("\\\\\\", "\\")
            fileobject.write("loadFile(\"" + modelfilepathnameOM + "\");\n")
            #configuration and simulation execution
            fileobject.write("simulate(" + modelName + ", startTime=" + mAPD.get("starttime") + ", ")
            fileobject.write("method=\"" + mAPD.get("solver") + "\", numberOfIntervals=" + str(nSteps) + ", ")
            fileobject.write("outputFormat=\"csv\", ")
            fileobject.write("stopTime=" + mAPD.get("stoptime") + ", fileNamePrefix=\"" + modelName + "\");\n")

        #now run the script - start and wait until done
        retcode = subprocess.call(["omc", scriptfilepathname])
        print("The simulation of the model " + modelName + " was executed by OpenModelica returning " + str(retcode) + ".")

        #just keep the signals of interest
        #in the csv not all signals are printed, signals that have an alias are not printed
        #which signals are alias of another signal stands in the created ..._init.xml created in the same directory as the csv
        # -> if a signal is not in the csv, find the alias in the ..._init.xml -> try to find the alias signal in the csv
        # -> if the alias is not in the csv -> take the value in the attribute start of the alias variable in the ..._init.xml
        try:
            signalsToKeepList = ast.literal_eval(mAPD.get("nsigana"))
            signalsToKeepListOrig = signalsToKeepList[:]  # make a copy
            """
            #old (before exporting a whole model as FMU)
            if mAPD.get("interface") == "FMI":  #for FMI the blocknames have an attached 1 -> this needs to be done to the signals to keep as well
                for sig in range(len(signalsToKeepList)):
                    signalsToKeepList[sig] = signalsToKeepList[sig].split(".")[0] + "1." + signalsToKeepList[sig].split(".")[1]
            """
            if mAPD.get("interface") == "FMI":  # for FMI the signals are like this: "sourceSys.y" becomes to "<modelname>.sourceSysOut" -> this needs to be done to the signals to keep as well
                for sig in range(len(signalsToKeepList)):
                    for modelbasefilepathname in modelbasefilespathname:
                        formodel, mbpathname = modelbasefilepathname.split(") ")    #the entry in the config file
                        formodel = formodel[1:]
                        modelfilename = os.path.basename(modelfilepathname) #the model to simulate
                        if os.path.basename(formodel) == modelfilename:
                            mbname = os.path.splitext(os.path.basename(mbpathname))[0]
                            blockToKeep = signalsToKeepList[sig].split(".")[0]
                            portToKeep = signalsToKeepList[sig].split(".")[1]
                            signalsToKeepList[sig] = mbname + "1." + blockToKeep + "_" + portToKeep + "_Out"
            csvresfile = os.path.splitext(modelfilepathname)[0] + "_res.csv"
            csvresfileExtended = os.path.splitext(modelfilepathname)[0] + "_res_ext.csv"
            xmlinitfile = os.path.splitext(modelfilepathname)[0] + "_init.xml"
            #add needed signals to the csvresfile that are not in the csvresfile because they are an alias of another signal
            with open(csvresfile, 'r') as inpcsv:
                csvreader = csv.reader(inpcsv)
                #firstcsvline = next(csvreader
                csvres = []
                for row in csvreader:
                    csvres.append(row)
                firstcsvline = csvres[0]

                for sig in signalsToKeepList:
                    if sig not in firstcsvline: #the signal is not in the csv -> append it
                        #first find it in the xml
                        tree = ET.parse(xmlinitfile)
                        #use XPath to find in the xml
                        scalVarElemSig = tree.find('ModelVariables/ScalarVariable[@name="'+str(sig)+'"]')
                        attribScalVarDict = scalVarElemSig.attrib
                        varAlias = attribScalVarDict.get('alias')
                        varAliasVar = attribScalVarDict.get('aliasVariable')    #the alias variable of the sig variable
                        #either the alias variable is in the csv or not
                        if varAlias == "alias" and varAliasVar in firstcsvline:  # the alias variable is in the csv -> copy the values
                            for flsig in range(len(firstcsvline)):
                                if firstcsvline[flsig] == varAliasVar:
                                    csvres[0].append(str(sig))
                                    el = 1
                                    while el < len(csvres):
                                        csvres[el].append(str(csvres[el][flsig]))
                                        el += 1
                        elif varAlias == "alias" and varAliasVar not in firstcsvline:  # the alias variable is not in the csv -> take the start value of the alias variable from the xml
                            #get the start variable from the alias in the xml
                            scalVarElemAlias = tree.find('ModelVariables/ScalarVariable[@name="' + str(varAliasVar) + '"]')
                            scalVarElemChildren = scalVarElemAlias.getchildren()
                            attrXMLStart = ""
                            for child in scalVarElemChildren:
                                attribChildDict = child.attrib
                                if attribChildDict.get('start'):  # if this is not None
                                    attrXMLStart = attribChildDict.get('start')
                            #append this to the csv
                            #rowCount = sum(1 for row in csvreader) + 1  #+1 because if csvreader already stands on first line since next() is called
                            csvres[0].append(str(sig))
                            el = 1
                            while el < len(csvres):
                                csvres[el].append(str(attrXMLStart))
                                el += 1

                #the updated csvres needs to be written to the csv file
                with open(csvresfileExtended, 'w') as inpcsvext:
                    for el in range(len(csvres)):
                        if el == 0:
                            csvres[el] = ['"' + ele + '"' for ele in csvres[el]]
                            inpcsvext.write(','.join(csvres[el]) + '\n')
                        else:
                            inpcsvext.write(','.join(csvres[el])+'\n')

            #rename the extended resfile in the csvresfile again
            os.remove(csvresfile)
            shutil.move(csvresfileExtended, csvresfile)

            #now create a file containing only the signals of interest
            newcsvresfile = os.path.splitext(modelfilepathname)[0] + ".csv"

            with open(csvresfile, 'r') as inp, open(newcsvresfile, 'w', newline='') as out:
                reader = csv.reader(inp)
                writer = csv.writer(out)
                #get the column numbers to keep
                firstline = next(reader)
                columnsToKeep = [0] #keep column 0 definitely (time)
                for sig in signalsToKeepList:
                    for sigfl in range(len(firstline)):
                        if firstline[sigfl] == sig:
                            columnsToKeep.append(sigfl)
                #return to the beginning of the file to read first line again (for writing the header now)
                inp.seek(0)
                #now write the resultfile
                for row in reader:
                    valuesLineSignalsToKeep = []
                    for ctk in columnsToKeep:
                        for ci in range(len(row)):
                            if ctk == ci:
                                valuesLineSignalsToKeep.append(row[ci])
                    #for FMI change signal names back again at occurrence, probably in the first line (signal names were changed for simulation using FMI)
                    if mAPD.get("interface") == "FMI":
                        for vLSK in range(len(valuesLineSignalsToKeep)):
                            if "." in valuesLineSignalsToKeep[vLSK]:  # only continue if the element valuesLineSignalsToKeep[vLSK] contains a dot at all
                                for sTKLO in signalsToKeepListOrig:
                                    try:
                                        signOrig = sTKLO.split(".")[0] + "_" + sTKLO.split(".")[1] + "_Out"
                                        signChan = valuesLineSignalsToKeep[vLSK].split(".")[1]
                                        if signOrig == signChan:
                                            valuesLineSignalsToKeep[vLSK] = sTKLO
                                    except:
                                        pass
                    writer.writerow(valuesLineSignalsToKeep)
            print("The output of the simulation of the model " + modelName + " was reduced only keeping signals of interest.")
        except:
            newcsvresfile = ""
        #return the results file
        return newcsvresfile

    #get the results
    def getResults(self, resultsfile):
        try:
            with open(resultsfile, 'r') as rf:
                reader = csv.reader(rf)
                signalValuesList = list(reader)
            return signalValuesList
        except:
            return []