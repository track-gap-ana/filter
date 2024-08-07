#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun, hdfwriter, simclasses
from icecube.icetray import I3Tray
import icecube.filter_tools as filter_tools
import glob
import pandas as pd
import re
import logging
import os
import yaml
import VarCalculatorHelper
import ConfigHelper

# set global logger
logger = logging.getLogger(__name__)

class VarCalculator(object):

    def __init__(self, args):
        self.config=ConfigHelper.ConfigHelper(config_var=args.config_var, config_samples=args.config_samples)
        # Load the config_samples file
        self.sig_top = self.config.loadSig()
        self.sig_type = self.config.loadSigType()
        self.gcd = self.config.loadGCD()
        self.version = self.config.loadVersion()

        # from config_variables
        self.vars = self.config.loadVars()
        self.filter = self.config.loadFilter()

        # outdir
        self.outdir = self.config.makeDirs(args.outdir)


    def fileStructure(self, args):
        for sig in os.listdir(args.sigs_path):
            sig_path = args.sigs_path+sig
            if os.path.isdir(sig_path) and os.listdir(sig_path) and "out" not in sig:
                logging.info(f"\n--------------On sample: \n{sig}")
                if args.dag is True:
                    filenamelist= list(glob.glob(sig_path+"/*i3*"))
                else:
                    filenamelist= list(glob.glob(sig_path+"/*/*.i3*"))
                outfile = self.outdir+"/"+sig+".hdf5"
                self.runTray(args, out_file = outfile, filenamelist = filenamelist)
            else: 
                pass
            
    def local_filterFileStructure(self, args):
        for sig in os.listdir(args.sigs_path):
            self.runTray(args, out_file = self.outdir+"/"+"test.hdf5", filenamelist = [args.sigs_path+sig])

    def loopTray(self,args):
            logging.info("\n--------------Making variables")        
            # make 1 bkg tree
            if args.withbkg is True: 
                logging.info("\n--------------Background booking is turned of and running")
                filenamelist= list(glob.glob(args.bkg_path+"/*zst"))
                # logging.debug(filenamelist)
                outfile = self.outdir+"/CORSIKA.hdf5"
                self.runTray(args, out_file = outfile, filenamelist = filenamelist, weight=True)
            else:
                # make all other trees
                if args.sigs_path is not None:
                    self.config_var = args.config_var
                    logger.debug(f"Config file: {self.config_var}")
                    logger.debug(f'Running on: {args.sigs_path}')
                    self.fileStructure(args)

    def runTray(self, args, out_file, filenamelist, weight=False):
        # fast option
        if args.fast is True: 
            filenamelist = filenamelist[:1]
            logger.debug(f"Fast option, only computing one file: {filenamelist}")
        else: 
            logger.debug(f"Running on all files: {filenamelist}")

        # Create dictionaries for stack treeogram
        with open(args.config_var, 'r') as f:
            config = yaml.full_load(f)
        vars = list(config["vars"].keys())
        filter = config["filter"]
        logger.info(f"\n--------------Variables for calculation and booking: \n{vars}")
        tray = I3Tray()
        
        # options required for simweights 
        if weight is True: 
            writer = hdfwriter.I3SimHDFWriter
            write_vars = vars + ["CorsikaWeightMap", "I3EventHeader", "PolyplopiaPrimary"]
        else: 
            writer = hdfwriter.I3SimHDFWriter
            write_vars = vars

        frame_count = [0]
        # Add modules to the tray
        tray.Add("I3Reader", filenamelist= filenamelist)
        # Print out the total number of frames that passed the filter
        if filter is not None: 
            logger.warning(f"Filtering on:-------------\n {filter}")
            tray.Add(
                lambda frame: bool(frame["OfflineFilterMask"][filter])
                if "OfflineFilterMask" in frame
                else False
            )
        else: 
            logger.warning(f"-------------\n No filter applied")
            out_file = out_file.replace(".hdf5", "_noFilter.hdf5")
        tray.AddModule(lambda frame: frame_count.append(frame_count.pop() + 1), 'counter')
        tray.Add(Stack, GCDFile = args.gcd_path, vars=vars)
        tray.Add(
            writer,
            keys=write_vars,
            output=out_file,
        )
        tray.Execute()
        logger.debug(f"Total number of frames: {frame_count[0]}")
       
        
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


