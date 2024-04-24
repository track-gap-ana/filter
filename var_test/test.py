#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses, MuonGun
from I3Tray import I3Tray
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
import pandas as pd
import re
import logging

class Stack(object):
    def __init__(self):
        pass

    def xsec_weight():
        """ Calculates CORSIKA weights in tray and applies them to appended histogram
        
        Returns: hdf5 weight keys

        Useage: to be used in create_hist_struct passed to the bkg strcture
        """
    def parseLegend(fileName):
        mass_match = re.search(r".mass-(\d+)", fileName)
        mass_match = f"{float(mass_match.group(1))} GeV"
        
        eps = re.search(r"eps(-?\d+e-?\d+)", fileName)
        eps = f" {float(eps.group(1))} eps"

        nevents = re.search(r"\.nevents-(\d+)", fileName)
        nevents = f" {float(nevents.group(1))} events"

        ene = re.search(r'\d+e\d+_\d+e\d+', fileName)
        ene = f" {ene.group(0)} ene"

        gap = re.search(r"\_gap_(\d+)", fileName)
        gap = f" {float(gap.group(1))} m"

        legend = mass_match+eps+nevents+ene+gap
        return legend

    def create_hist_struct(self,fileName=None, color=None, args=None):
        """Creates two data structures containing mass, epsilon, color, gap length, and either weight or ene.

        Args:
            args: An argparse.Namespace object containing dir of samples.

        Returns:
            Three (two sig + 1 bkg) structures containing mass, epsilon, color, gap length and either weight or ene.
        """

        histAttri = pd.DataFrame(data= 
                                    {
                                    'legend': None,
                                    'color' : None,
                                    'weight' : None,
                                    }
                                )

        if args.withbkg is not None:
            histAttri['legend'] = "CORSIKA",
            histAttri['color'] =  "#d55e00",
            # histAttri['weight'] = weight
            
        else:
            
            # add in when weight things for signal sample have been figured 
            # if args.weight is not None:
            #     histAttri['legend'] =  f"{float(match.group("mass"))}GeV {float(match.group("epsilon"))} eps {int(match.group("gap"))}m"
            #     # histAttri["weight"] = float(match.group("value")),
            # else:
            
            if fileName is not None: 
                histAttri["legend"] = self.parseLegend(fileName)
            else: 
                logging.warning('No files found')
            
            histAttri["color"] = color
                            
        return histAttri.T()
            
    def makeHist(self,args):
        # make 1 bkg hist
        if args.withbkg is not None: 
            _,bkgAttri = self.create_hist_struct()
            tray = I3Tray()
            tray.Add(HistogramLLPs, histAttri=bkgAttri , out_dir = args.outdir, GCDFile = GCD_path)
        
        colors = [ "#003f5c", "#bc5090", "#ffa600", "#ff6361", "#000000", "#444444", "#888888", "#cccccc", "#e6e6e6", "#f5f5f5", "#ffffff", "#56b4e9", "#009e73", "#f0e442"]
        
        # make all other hists

        for (sig, color) in zip(args.sigs, colors):
            sigAttri,_= self.create_hist_struct(fileName=sig, color=color)
            tray = I3Tray()
            tray.Add("I3Reader", filenamelist= list(glob.glob(sig_path+"LLPSim*/*.gz")))
            tray.Add(HistogramLLPs, histAttri=sigAttri , out_dir = args.outdir, GCDFile = GCD_path)
            tray.Execute()

        
        # Stack call here


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
        print("Loading the DOM locations from the GCD file")
        for i, key in enumerate(geometry.omgeo.keys()):
            if i % step == 0:
                print( "{0}/{1} = {2}%".format(i,len(geometry.omgeo.keys()), int(round(i/len(geometry.omgeo.keys())*100))))
                
            if key.om in [61, 62, 63, 64] and key.string <= 81: #Remove IT...
                continue

            pos = geometry.omgeo[key].position

            if pos.z > 1500:
                continue
                
            xyList.append(pos)
            i+=1
        
        return MuonGun.ExtrudedPolygon(xyList, padding) 


