# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import subprocess
import csv
import platform

class functionsSimulink():

    #run the system
    def runSimulation(self, modelfilepathname, mAPD):
        #set the system
        syst = platform.system()

        #add necessary parameters to the modelfile
        modelName = os.path.splitext(os.path.basename(modelfilepathname))[0]
        with open(modelfilepathname, "a") as fileobject:
            fileobject.write("\n")
            fileobject.write("try\n")
            fileobject.write("\n")

            #add outports to the signals of interest -> Simulink only returns values that have outports
            #copy the .slx file with the outport to this script
            pathOfThisFile = os.path.dirname(os.path.abspath(__file__))
            pathOfSimulinkOutBlock = os.path.join(pathOfThisFile, 'general_Simulator_files', 'Simulink_OutBlock.slx')
            newPathOfSimulinkOutBlock = os.path.join(os.path.split(modelfilepathname)[0], 'Simulink_OutBlock.slx')
            shutil.copyfile(pathOfSimulinkOutBlock, newPathOfSimulinkOutBlock)
            #add the Out blocks to the signals of interest

            #path = os.path.split(modelfilepathname)[0]
            #fileobject.write("addpath('" + path + "');\n")

            #interprete nsigana -> number of Out blocks and where to connect to
            nsigana = eval(mAPD.get('nsigana'))
            for i in range(len(nsigana)):
                #add the outblock
                sourceblockname = nsigana[i].split(".")[0].replace("-", "_")
                sourceblock = modelName + "/" + sourceblockname
                sourceblockport = nsigana[i].split(".")[-1]  #the name of the sourceport -> find the portnumber
                sinkblockname = sourceblockname + "_" + nsigana[i].split(".")[-1]   #the sink is the Out block
                sinkblock = modelName + "/" + sinkblockname
                sinkblockportnumber = "1"   #the number of the Out block's port -> is has only one, so portnumber "1"
                fileobject.write("%One out block with connection\n")
                #add the block
                fileobject.write("h = add_block('Simulink_OutBlock/Out', '" + sinkblock + "');    %add Simulink Out block from an MB containing only the Simulink Out block\n")
                fileobject.write("set_param(h, 'Port', '" + str(i+1) + "');    %set the number of the Out block\n")
                #add the connection
                if mAPD.get("interface") == "native":
                    fileobject.write("phFrom = get_param('" + sourceblock + "','PortHandles');    %get the port handles of the source block\n")
                else:
                    fileobject.write("phFrom = get_param('" + modelName + "/" + modelName + "','PortHandles');    %get the port handles of the source block\n")
                fileobject.write("phTo = get_param('" + sinkblock + "','PortHandles');    %get the port handles of the sink block\n")
                #port for connection: sourceblock -> out port
                if mAPD.get("interface") == "native":
                    fileobject.write("simBlockHandle = get_param('" + sourceblock + "','Handle');    %get the handle of the source block (which is a subsystem of the functional block(s) and In/Out blocks)\n")
                else:
                    fileobject.write("simBlockHandle = get_param('" + modelName + "/" + modelName + "','Handle');    %get the handle of the source block (which is a subsystem of the model FMU and Out blocks)\n")
                fileobject.write("outportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');    %get the handles to Out blocks in the subsystem\n")
                fileobject.write("outNames = get_param(outportHandles, 'Name');    %get the names of the Out blocks\n")
                fileobject.write("outPorts = get_param(outportHandles, 'Port');    %get the ports of the Out blocks\n")
                fileobject.write("if iscell(outNames)\n")
                if mAPD.get("interface") == "native":
                    fileobject.write("    idx = find(ismember(outNames, '" + sourceblockport + "'));    %If there are several outNames, the values are placed in a cell array outPorts. -> Find the right number to the name.\n")
                else:
                    fileobject.write("    idx = find(ismember(outNames, '" + sourceblockname + "_" + sourceblockport + "_Out'));    %If there are several outNames, the values are placed in a cell array outPorts. -> Find the right number to the name.\n")
                fileobject.write("    pno = str2num(outPorts{idx});\n")
                fileobject.write("else\n")
                fileobject.write("    pno = str2num(outPorts);    %If there is only one outName, the outPorts is a string with value '1'. It can be used directly.\n")
                fileobject.write("end\n")
                #port for connection: sinkblock -> in port -> the Out block -> it is clear which port, so no more code
                fileobject.write("pni = " + sinkblockportnumber + ";    %port of the sinkblock for the connection -> The in port of the Out block -> The port is clear.\n")
                #draw the line
                fileobject.write("add_line('" + modelName + "', phFrom.Outport(pno), phTo.Inport(pni), 'autorouting', 'on');   %draw a connection between the now found outport and inport\n")
                fileobject.write("\n")

            #fileobject.write("rmpath('" + path + "');\n")

            #append simulation information
            fileobject.write("%Simulator run\n")
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
            fileobject.write("\n")

            #write results in a file------------------------------------------------------------------------------------
            fileobject.write("%Get the simulation results and write them into a CSV file\n")
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
            fileobject.write("    blockName = simout.yout.signals(i).blockName;\n")
            fileobject.write("    blockName = split(blockName, '/');\n")
            fileobject.write("    blockName = blockName{end};\n")
            fileobject.write("    blockName = strrep(blockName, '_', '.');\n")
            fileobject.write("    header{1,i+1} = blockName;\n")
            fileobject.write("    simdata(:,i+1) = simout.yout.signals(i).values;\n")
            fileobject.write("end\n")

            fileobject.write("csvHeader = strjoin(header, ',');\n") #join the values in the header separated by comma
            fileobject.write("fid = fopen('" + modelName + ".csv','w');\n") #write the header to file
            fileobject.write("fprintf(fid, csvHeader);\n")
            fileobject.write("fprintf(fid, '\\n');\n")
            fileobject.write("fclose(fid);\n")

            fileobject.write("dlmwrite('" + modelName + ".csv',simdata,'-append');\n")

            #catch if error---------------------------------------------------------------------------------------------
            fileobject.write("\n")
            fileobject.write("catch\n")
            fileobject.write("end\n")
            fileobject.write("\n")

            #end write results in a file--------------------------------------------------------------------------------

            fileobject.write("bdclose\n")   #close the simulation model
            fileobject.write("quit\n")      #close Matlab

        #now run the script - start and wait until done
        if syst == "Windows":
            retcode = subprocess.call(["matlab", "-nosplash", "-nodesktop", "-wait", "-r", "\"run('" + modelfilepathname + "');\""])
        else:
            retcode = subprocess.call(["matlab", "-nosplash", "-nodesktop", "-wait", "-r", "run('" + modelfilepathname + "');"])
        print("The simulation of the model " + modelName + " was executed by Simulink returning " + str(retcode) + ".")
        print("The simulation of the model " + modelName + " was saved as csv.")

        #return the results file
        resfilepathname = os.path.splitext(modelfilepathname)[0] + ".csv"
        return resfilepathname

    #get the results
    def getResults(self, resultsfile):
        try:
            with open(resultsfile, 'r') as rf:
                reader = csv.reader(rf)
                signalValuesList = list(reader)
            return signalValuesList
        except:
            return []