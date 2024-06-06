#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun, hdfwriter, simclasses
from icecube.icetray import I3Tray
import glob
import pandas as pd
import re
import logging
import os
import yaml
import VarCalculatorHelper

# set global logger
logger = logging.getLogger(__name__)

class VarCalculator(object):

    def loopTray(self,args):
            logging.info("Making treeograms")
        
            # make 1 bkg tree
            if args.withbkg is True: 
                logging.info("Background treeograming")
                filenamelist= list(glob.glob(args.bkg_path+"/*zst"))
                # logging.debug(filenamelist)
                outfile = args.outdir+"/CORSIKA.hdf5"
                self.runTray(args, out_file = outfile, filenamelist = filenamelist, weight=True)
            else:
                # make all other trees
                if args.sigs_path is not None:
                    self.config_var = args.config_var
                    for sig in os.listdir(args.sigs_path):
                        sig_path = args.sigs_path+sig
                        if os.path.isdir(sig_path) == True:
                            logging.info(f"On sample: {sig}")
                            filenamelist= list(glob.glob(sig_path+"/LLPSim*/*.gz"))
                            outfile = args.outdir+"/"+sig+".hdf5"
                            self.runTray(args, out_file = outfile, filenamelist = filenamelist)
                        
                        else: 
                            pass
                        
    def runTray(self, args, out_file, filenamelist, weight=False):
        # fast option
        if args.fast is not None: filenamelist = [filenamelist[0]]

        # Create dictionaries for stack treeogram
        with open(args.config_var, 'r') as f:
            config = yaml.full_load(f)
        vars = list(config["vars"].keys())
        tray = I3Tray()
        
        # options required for simweights 
        if weight is True: 
            writer = hdfwriter.I3SimHDFWriter
            write_vars = vars + ["CorsikaWeightMap", "I3EventHeader", "PolyplopiaPrimary"]
        else: 
            writer = hdfwriter.I3SimHDFWriter
            write_vars = vars
        logger.debug(f"\n--------------Variables for calculation and booking: {vars}")

        # Add modules to the tray
        tray.Add("I3Reader", filenamelist= filenamelist)
        tray.Add(Stack, GCDFile = args.gcd_path, vars=vars)
        tray.Add(
            writer,
            keys=write_vars,
            output=out_file,
        )
        tray.Execute()

        
class Geometry(object):
    def __init__(self):
        pass
    #Function to read the GCD file and make the extruded polygon which
    #defines the edge of the in-ice array
    def MakeSurface(gcdName, padding):
        file = dataio.I3File(gcdName, "r")
        frame = file.pop_frame()
        while not "I3Geometry" in frame:
            frame = file.pop_frame()
        geometry = frame["I3Geometry"]
        xyList = []
        zmax = -1e100
        zmin = 1e100
        step = int(len(geometry.omgeo.keys())/10)
        logging.info("Loading the DOM locations from the GCD file")
        for i, key in enumerate(geometry.omgeo.keys()):
            if i % step == 0:
                logging.info( "{0}/{1} = {2}%".format(i,len(geometry.omgeo.keys()), int(round(i/len(geometry.omgeo.keys())*100))))
                
            if key.om in [61, 62, 63, 64] and key.string <= 81: #Remove IT...
                continue

            pos = geometry.omgeo[key].position

            if pos.z > 1500:
                continue
                
            xyList.append(pos)
            i+=1
        
        return MuonGun.ExtrudedPolygon(xyList, padding) 


class Stack(icetray.I3Module):

    def __init__(self,ctx):
        icetray.I3Module.__init__(self,ctx)
        self.AddParameter("vars", "vars", None)
        self.gcdFile = self.AddParameter("GCDFile", "GCDFile", "")
    
    def Configure(self): 
        self.vars = self.GetParameter("vars")
        self.weights = []

        # create surface for detector volume
        self.gcdFile = self.GetParameter("GCDFile")
        if self.gcdFile != "":
            self.surface = Geometry.MakeSurface(self.gcdFile, 0)
        else:
            self.surface = MuonGun.Cylinder(1000,500) # approximate detector volume

    def DAQ(self, frame):
        # which weight?
        if "muongun_weights" in frame:
            weight = frame["muongun_weights"].value
        else:
            weight = 1
        # fill treeogram
        self.weights.append( weight )

        # Loading var calculator!
        var_calculator = VarCalculatorHelper.VarCalculatorHelper(self.surface, frame) 
        for var_name in self.vars:
            var_value = var_calculator.RunCalculator(var_name)     
            # logger.debug(f"Var: {var_name} = {var_value}")       
            frame.Put(var_name, dataclasses.I3Double(var_value))
            self.PushFrame(frame)
        
    def Finish(self):

        logging.info(f"Finishing the creation of var tree hdf5 files -------------------")


