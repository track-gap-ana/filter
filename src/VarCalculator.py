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
import VarCalculatorHelperSim
import VarCalculatorHelperData
import ConfigHelper

# Set global logger
logger = logging.getLogger(__name__)

class VarCalculator(object):
    def __init__(self, args):
        self.config = ConfigHelper.ConfigHelper(config_var=args.config_var, config_samples=args.config_samples)
        self.sig_top = self.config.loadSig()
        self.data_top = self.config.loadData()
        self.sig_type = self.config.loadSigType()
        self.gcd = self.config.loadGCD()
        self.version = self.config.loadVersion()
        self.vars = self.config.loadVars()
        self.filter = self.config.loadFilter()
        self.model = self.config.loadModel()
        self.outdir = self.config.makeDirs(args.outdir)
        self.i3 = args.i3
        self.dag = args.dag

    def localTrayLoop(self, args):
        """
        Executes the local tray loop for variable calculation.
        This method processes local input files to calculate variables based on the provided arguments.
        It can handle both background and signal data, and outputs the results to an HDF5 file.
        Args:
            args (Namespace): A namespace object containing the following attributes:
                withbkg (bool): Flag indicating whether to process background data.
                bkg_path (str, optional): Path to the background data files.
                sigs_path (str, optional): Path to the signal data files.
                config_var (str, optional): Path to the configuration file.
        Returns:
            None
        """

        logging.info("\n--------------Making variables")
        if args.data is True:
            logging.info("\n--------------Data booking is turned on and running")
            filenamelist = list(glob.glob(self.data_top + "/*i3*"))
            logger.debug(f"Data files: {filenamelist}")
            outfile = os.path.join(self.outdir, "data.hdf5")
            self.runTray(args, out_file=outfile, filenamelist=filenamelist)
        elif args.withbkg:
            logging.info("\n--------------Background sim booking is turned on and running")
            filenamelist = list(glob.glob(args.bkg_path + "/*zst"))
            outfile = self.outdir + "/CORSIKA.hdf5"
            self.runTray(args, out_file=outfile, filenamelist=filenamelist, weight=True)
        elif args.sigs_path is True:
            logging.info("\n--------------Signal sim booking is turned on and running")
            self.config_var = args.config_var
            logger.info(f"Config file: {self.config_var}")
            self.sig_fileStructure(args)
            
    def sig_fileStructure(self, args):
        filenamelist = [filename for filename in glob.glob(args.sigs_path + "/*i3*") if "DarkLeptonicScalar" in filename] if self.dag else [filename for filename in glob.glob(args.sigs_path + "/*/*/*.i3*") if "DarkLeptonicScalar" in filename]
        if "DarkLeptonicScalar" in args.sigs_path:
            logging.info(f"\n--------------Only one sample type given: \n{args.sigs_path}")
            outfile = self.outdir + "/" + os.path.basename(args.sigs_path) + ".hdf5"
            logger.debug(f"Running on all base and unprocessed LLP files")
            self.iterateFilters(lambda: self.runTray(args, out_file=outfile, filenamelist=filenamelist))
        elif args.fast:
            filenamelist = filenamelist[:1]
            logger.warning(f"Fast option on, only running on one file: {filenamelist}")
            outfile = self.outdir + "/" "thefirstone_test.hdf5"
            self.iterateFilters(lambda: self.runTray(args, out_file=outfile, filenamelist=filenamelist))
        else:
            for sig in os.listdir(args.sigs_path):
                sig_path = args.sigs_path + sig
                if os.path.isdir(sig_path) and os.listdir(sig_path) and "out" not in sig:
                    logging.info(f"\n--------------On sample: \n{sig}")
                    outfile = self.outdir + "/" + sig + ".hdf5"
                    logger.debug(f"Running on all files")
                    self.iterateFilters(lambda: self.runTray(args, out_file=outfile, filenamelist=filenamelist))

    def iterateFilters(self, func):
        if "None" in self.filter:
            func()
        else:
            logger.info(f"Found filters: {self.filter}")
            for filter in self.filter:
                logger.debug(f"Filtering on: {filter}")
                self.filter = filter
                func()

    def runTray(self, args, out_file, filenamelist, weight=False):
        with open(args.config_var, 'r') as f:
            config = yaml.full_load(f)
        vars = list(config["vars"].keys())
        if args.fast:
            fastFrames = 70
        logger.info(f"\n--------------Variables for calculation and booking: \n{vars}")
        tray = I3Tray()

        if weight: # used for corika samples
            writer = hdfwriter.I3SimHDFWriter
            write_vars = vars + ["CorsikaWeightMap", "I3EventHeader", "PolyplopiaPrimary"]
        else: # used for signal samples
            writer = hdfwriter.I3HDFWriter
            write_vars = vars
            subeventstream = ["InIceSplit"] # default subeventstream
            if self.filter is not None: subeventstream = [self.filter] # if filter is specified, use it
            logger.debug(f"Subeventstream: {subeventstream}")
            
        frame_count = [0]
        tray.Add("I3Reader", filenamelist=filenamelist)

        # Make selections (or not)
        if self.filter is not None or self.model is not None:
            if self.filter is not None: 
                logger.warning(f"Selecting on Existing Filter:-------------\n {self.filter}")
                tray.Add(lambda frame: bool(frame["OfflineFilterMask"][self.filter]) if "OfflineFilterMask" in frame else False)
                write_vars = vars + [self.filter]
                # This is an unchecked addition! 
            if self.model is not None: 
                logger.warning(f"Selecting on Model:-------------\n {self.model}")
                tray.Add(lambda frame: bool(frame[self.model]) if self.model in frame else False)
                write_vars = vars + [self.model]
        else:
            logger.warning(f"-------------\n No selections applied")
            out_file = out_file.replace(".hdf5", "_noSelection.hdf5")

        tray.AddModule(lambda frame: frame_count.append(frame_count.pop() + 1), 'counter')
        tray.Add(Stack, GCDFile=args.gcd_path, vars=vars, data=args.data)

        if self.i3: # convert hdf5 to i3 files
            tray.AddModule("I3Writer", Filename=out_file.replace(".hdf5", ".i3"))
        else: # write out hdf5 files
            tray.Add(writer, keys=write_vars, output=out_file, SubEventStreams=subeventstream)

        tray.Execute(fastFrames)
        logger.debug(f"Total number of frames passing filter (if used): {frame_count[0]}")
        logger.info(f"Output file: {out_file}")

