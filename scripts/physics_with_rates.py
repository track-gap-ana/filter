import os
import matplotlib.pyplot as plt
from icecube import icetray, dataio, dataclasses

# Directory and GCD file
directory = "/data/exp/IceCube/2025/filtered/Offline/0613/Run00141028"
gcd_file = "/data/exp/IceCube/2025/filtered/Offline/0613/Run00141028/Offline_IC86.2025_data_Run00141028_0613_89_852_GCD.i3.zst"
# List to store total charges for events passing the LLP filter
total_charges = []

# Limit processing to the first 200 files
file_count = 0
max_files = 400
llp_filter_count = 0  # Count of events passing LLPFilter_25
overlap_count = 0  # Count of events with overlap with other filters

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".i3.zst"):
        filepath = os.path.join(directory, filename)
        
        # Increment file count and stop after max_files
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
                
                # Process only Physics frames with SubEvent "InIceSplit"
                if frame.Stop == icetray.I3Frame.Physics and frame["I3EventHeader"].sub_event_stream == "InIceSplit":

                    # Check if OfflineFilterMask exists in the frame
                    if "OfflineFilterMask" in frame:
                        filter_mask = frame["OfflineFilterMask"]
                        
                        # Check if the frame passes the LLPFilter_25
                        if "LLPFilter_25" in filter_mask and filter_mask["LLPFilter_25"].condition_passed:
                            llp_filter_count += 1  # Increment LLP filter count
                            
                            # Check for overlap with other filters
                            other_filters = [key for key in filter_mask.keys() if key != "LLPFilter_25"]
                            passed_other_filter = any(filter_mask[key].condition_passed for key in other_filters)
                            
                            if passed_other_filter:
                                overlap_count += 1  # Increment overlap count
                            
                            # Check if SplitInIcePulses exists in the frame
                            if "SplitInIcePulses" in frame:
                                pulse_map_mask = frame["SplitInIcePulses"]
                                
                                # Unmask the pulse map
                                pulse_map = pulse_map_mask.apply(frame)
                                
                                # Calculate total charge for the event
                                total_charge = sum(pulse.charge for dom, pulses in pulse_map.items() for pulse in pulses)
                                
                                # Store the total charge
                                total_charges.append(total_charge)
                                print(f"Processed file: {filename}, Frame: {frame_count}, Total Charge: {total_charge:.2f} p.e.")

                            else:
                                print("SplitInIcePulses not found in frame. Skipping frame.")
        except Exception as e:
            print(f"Error processing file {filepath}: {e}")
            continue

# Plotting the histogram of total charges for events passing LLPFilter_25
print("Processing complete. Plotting results...")
print(f"Total events processed: {file_count}")
print(f"Total events passing LLPFilter_25: {llp_filter_count}")
print(f"Total events with overlap with other filters: {overlap_count}")
output_dir = "/home/vparrish/icecube/llp_ana/reco_studies/microNN_filter/outdir/July2025"
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

plt.figure()
plt.hist(total_charges, bins=100, range=(0, 500), alpha=0.75, color='purple', edgecolor='black')
plt.title("Distribution of Total Charge (LLPFilter_25 Passed)\nData, Run00141028")
plt.xlabel("Total Charge (p.e.)")  # Added units (photoelectrons)
plt.ylabel("Frequency")
plt.grid(True)
plt.savefig(f"{output_dir}/total_charge_distribution_llpfilter.png")
plt.show()

print("Plot saved as PNG file.")