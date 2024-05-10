#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun
from icecube.icetray import I3Tray
import glob
import pandas as pd
import re
import logging
import os
import yaml

# set global logger
logger = logging.getLogger(__name__)

class Hist(object):
    def __init__(self):
        pass

    def parseLegend(self,fileName):
        mass_match = re.search(r".mass-(\d+)", fileName)
        mass_match = f"{float(mass_match.group(1))} GeV"
        
        eps = re.search(r"eps(-?\d+e-?\d+)", fileName)
        eps = f" {float(eps.group(1))} eps"

        nevents = re.search(r"\.nevents-(\d+)", fileName)
        nevents = f" {float(nevents.group(1))} events"

        ene = re.search(r'\d+e\d+_\d+e\d+', fileName)
        ene = f" {ene.group(0)} ene"

        gap = re.search(r"\_gap_(\d+)", fileName)
        if gap is not None: 
            gap = f" {float(gap.group(1))} m"
        else: 
            gap = " 50 m"

        legend = mass_match+eps+nevents+ene+gap
        return legend
    
    def readConfigs(self):
        with open(self.config_var, 'r') as f:
            d_histVars = yaml.full_load(f)
        return d_histVars

    def create_hist_struct(self, args, fileName=None, color=None):
        """Creates two data structures containing mass, epsilon, color, gap length, and either weight or ene.

        Args:
            args: An argparse.Namespace object containing dir of samples.

        Returns:
            Three (two sig + 1 bkg) structures containing mass, epsilon, color, gap length and either weight or ene.
        """
        d_histAttri =  {
                        'legend': None,
                        'color' : None,
                        'weight' : None,
                        }
                      
        if args.withbkg is True:
            d_histAttri['legend'] = "CORSIKA"
            d_histAttri['color'] =  "#d55e00"
            # d_histAttri['weight'] = weight
            
        else:
            
            # add in when weight things for signal sample have been figured 
            # if args.weight'] is not None:
            #     d_histAttri['legend'] =  f"{float(match.group("mass"))}GeV {float(match.group("epsilon"))} eps {int(match.group("gap"))}m"
            #     # d_histAttri["weight"] = float(match.group("value")),
            # else:
            
            if fileName is not None: 
                legend = self.parseLegend(fileName)
                d_histAttri["legend"] = self.parseLegend(fileName)
            else: 
                logging.warning('No files found')
            
            d_histAttri["color"] = color
        
        # create and transform it to df
        return d_histAttri

    def addTray(self, args, filenamelist, histAttri):
        tray = I3Tray()
        # if args.nfiles is not None: 
        #     nfiles = int(args.nfiles)  # Convert args.nfiles to an integer
        #     filenamelist = filenamelist[:nfiles]
        
        if args.nevents is not None: frames = int(args.nevents)
        else: frames = float("inf")
        
        tray.Add("I3Reader", filenamelist= filenamelist)
        tray.Add(Stack, d_histAttri=histAttri , out_dir = args.outdir, GCDFile = args.gcd_path, config_var=args.config_var)
        tray.Execute(frames)

    def makeHist(self,args):
        logging.info("Making histograms")
        # make 1 bkg hist
        if args.withbkg is True: 
            logging.info("Background histograming")
            filenamelist= list(glob.glob(args.bkg_path+"/*zst"))
            bkgAttri = self.create_hist_struct(args)
            # logging.debug(filenamelist)
            self.addTray(args, filenamelist = filenamelist, histAttri= bkgAttri)
        else:
            # make all other hists
            if args.sigs_path is not None:
                colors = self.readConfigs()["attr"]["colorblind"]
                for (sig, color) in zip(os.listdir(args.sigs_path), colors):
                    sig_path = args.sigs_path+sig
                    if os.path.isdir(sig_path) == True:
                        logging.info(f"On sample: {sig}")
                        filenamelist= list(glob.glob(sig_path+"/LLPSim*/*.gz"))
                        sigAttri= self.create_hist_struct(args=args,fileName=sig, color=color)
                        self.addTray(args, filenamelist = filenamelist, histAttri = sigAttri)
                    
                    else: 
                        pass

        
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
        self.AddParameter("out_dir", "out_dir", None)
        self.AddParameter("d_histAttri", "d_histAttri", None)
        self.AddParameter("config_var", "config_var", None)
        self.gcdFile = self.AddParameter("GCDFile", "GCDFile", "")
    
    def Configure(self): 
        self.out_dir = self.GetParameter("out_dir")
        self.config_var = self.GetParameter("config_var")
        self.weights = []

        #Create dictionaries for stack histogram
        with open(self.config_var, 'r') as f:
            d_histVars = yaml.full_load(f)
            d_histVars = d_histVars["vars"]
        # make a df hist out of it
        self.df_hist = pd.DataFrame(d_histVars, index =['bins', 'min', 'max'] )

        # configure hist attributes by unzipping dictionary to lists
        self.d_histAttri = self.GetParameter("d_histAttri")
        (inx, item) = zip(*self.d_histAttri.items())
        df_histAttri = pd.DataFrame({varName : item for varName in d_histVars.keys()}, index = inx)

        # append hist attributes to hist vars
        self.df_hist = self.df_hist._append(df_histAttri, ignore_index = False)
 
        # create new dictionary for histogram event entries called in AppendHist()
        self.d_histData = {varName: [] for varName in d_histVars.keys()}

        # create surface for detector volume
        self.gcdFile = self.GetParameter("GCDFile")
        if self.gcdFile != "":
            self.surface = Geometry.MakeSurface(self.gcdFile, 0)
        else:
            self.surface = MuonGun.Cylinder(1000,500) # approximate detector volume

    def AppendHist(self, varName, frameitem):
        # append events entries to variable column
        self.d_histData[varName].append(frameitem)

    def DAQ(self, frame):
        # which weight?
        if "muongun_weights" in frame:
            weight = frame["muongun_weights"].value
        else:
            weight = 1
        # fill histogram
        self.weights.append( weight )
        # self.AppendHist(frame, frame["LLPInfo"]["length"], self.d_histVars["gaplength"]["histogramdictionary"])
        # self.AppendHist(frame, frame["LLPInfo"]["prod_z"], self.d_histVars["prodz"]["histogramdictionary"])
        # self.AppendHist(frame, frame["LLPInfo"]["prod_z"]-frame["LLPInfo"]["length"]*np.cos(frame["LLPInfo"]["zenith"]), self.d_histVars["decayz"]["histogramdictionary"])
        # self.AppendHist(frame, frame["I3MCTree_preMuonProp"].get_head().dir.zenith, self.d_histVars["zenith"]["histogramdictionary"])
        self.AppendHist(varName = 'Edeposited', frameitem= self.ComputeDepositedEnergy(frame))
        self.AppendHist(varName = "totalInitialE", frameitem = self.ComputeTotalEnergyAtBoundary(frame))
        self.AppendHist(varName = "totalMCPulseCharge", frameitem = self.ComputeTotalMCPulseCharge(frame))
        self.AppendHist(varName = "totalDOMHits", frameitem = self.ComputeTotalDOMHits(frame))

    
        self.PushFrame(frame)
        
    def ComputeDepositedEnergy(self, frame):
        edep = 0

        # Change name scheme between sig and bkg sim samples 
        if 'I3MCTree' in frame: MCTree = 'I3MCTree'
        else: MCTree = 'SignalI3MCTree'

        for track in MuonGun.Track.harvest(frame[MCTree], frame['MMCTrackList']):
            # Find distance to entrance and exit from sampling volume
            intersections = self.surface.intersection(track.pos, track.dir)
            # Get the corresponding energies
            e0, e1 = track.get_energy(intersections.first), track.get_energy(intersections.second)
            # Accumulate
            edep +=  (e0-e1)
        return edep
    
    def ComputeTotalMCPulseCharge(self, frame):
        totalCharge = 0
        for key, item in frame["I3MCPulseSeriesMap"]:
            totalCharge += sum([pulse.charge for pulse in item])
        return totalCharge
    
    def ComputeTotalDOMHits(self, frame):
        totalHits = 0
        for key, item in frame["I3MCPulseSeriesMap"]:
            totalHits += 1
        return totalHits
    
    def ComputeTotalEnergyAtBoundary(self, frame):
        totalE = 0
        for p in frame["I3MCTree_preMuonProp"].children(frame["I3MCTree_preMuonProp"].get_head()):
            totalE += p.energy
        return totalE
    
    def Finish(self):
        # convert dictionaries to dataframes
        df_histData = pd.DataFrame(self.d_histData)        
        self.df_hist = self.df_hist._append(df_histData)
        outFile = self.df_hist.loc['legend'][0].replace(" ", "_")
        logging.info(f"Creating {outFile} histogram -------------------")
        logging.debug(self.df_hist)
        # Create an HDF5 file for background weighting
        outFile = self.df_hist.loc['legend'][0].replace(" ", "_")
        self.df_hist.to_csv(f"{self.out_dir}/{outFile}.csv")
        if "CORSIKA" in str(outFile):
            with pd.HDFStore(f"{self.out_dir}/forbkgweighting.hdf5", mode = 'w') as store:
                for column in df_histData.columns:
                    store.put(column, df_histData[column]) 