class Geometry(object):
    @staticmethod
    def MakeSurface(gcdName, padding):
        file = dataio.I3File(gcdName, "r")
        frame = file.pop_frame()
        while "I3Geometry" not in frame:
            frame = file.pop_frame()
        geometry = frame["I3Geometry"]
        xyList = []
        step = int(len(geometry.omgeo.keys()) / 10)
        logging.info("Loading the DOM locations from the GCD file")
        for i, key in enumerate(geometry.omgeo.keys()):
            if i % step == 0:
                logging.info("{0}/{1} = {2}%".format(i, len(geometry.omgeo.keys()), int(round(i / len(geometry.omgeo.keys()) * 100))))
            if key.om in [61, 62, 63, 64] and key.string <= 81:
                continue
            pos = geometry.omgeo[key].position
            if pos.z > 1500:
                continue
            xyList.append(pos)
        return MuonGun.ExtrudedPolygon(xyList, padding)

class Stack(icetray.I3Module):
    def __init__(self, ctx):
        icetray.I3Module.__init__(self, ctx)
        self.AddParameter("vars", "vars", None)
        self.AddParameter("GCDFile", "GCDFile", "")
        self.AddParameter("data", "data", False) # default is simulation

    def Configure(self):
        self.vars = self.GetParameter("vars")
        self.data = self.GetParameter("data")
        self.weights = []
        self.gcdFile = self.GetParameter("GCDFile")
        self.surface = Geometry.MakeSurface(self.gcdFile, 0) if self.gcdFile else MuonGun.Cylinder(1000, 500)

    def Physics(self, frame):
        weight = frame["muongun_weights"].value if "muongun_weights" in frame else 1
        self.weights.append(weight)
        if self.data is True:
            logging.info(f"Running on data")
            var_calculator = VarCalculatorHelperData.VarCalculatorHelperData(frame)
        else : 
            logging.info(f"Running on simulation")
            var_calculator = VarCalculatorHelperSim.VarCalculatorHelperSim(self.surface, frame)

        for var_name in self.vars:
            var_value = var_calculator.RunCalculator(var_name)
            logging.debug(f"Variable: {var_name} Value: {var_value}")
            frame.Put(var_name, dataclasses.I3Double(var_value))
            
        self.PushFrame(frame)

    def Finish(self):
        logging.info(f"Finishing the creation of var files -------------------")