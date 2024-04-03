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

                             }
        self.InitializeHistograms()
        
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

    def SaveInfo(self, frame, frameitem, listdictionary):
        listdictionary["trigger"].append(frameitem)

    def Finish(self):
        print("Total event rate trigger:", sum(self.weights))
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


tray = I3Tray()
sig_path="/mnt/scratch/parrishv/samples_052724/sig/DarkLeptonicScalar.mass-115.eps-5e-6.nevents-250000_ene_1e2_2e5_gap_50_240202.203241628/"
#bkg_path
folder_path="/mnt/home/parrishv/mount/icecube/dnn/var_test/plots/"

tray.Add("I3Reader", filenamelist= list(glob.glob(sig_path+"LLPSim*/*.gz")))
tray.Add(HistogramLLPs, folder_path = folder_path, GCDFile = "/mnt/scratch/parrishv/samples_052724/sig/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz")
tray.Execute()
