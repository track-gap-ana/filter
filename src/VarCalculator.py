from icecube import icetray, dataio, dataclasses, MuonGun

class VarCalculator:
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