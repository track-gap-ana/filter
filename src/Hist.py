#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun
from icecube.icetray import I3Tray
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
import pandas as pd
import re
import logging
import os
import yaml
import Plot

class Hist(object):
    def __init__(self):
        pass

    def xsec_weight():
        """ Calculates CORSIKA weights in tray and applies them to appended histogram
        
        Returns: hdf5 weight keys

        Useage: to be used in create_hist_struct passed to the bkg strcture
        """
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
            d_histAttri['legend'] = "CORSIKA",
            d_histAttri['color'] =  "#d55e00",
            # d_histAttri['weight'] = weight
            
        else:
            
            # add in when weight things for signal sample have been figured 
            # if args.weight is not None:
            #     d_histAttri['legend'] =  f"{float(match.group("mass"))}GeV {float(match.group("epsilon"))} eps {int(match.group("gap"))}m"
            #     # d_histAttri["weight"] = float(match.group("value")),
            # else:
            
            if fileName is not None: 
                logging.info("on sample: ",fileName)
                legend = self.parseLegend(fileName)
                d_histAttri["legend"] = self.parseLegend(fileName)
            else: 
                logging.warning('No files found')
            
            d_histAttri["color"] = color
        
        # create and transform it to df
        return d_histAttri
            
    def makeHist(self,args):
        # make 1 bkg hist
        if args.withbkg is True: 
            bkgAttri = self.create_hist_struct(args)
            tray = I3Tray()
            tray.Add(Stack, d_histAttri=bkgAttri , out_dir = args.outdir, GCDFile = args.gcd_path)
        
        colors = [ "#003f5c", "#bc5090", "#ffa600", "#ff6361", "#000000", "#444444", "#888888", "#cccccc", "#e6e6e6", "#f5f5f5", "#ffffff", "#56b4e9", "#009e73", "#f0e442"]
        
        # make all other hists
        if args.sigs_path is not None:
            for (sig, color) in zip(os.listdir(args.sigs_path), colors):
                sig_path = args.sigs_path+sig
                if os.path.isdir(sig_path) == True:
                    sigAttri= self.create_hist_struct(args=args,fileName=sig, color=color)
                    tray = I3Tray()
                    tray.Add("I3Reader", filenamelist= list(glob.glob(sig_path+"/LLPSim*/*.gz")))
                    tray.Add(Stack, d_histAttri=sigAttri , out_dir = args.outdir, GCDFile = args.gcd_path)
                    tray.Execute()
                else: 
                    pass
        else:
            sigAttri= self.create_hist_struct(args=args,fileName=args.test_sig, color="#003f5c")
            tray = I3Tray()
            fileList = list(glob.glob(args.test_sig+"/LLPSim*/*.gz"))
            tray.Add("I3Reader", filenamelist= list(glob.glob(args.test_sig+"/LLPSim*/*.gz"))[:2])
            tray.Add(Stack, d_histAttri=sigAttri , out_dir = args.outdir, GCDFile = args.gcd_path)
            tray.Execute()
        
        # if plot flag is used, plot
        if args.plot: self.plot()

    def plot(self):
        plot = Plot.Stack(histpath=args.outdir, config_var=args.config_var)
        plot.processHist()


        
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
        self.gcdFile = self.AddParameter("GCDFile", "GCDFile", "")
    
    def Configure(self): 
        self.out_dir = self.GetParameter("out_dir")
        self.weights = []

        #Create dictionaries for stack histogram
        with open(args.config_var, 'r') as f:
            d_histVars = yaml.full_load(f)
        print("var config \n", d_histVars)    

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
        for track in MuonGun.Track.harvest(frame['I3MCTree'], frame['MMCTrackList']):
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
        print('histogram: \n', self.df_hist)
        logging.info(f"Creating {self.df_hist.loc['legend'][0]}-------------------")
        # Create an HDF5 file
        outFile = self.df_hist.loc['legend'][0].replace(" ", "_")
        logging.info('output file path:', f"{args.outdir}/{outFile}.hdf5")
        self.df_hist.to_csv(f"{args.outdir}/{outFile}.csv")
            



if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--sigs_path", "-sp", default=None, required=False)
  parser.add_argument("--test_sig", "-ts", default="/data/user/axelpo/LLP-data/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628", required=False)
  parser.add_argument("--gcd_path", '-g', default="/data/user/axelpo/LLP-at-IceCube/dark-leptonic-scalar-simulation/resources/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz", required=False)
  parser.add_argument("--weight", "-w", type=float, required=False)
  parser.add_argument('--outdir', "-o", default="outdir")
  parser.add_argument('--withbkg', "-b", action="store_true")
  parser.add_argument('--plot', '-p', action="store_true")
  parser.add_argument('--config-var', '-cv', default = "configs/variables.yaml" ,help="config yaml variable file")
  args = parser.parse_args()
  stack = Hist()
  stack.makeHist(args)




# sigs_path="/mnt/scratch/parrishv/samples_052724/sig/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628/"
# bkg_path="/data/sim/IceCube/2020/generated/CORSIKA-in-ice/20904/"

