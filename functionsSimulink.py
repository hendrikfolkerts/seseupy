# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import subprocess
import csv

class functionsSimulink():

    #run the system
    def runSimulation(self, modelfilepathname, mAPD):
        #add necessary parameters to the modelfile
        modelName = os.path.splitext(os.path.basename(modelfilepathname))[0]
        with open(modelfilepathname, "a") as fileobject:
            #append simulation information
            fileobject.write("simout = sim('" + modelName + "',...\n")
            fileobject.write("'StartTime', '" + str(mAPD.get("starttime")) + "',...\n")
            fileobject.write("'Solver', '" + mAPD.get("solver") + "',...\n")
            fileobject.write("'StopTime', '" + str(mAPD.get("stoptime")) + "',...\n")
            fileobject.write("'MaxStep', '" + str(mAPD.get("maxstep")) + "',...\n")

            #not needed, since SaveOutput seems to be ignored, instead just take Out ports
            #fileobject.write("'SimulationMode', 'normal',...\n")
            #fileobject.write("'SaveTime', 'on', 'TimeSaveName', 'tout',...\n")
            #fileobject.write("'SaveState', 'on', 'StateSaveName', 'xout',...\n")
            #fileobject.write("'SaveOutput', 'on', 'OutputSaveName', 'yout',...\n")

            fileobject.write("'SaveFormat', 'StructureWithTime');\n")

            #write results in a file------------------------------------------------------------------------------------
            #fileobject.write("save('" + modelName + ".mat', 'simout')\n")  #it shall be saved as csv instead, therefore the following lines

            fileobject.write("t = simout.tout;\n")              #get the simulation time
            fileobject.write("y = simout.yout.signals;\n")      #get the simulation signals with their values
            fileobject.write("numValues = length(t);\n")
            fileobject.write("numSignals = length(y);\n")

            fileobject.write("header(1,1:numSignals+1) = {0};\n")              #preallocate memory for the header
            fileobject.write("simdata = zeros(numValues,numSignals+1);\n")     #simdata: preallocate memory for the signals and their values

            fileobject.write("header(1) = {'time'};\n")
            fileobject.write("simdata(:,1) = t;\n")

            fileobject.write("for i = 1:numSignals\n")  #fill the header and the simdata object
            fileobject.write("    header{1,i+1} = simout.yout.signals(i).blockName;\n")
            fileobject.write("    simdata(:,i+1) = simout.yout.signals(i).values;\n")
            fileobject.write("end\n")

            fileobject.write("csvHeader = strjoin(header, ',');\n") #join the values in the header separated by comma
            fileobject.write("fid = fopen('" + modelName + ".csv','w');\n") #write the header to file
            fileobject.write("fprintf(fid, csvHeader);\n")
            fileobject.write("fprintf(fid, '\\n');\n")
            fileobject.write("fclose(fid);\n")

            fileobject.write("dlmwrite('" + modelName + ".csv',simdata,'-append');\n")

            #end write results in a file--------------------------------------------------------------------------------

            fileobject.write("bdclose\n")   #close the simulation model
            fileobject.write("quit\n")      #close Matlab

        #now run the script - start and wait until done
        retcode = subprocess.call(["matlab", "-nosplash", "-nodesktop", "-wait", "-r", "\"run('" + modelfilepathname + "');\""])
        print("The simulation of the model " + modelName + " was executed by Simulink returning " + str(retcode) + ".")
        print("The simulation of the model " + modelName + " was saved as csv.")

        #return the results file
        resfilepathname = os.path.splitext(modelfilepathname)[0] + ".csv"
        return resfilepathname

    #get the results
    def getResults(self, resultsfile):
        with open(resultsfile, 'r') as rf:
            reader = csv.reader(rf)
            signalValuesList = list(reader)
        return signalValuesList