import os
import matplotlib.pyplot as plt
from icecube import icetray, dataio, dataclasses

# Directory and GCD file
directory = "/data/sim/IceCube/2023/filtered/dev7/GENIE/23315/0000000-0000999"
gcd_file = "/data/sim/IceCube/2023/filtered/dev7/GENIE/23315/0000000-0000999/OfflineFiltered_IC86.2024.genie_NuTau.023315.000262.i3.zst"

# Lists to store results
total_energy_deposited = []
total_mc_pulse_charge = []
total_dom_hits = []

# Limit processing to the first 10 files
file_count = 0
max_files = 1400
filter_overlap = {}
llp_unique_hits = 0

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".i3.zst"):
        filepath = os.path.join(directory, filename)
        
        # Increment file count and stop after 10 files
        file_count += 1
        if file_count > max_files:
            break
        
        try:
            # Open the I3 file
            i3_file = dataio.I3File(filepath, "r")
            frame_count = 0
            
            while i3_file.more():
                frame = i3_file.pop_frame()
                frame_count += 1
                
                # Process only P frames with SubEvent "InIceSplit"
                if frame.Stop == icetray.I3Frame.Physics and frame["I3EventHeader"].sub_event_stream == "InIceSplit":
                    # Check if OfflineFilterMask exists in the frame
                    if "OfflineFilterMask" in frame:
                        filter_mask = frame["OfflineFilterMask"]
                        
                        # Check if the frame passes the LLPFilter_25
                        if "LLPFilter_25" in filter_mask and filter_mask["LLPFilter_25"].condition_passed:
                            for filter_name, filter_status in filter_mask.items():
                                other_filters_passed = any(
                                    filter_status.condition_passed for filter_name, filter_status in filter_mask.items() if filter_name != "LLPFilter_25"
                                )
                                # count unique hits
                                if not other_filters_passed:
                                    llp_unique_hits += 1
                                
                                # Record the filter overlap
                                for filter_name, filter_status in filter_mask.items():
                                    if filter_name not in filter_overlap:
                                        filter_overlap[filter_name] = 0
                                    if filter_status.condition_passed:
                                        filter_overlap[filter_name] += 1

                            # Calculate total energy deposited
                            if "I3MCTree" in frame:
                                mc_tree = frame["I3MCTree"]
                                energy_deposited = 0
                                for particle in mc_tree:
                                    if particle.location_type == dataclasses.I3Particle.LocationType.InIce:
                                        energy_deposited += particle.energy
                                total_energy_deposited.append(energy_deposited)
                            
                            # Calculate total MC pulse charge
                            if "SplitInIcePulses" in frame:
                                pulse_map_mask = frame["SplitInIcePulses"]
                                pulse_map = pulse_map_mask.apply(frame)
                                mc_pulse_charge = 0
                                for dom, pulses in pulse_map.items():
                                    for pulse in pulses:
                                        mc_pulse_charge += pulse.charge
                                total_mc_pulse_charge.append(mc_pulse_charge)
                            
                            # Calculate total DOM hits
                            if "SplitInIcePulses" in frame:
                                pulse_map_mask = frame["SplitInIcePulses"]
                                pulse_map = pulse_map_mask.apply(frame)
                                dom_hits = len(pulse_map.keys())
                                total_dom_hits.append(dom_hits)
        except Exception as e:
            print(f"Error processing file {filepath}: {e}")
            continue

# Plotting the histograms for all variables
print("Processing complete. Plotting results...")
output_dir = "/home/vparrish/icecube/llp_ana/reco_studies/microNN_filter/outdir/July2025"
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

# Plot total energy deposited
plt.figure()
plt.hist(total_energy_deposited, bins=100, range=(0, 12000), alpha=0.75, color='purple', edgecolor='black')
# plt.xscale('log')  # Set x-axis to logarithmic scale
plt.title("Distribution of Total Energy Deposited\nGENIE Pass 3 23315 MC Set")
plt.xlabel("Energy Deposited (GeV)")
plt.ylabel("Frequency")
plt.grid(True)
plt.savefig(f"{output_dir}/total_energy_deposited.png")
plt.show()

# Plot total MC pulse charge
plt.figure()
plt.hist(total_mc_pulse_charge, bins=100, range=(0, 600), alpha=0.75, color='purple', edgecolor='black')
plt.title("Distribution of Total MC Pulse Charge\nGENIE Pass 3 23315 MC Set")
plt.xlabel("MC Pulse Charge")
plt.ylabel("Frequency")
plt.grid(True)
plt.savefig(f"{output_dir}/total_mc_pulse_charge.png")
plt.show()

# Plot total DOM hits
plt.figure()
plt.hist(total_dom_hits, bins=50, range=(0, 200), alpha=0.75, color='purple', edgecolor='black')
plt.title("Distribution of Total DOM Hits\nGENIE Pass 3 23315 MC Set")
plt.xlabel("Number of DOM Hits")
plt.ylabel("Frequency")
plt.grid(True)
plt.savefig(f"{output_dir}/total_dom_hits.png")
plt.show()

# Plotting the overlap results
print("Calculating filter overlaps...")

# Add LLP unique hits to the overlap dictionary for plotting
filter_overlap["LLPFilter_25_Unique"] = llp_unique_hits
filtered_overlap = {key: value for key, value in filter_overlap.items() if key != "LLPFilter_25"}
print(f"removed LLPFilter_25 from overlap dictionary, now contains {len(filtered_overlap)} filters.")

# Use filtered_overlap for both keys and values in the bar plot
plt.figure()
plt.bar(filtered_overlap.keys(), filtered_overlap.values(), color='purple', edgecolor='black')
plt.title("Overlap Between LLPFilter_25 and Other Filters")
plt.xlabel("Filter Name")
plt.ylabel("Number of Overlapping Events")
plt.xticks(rotation=45, ha='right')
plt.grid(True)
plt.tight_layout()
plt.savefig(f"{output_dir}/filter_overlap.png")

print("Plots saved as PNG files.")