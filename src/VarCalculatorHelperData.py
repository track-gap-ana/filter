from icecube import icetray, dataio, dataclasses
import logging
# Set global logger
logger = logging.getLogger(__name__)

class VarCalculatorHelperData:
    def __init__(self, frame):
        self.frame = frame

    def ComputeTotalRecoPulseCharge(self):
        totalCharge = 0
        if 'SplitInIcePulses' in self.frame:
            pulse_series_map_mask = self.frame['SplitInIcePulses']
            pulse_series_map = pulse_series_map_mask.apply(self.frame)
            for key, item in pulse_series_map:
                totalCharge += sum([pulse.charge for pulse in item])
        return totalCharge

    def ComputeTotalDOMHits(self):
        logger.debug("Computing total DOM hits")
        totalHits = 0
        if 'SplitInIcePulses' in self.frame:
            pulse_series_map_mask = self.frame['SplitInIcePulses']
            pulse_series_map = pulse_series_map_mask.apply(self.frame)
            for key, item in pulse_series_map:
                totalHits += len(item)
        return totalHits

    def ComputeTimeOfFirstPulse(self):
        firstPulseTime = float('inf')
        if 'SplitInIcePulses' in self.frame:
            pulse_series_map_mask = self.frame['SplitInIcePulses']
            pulse_series_map = pulse_series_map_mask.apply(self.frame)
            for key, item in pulse_series_map:
                for pulse in item:
                    if pulse.time < firstPulseTime:
                        firstPulseTime = pulse.time
        return firstPulseTime

    def ComputeChargeWeightedStdDev(self):
        charges = []
        times = []
        if 'SplitInIcePulses' in self.frame:
            pulse_series_map_mask = self.frame['SplitInIcePulses']
            pulse_series_map = pulse_series_map_mask.apply(self.frame)
            for key, item in pulse_series_map:
                for pulse in item:
                    charges.append(pulse.charge)
                    times.append(pulse.time)
        if not charges:
            return 0
        mean_time = sum(times) / len(times)
        variance = sum((time - mean_time) ** 2 * charge for time, charge in zip(times, charges)) / sum(charges)
        return variance ** 0.5
    

    def RunCalculator(self, var):
        logger.debug(f"Running calculator for {var}")
        if 'lcsc_prediction' in self.frame:
            logger.debug("Cut applied, processing frame")
            total_charge = self.ComputeTotalRecoPulseCharge()
            total_hits = self.ComputeTotalDOMHits()
            first_pulse_time = self.ComputeTimeOfFirstPulse()
            charge_weighted_std_dev = self.ComputeChargeWeightedStdDev()
            if var == 'totalDOMHits': return total_hits
            if var == 'totalPulseCharge': return total_charge
            if var == 'firstPulseTime': return first_pulse_time
            if var == 'chargeWeightedStdDev': return charge_weighted_std_dev
            return 0
        else:
            return 0