class HistogramLLPs(icetray.I3Module):

    def __init__(self,ctx):
        icetray.I3Module.__init__(self,ctx)
        self.AddParameter("out_dir", "out_dir", None)
        self.AddParameter("histAttr", "histAttr")
        self.gcdFile = self.AddParameter("GCDFile", "GCDFile", "")
    
    def Configure(self): 
        self.out_dir = self.GetParameter("out_dir")
        self.weights = []
        hist_data = {
                            #   "gaplength"             : {"bins": 100, "bounds": [0, 500]},
                            #   "zenith"                : {"bins": 20,  "bounds": [0, 1.7]},
                            #   "prodz"                 : {"bins": 20,  "bounds": [-800, 800]},
                            #   "decayz"                : {"bins": 20,  "bounds": [-800, 800]},
                              "Edeposited"            : [100, 0, 1000],
                              "totalInitialE"         : [100, 0, 20000],
                              "totalMCPulseCharge"    : [100, 0, 4000],
                              "totalDOMHits"          : [100, 0, 2500],

                             }
        # produce
        self.items_to_save = pd.DataFrame(hist_data, index =['bins', 'min', 'max'] )
        self.InitializeHistograms()
        
        # create surface for detector volume
        self.gcdFile = self.GetParameter("GCDFile")
        if self.gcdFile != "":
            self.surface = MakeSurface(self.gcdFile, 0)
        else:
            self.surface = MuonGun.Cylinder(1000,500) # approximate detector volume
                              
    # def AddHistAttri(self):
    #     for columnName, columnData in self.items_to_save.iteritems():
            
    #         self.items_to_save = self.items_to_save[columnName].append(self.histAttr)
            
            # if "bins" not in self.items_to_save[key]:Stack
            #     self.items_to_save[key]["bins"] = 50
            # if "bounds" not in self.items_to_save[key]:
            #     self.items_to_save[key]["bounds"] = [-10, 10]

    def AppendHist(self, columnName, frameitem):
        self.items_to_save = self.items_to_save[columnName].append({[columnName] : frameitem}, ignore_index = True)

    def DAQ(self, frame):
        # which weight?
        if "muongun_weights" in frame:
            weight = frame["muongun_weights"].value
        else:
            weight = 1
        # fill histogram
        self.weights.append( weight )
        # self.AppendHist(frame, frame["LLPInfo"]["length"], self.items_to_save["gaplength"]["histogramdictionary"])
        # self.AppendHist(frame, frame["LLPInfo"]["prod_z"], self.items_to_save["prodz"]["histogramdictionary"])
        # self.AppendHist(frame, frame["LLPInfo"]["prod_z"]-frame["LLPInfo"]["length"]*np.cos(frame["LLPInfo"]["zenith"]), self.items_to_save["decayz"]["histogramdictionary"])
        # self.AppendHist(frame, frame["I3MCTree_preMuonProp"].get_head().dir.zenith, self.items_to_save["zenith"]["histogramdictionary"])
        self.AppendHist(columnName = 'Edeposited', frameitem= self.ComputeDepositedEnergy(frame))
        self.AppendHist(columnName = "Edeposited", frameitem = self.ComputeDepositedEnergy(frame))
        self.AppendHist(columnName = "totalInitialE", frameitem = self.ComputeTotalEnergyAtBoundary(frame))
        self.AppendHist(columnName = "totalMCPulseCharge", frameitem = self.ComputeTotalMCPulseCharge(frame))
        self.AppendHist(columnName = "totalDOMHits", frameitem = self.ComputeTotalDOMHits(frame))
    
        
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
    
    def SaveHist(self):
        for columnName, columnData in self.items_to_save.iteritems():
            # add hist attrib to dataframe at top 
            df = self.items_to_save[columnName] 
            df = df.concat(self.histAttr, df).reset_index(drop=True)
            # Create an HDF5 file
            df.to_hdf(f"{self.histAttri['legend']}_{columnName}.hdf5", key = 'df', mode = w)
            

# class Plot(icetray.I3Module):
#     def __init__(self,ctx):
#         icetray.I3Module.__init__(self,ctx)
#         self.outdir = self.AddParameter("out_dir", "out_dir", "")
#         self.hist_list = self.AddParameter("hist_list", "hist_list", "")

#     def Finish(self):
#         print("Total event rate trigger:", sum(self.weights))
#         # plot histograms
#         for key, val in self.items_to_save.items():
#             current_sub_dict = self.items_to_save[key]
#             print('In this iteration:  ', key)
#             plt.figure()
#             # plt.hist(current_sub_dict["histogramdictionary"]["trigger"], weights = self.weights, bins = current_sub_dict["bins"], range = current_sub_dict["bounds"], alpha = 0.3, color = "blue", label = "trigger")
#             # plt.hist(current_sub_dict["histogramdictionary"]["L2"], weights = self.weightsL2, bins = current_sub_dict["bins"], range = current_sub_dict["bounds"], alpha = 0.3, color = "red", label = "L2")
#             plt.legend()
#             plt.yscale("log")
#             plt.ylabel("Event Rate [Hz]")
#             plt.title(key)
#             plt.savefig(self.out_dir + key +"_histogram.png")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--sig_path", "-s", default="/data/user/axelpo/LLP-data/", required=False)
  parser.add_argument("--weight", "-w", type=float, required=False)
  parser.add_argument('--outdir', "-o", default="outdir/")
  parser.add_argument('--withbkg', "-b", action="store_true")
  args = parser.parse_args()
  stack = Stack()
  stack.makeHist(args)



# sig_path="/mnt/scratch/parrishv/samples_052724/sig/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628/"
# bkg_path="/data/sim/IceCube/2020/generated/CORSIKA-in-ice/20904/"
GCD_path= "/data/user/axelpo/LLP-at-IceCube/dark-leptonic-scalar-simulation/resources/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz"

