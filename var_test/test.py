#!/usr/bin/env python3
#!/usr/bin/env python
import icecube
from icecube import icetray, dataio, dataclasses
from I3Tray import I3Tray
import glob
from datetime import datetime
import matplotlib.pyplot as plt
from icecube import MuonGun
import numpy as np
import argparse

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
    print("Finished loading DOMs... creating ExtrudedPolygon")
    surface = MuonGun.ExtrudedPolygon(xyList, padding)
    print("ExtrudedPolygon surface created.") 
    return surface

class HistogramLLPs(icetray.I3Module):

    def __init__(self,ctx):
        icetray.I3Module.__init__(self,ctx)
        self.AddParameter("folder_path", "folder_path", None)
        self.gcdFile = self.AddParameter("GCDFile", "GCDFile", "")
        
    def Configure(self): 
        self.folder_path = self.GetParameter("folder_path")
        self.weights = []
        self.weightsL2 = []
        self.items_to_save = {"gaplength"             : {"bins": 100, "bounds": [0, 500]},
                              "zenith"                : {"bins": 20,  "bounds": [0, 1.7]},
                              "prodz"                 : {"bins": 20,  "bounds": [-800, 800]},
                              "decayz"                : {"bins": 20,  "bounds": [-800, 800]},
                              "Edeposited"            : {"bins": 100, "bounds": [0, 1000]},
                              "totalInitialE"         : {"bins": 100, "bounds": [0, 20000]},
                              "totalMCPulseCharge"    : {"bins": 100, "bounds": [0,4000]},
                              "totalDOMHits"          : {"bins": 100, "bounds": [0,2500]},
                              "prodAlongPath"         : {"bins": 100, "bounds": [0,1]},

                             }
        self.InitializeHistograms()
        self.nevents = 0 # for counting
        
        # create surface for detector volume
        self.gcdFile = self.GetParameter("GCDFile")
        if self.gcdFile != "":
            self.surface = MakeSurface(self.gcdFile, 0)
        else:
            self.surface = MuonGun.Cylinder(1000,500) # approximate detector volume
                              
    def InitializeHistograms(self):
        for key, val in self.items_to_save.items():
            self.items_to_save[key]["histogramdictionary"] = {"trigger": [], "L2": []} # create lists to hold values
            if "bins" not in self.items_to_save[key]:
                self.items_to_save[key]["bins"] = 50
            if "bounds" not in self.items_to_save[key]:
                self.items_to_save[key]["bounds"] = [-10, 10]
        
    def DAQ(self, frame):
        # which weight?
        if "muongun_weights" in frame:
            weight = frame["muongun_weights"].value
        else:
            weight = 1
        # fill histogram
        self.weights.append( weight )
        self.SaveInfo(frame, frame["LLPInfo"]["length"], self.items_to_save["gaplength"]["histogramdictionary"])
        self.SaveInfo(frame, frame["LLPInfo"]["prod_z"], self.items_to_save["prodz"]["histogramdictionary"])
        self.SaveInfo(frame, frame["LLPInfo"]["prod_z"]-frame["LLPInfo"]["length"]*np.cos(frame["LLPInfo"]["zenith"]), self.items_to_save["decayz"]["histogramdictionary"])
        self.SaveInfo(frame, frame["I3MCTree_preMuonProp"].get_head().dir.zenith, self.items_to_save["zenith"]["histogramdictionary"])
        self.SaveInfo(frame, self.ComputeDepositedEnergy(frame), self.items_to_save["Edeposited"]["histogramdictionary"])
        self.SaveInfo(frame, self.ComputeTotalEnergyAtBoundary(frame), self.items_to_save["totalInitialE"]["histogramdictionary"])
        self.SaveInfo(frame, self.ComputeTotalMCPulseCharge(frame), self.items_to_save["totalMCPulseCharge"]["histogramdictionary"])
        self.SaveInfo(frame, self.ComputeTotalDOMHits(frame), self.items_to_save["totalDOMHits"]["histogramdictionary"])
        self.SaveInfo(frame, self.ComputeProdAlongPath(frame), self.items_to_save["prodAlongPath"]["histogramdictionary"])
        
        # count
        self.nevents += 1
        if self.nevents % 5000 == 0:
            print("Processed {} events".format(self.nevents))

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

    def ComputeProdAlongPath(self, frame):
        """ When along path in detector was the LLP produced?
        	
        Expressed as fraction prod_length/total_length.
        A number between 0 and 1.
        0 = detector entry, 1 = detector exit
        
        What should the distribution look like?
        Flat to first order modified by:
                - muons might stop in detector
                - muons lose energy = smaller LLP xsec
                - LLPs closer to exit have decay outside = not saved
        If distribution is not flat + above effects then
        cross section bias is too large.
        """
        # Take first MMCTrack, that is the MuonGun muon
        tracks = MuonGun.Track.harvest(frame['I3MCTree'], frame['MMCTrackList'])
        track = tracks[0]
        # Find distance to entrance and exit from detector volume
        intersections = self.surface.intersection(track.pos, track.dir)
        # Get total length in detector
        total_length = intersections.second - intersections.first
        # Get LLP prod length
        production = dataclasses.I3Position(frame["LLPInfo"]["prod_x"],
                                            frame["LLPInfo"]["prod_y"],
                                            frame["LLPInfo"]["prod_z"])
        prod_intersections = self.surface.intersection(production, track.dir)
        prod_length = -1*prod_intersections.first # entry point is BEHIND prod point, so neg length
        # fraction
        prodAlongPath = prod_length / total_length
        return prodAlongPath

    def SaveInfo(self, frame, frameitem, listdictionary):
        listdictionary["trigger"].append(frameitem)

    def Finish(self):
        print("Total event rate trigger:", sum(self.weights))
        print("Total number of events:", self.nevents)
        # plot histograms
        for key, val in self.items_to_save.items():
            current_sub_dict = self.items_to_save[key]
            print('In this iteration:  ', key)
            plt.figure()
            plt.hist(current_sub_dict["histogramdictionary"]["trigger"], weights = self.weights, bins = current_sub_dict["bins"], range = current_sub_dict["bounds"], alpha = 0.3, color = "blue", label = "trigger")
            plt.hist(current_sub_dict["histogramdictionary"]["L2"], weights = self.weightsL2, bins = current_sub_dict["bins"], range = current_sub_dict["bounds"], alpha = 0.3, color = "red", label = "L2")
            plt.legend()
            plt.yscale("log")
            plt.ylabel("Event Rate [Hz]")
            plt.title(key)
            plt.savefig(self.folder_path + key +"_histogram.png")


# create argparse
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--axel", action="store_true", default=False, dest="axels-folders", help="Is Axel running this script?")
params = vars(parser.parse_args())

if not params["axels-folders"]:
    # victoria is running this
    sig_path="/mnt/scratch/parrishv/samples_052724/sig/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628/"
    #bkg_path
    folder_path="/mnt/home/parrishv/mount/icecube/dnn/var_test/plots/"
    gcdfile = "/mnt/scratch/parrishv/samples_052724/sig/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz"
else:
    # axel is running this
    sig_path="/data/user/axelpo/LLP-data/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628/"
    folder_path="/data/user/axelpo/microNN_filter/var_test/plots/"
    gcdfile = "/data/sim/sim-new/downloads/GCD/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz"

tray = I3Tray()
tray.Add("I3Reader", filenamelist= list(glob.glob(sig_path+"LLPSim*/*.gz")))
tray.Add(HistogramLLPs, folder_path = folder_path, GCDFile = gcdfile)
tray.Execute()
