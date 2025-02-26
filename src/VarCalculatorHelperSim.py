from icecube import icetray, dataio, dataclasses, MuonGun


class VarCalculatorHelperSim:
    def __init__(self, surface, frame):
        self.surface = surface
        self.frame = frame
    
    def ComputeDepositedEnergy(self):
        edep = 0
        # Change name scheme between sig and bkg sim samples 
        if 'I3MCTree' in self.frame: MCTree = 'I3MCTree'
        else: MCTree = 'SignalI3MCTree'
        for track in MuonGun.Track.harvest(self.frame[MCTree], self.frame['MMCTrackList']):
            # Find distance to entrance and exit from sampling volume
            intersections = self.surface.intersection(track.pos, track.dir)
            # Get the corresponding energies
            e0, e1 = track.get_energy(intersections.first), track.get_energy(intersections.second)
            # Accumulate
            edep +=  (e0-e1)
        return edep

    
    def ComputeTotalMCPulseCharge(self):
        totalCharge = 0
        for key, item in self.frame["I3MCPulseSeriesMap"]:
            totalCharge += sum([pulse.charge for pulse in item])
        return totalCharge
    
    def ComputeTotalDOMHits(self):
        totalHits = 0
        for key, item in self.frame["I3MCPulseSeriesMap"]:
            totalHits += 1
        return totalHits
    
    def ComputeTimeOfFirstPulse(self):
        firstPulseTime = float('inf')
        for key, item in self.frame["I3MCPulseSeriesMap"]:
            for pulse in item:
                if pulse.time < firstPulseTime:
                    firstPulseTime = pulse.time
        return firstPulseTime
    
    def ComputeChargeWeightedStdDev(self):
        totalCharge = 0
        totalWeightedCharge = 0
        for key, item in self.frame["I3MCPulseSeriesMap"]:
            for pulse in item:
                totalCharge += pulse.charge
                totalWeightedCharge += pulse.charge * pulse.time
        meanTime = totalWeightedCharge / totalCharge
        chargedWeightStdDev = 0
        for key, item in self.frame["I3MCPulseSeriesMap"]:
            for pulse in item:
                chargedWeightStdDev += (pulse.charge * (pulse.time - meanTime) ** 2)
        chargedWeightStdDev = (chargedWeightStdDev / totalCharge) ** 0.5
        return chargedWeightStdDev
    
    def ComputeTotalEnergyAtBoundary(self):
        totalE = 0
        for p in self.frame["I3MCTree_preMuonProp"].children(self.frame["I3MCTree_preMuonProp"].get_head()):
            totalE += p.energy
        return totalE
    
    def RunCalculator(self, var):
        if var == 'Edeposited': return self.ComputeDepositedEnergy()
        if var == 'totalMCPulseCharge': return self.ComputeTotalMCPulseCharge()
        if var == 'totalDOMHits': return self.ComputeTotalDOMHits()
        if var == 'totalInitialE': return self.ComputeTotalEnergyAtBoundary()
        if var == 'firstPulseTime': return self.ComputeTimeOfFirstPulse()
        if var == 'chargeWeightedStdDev': return self.ComputeChargeWeightedStdDev()
        return 0
 