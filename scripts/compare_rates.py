import glob
import os
import matplotlib.pyplot as plt
import ast
import numpy as np

def extract_llpfilter_rates(file_path):
    """Extract rates for LLPFilter_25 and Overall frame rate from the given file."""
    llp_rates = []
    overall_frame_rates = []
    with open(file_path, 'r') as f:
        for line in f:
            if 'LLPFilter_25' in line:
                try:
                    if 'Rate:' in line:
                        rate_str = line.split('Rate:')[-1].strip().split()[0]
                        rate = float(rate_str)
                        llp_rates.append(rate)
                except ValueError:
                    print("Warning: Could not parse LLPFilter_25 rate from line: {}".format(line))
                    continue
            elif 'Overall frame rate:' in line:
                try:
                    rate_str = line.split('Overall frame rate:')[-1].strip().split()[0]
                    rate = float(rate_str)
                    overall_frame_rates.append(rate)
                except ValueError:
                    print("Warning: Could not parse Overall frame rate from line: {}".format(line))
                    continue
    return llp_rates, overall_frame_rates
    
def extract_filter_counts(file_path):
    """Extract filter counts for LLPFilter_25 and average count of other filters from the given file."""
    counts_25 = []
    average_other_counts = []
    with open(file_path, 'r') as f:
        for line in f:
            if 'OfflineFilterMask count:' in line:
                try:
                    count_dict = ast.literal_eval(line.split('OfflineFilterMask count:')[-1].strip())
                    # Extract counts for filters ending in _25
                    counts_25.extend([count for filter_name, count in count_dict.items() if filter_name.endswith('_25')])
                    # Calculate the average count excluding LLPFilter_25
                    other_counts = [count for filter_name, count in count_dict.items() if filter_name != 'LLPFilter_25']
                    if other_counts:
                        average_other_counts.append(sum(other_counts) / len(other_counts))
                except (ValueError, SyntaxError):
                    print("Warning: Could not parse OfflineFilterMask counts from line: {}".format(line))
                    continue
    return counts_25, average_other_counts

def aggregate_rates(directory):
    """Aggregate LLPFilter_25 rates and Overall frame rates across all files in the given directory."""
    llp_rates = []
    overall_frame_rates = []
    files = glob.glob(os.path.join(directory, '*calc_rates.txt'))
    if not files:
        print(f"Warning: No calc_rates.txt files found in directory: {directory}")
        return llp_rates, overall_frame_rates

    for file_path in files:
        file_llp_rates, file_overall_frame_rates = extract_llpfilter_rates(file_path)
        llp_rates.extend(file_llp_rates)
        overall_frame_rates.extend(file_overall_frame_rates)
    return llp_rates, overall_frame_rates

def aggregate_counts(directory):
    """Aggregate LLPFilter_25 counts and average counts of other filters across all files in the given directory."""
    counts_25 = []
    average_other_counts = []
    files = glob.glob(os.path.join(directory, '*calc_rates.txt'))
    if not files:
        print(f"Warning: No calc_rates.txt files found in directory: {directory}")
        return counts_25, average_other_counts

    for file_path in files:
        file_counts_25, file_average_other_counts = extract_filter_counts(file_path)
        counts_25.extend(file_counts_25)
        average_other_counts.extend(file_average_other_counts)
    return counts_25, average_other_counts

def plot_average_filter_rates(directory, output_file):
    """Plot the average rates of all filters from the given directory."""
    files = glob.glob(os.path.join(directory, '*.txt'))
    if not files:
        print(f"Warning: No txt files found in directory: {directory}")
        return

    filter_rates = {}
    print(f"Processing files in directory: {directory}")

    # Extract filter rates from files
    for file_path in files:
        with open(file_path, 'r') as f:
            for line in f:
                if 'OfflineFilterMask count:' in line:
                    try:
                        count_dict = ast.literal_eval(line.split('OfflineFilterMask count:')[-1].strip())
                        for filter_name, count in count_dict.items():
                            if filter_name not in filter_rates:
                                filter_rates[filter_name] = []
                            filter_rates[filter_name].append(count)
                    except (ValueError, SyntaxError):
                        print(f"Warning: Could not parse OfflineFilterMask rates from line: {line}")
                        continue

    # Calculate average rates for each filter
    average_rates = {filter_name: np.mean(rates) for filter_name, rates in filter_rates.items()}

    # Plot average rates
    filters = list(average_rates.keys())
    averages = list(average_rates.values())

    plt.figure(figsize=(10, 6))
    plt.bar(filters, averages, color='purple', alpha=0.7)
    plt.xlabel('Filter Name')
    plt.ylabel('Average Rate (Hz)')
    plt.title('Average Filter Rates')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.show()

def plot_with_ratios(data_2025, data_2024, bins, xlabel, ylabel, title, output_file):
    """Plot histograms with a ratio subplot beneath."""
    # Compute histograms
    hist_2025, bin_edges = np.histogram(data_2025, bins=bins)
    hist_2024, _ = np.histogram(data_2024, bins=bins)

    # Compute ratios
    ratios = np.divide(hist_2025, hist_2024, out=np.zeros_like(hist_2025, dtype=float), where=hist_2024 != 0)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2  # Calculate bin centers for scatter plot

    # Create figure with two subplots
    fig, (ax_main, ax_ratio) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # Main plot (histograms)
    ax_main.hist(data_2025, bins=bins, alpha=0.5, label='2025', color='purple')
    ax_main.hist(data_2024, bins=bins, alpha=0.5, label='2024', color='orange')
    ax_main.set_ylabel(ylabel)
    ax_main.set_title(title)
    ax_main.legend()

    # Ratio plot (scatter points)
    ax_ratio.scatter(bin_centers, ratios, color='purple', marker='x', label='2025/2024 Ratio')
    ax_ratio.set_xlabel(xlabel)
    ax_ratio.set_ylabel('Ratio (2025/2024)')
    ax_ratio.axhline(1, color='black', linestyle='--', linewidth=1)  # Reference line at ratio = 1
    ax_ratio.legend()

    # Save and show the plot
    plt.tight_layout()
    plt.savefig(output_file)
    plt.show()

def main():
    # Directories for the runs
    dir_2025 = '/data/exp/IceCube/2025/filtered/Offline/0613/Run00141028'
    dir_2024 = '/data/exp/IceCube/2025/filtered/Offline/0529/Run00140970'

    # Aggregate rates
    llp_rates_2025, overall_frame_rates_2025 = aggregate_rates(dir_2025)
    llp_rates_2024, overall_frame_rates_2024 = aggregate_rates(dir_2024)

    # Aggregate counts
    counts_25_2025, average_other_counts_2025 = aggregate_counts(dir_2025)
    counts_25_2024, average_other_counts_2024 = aggregate_counts(dir_2024)

    # Plot rates with ratios
    plot_with_ratios(llp_rates_2025, llp_rates_2024, bins=20, xlabel='Rate (Hz)', ylabel='Frequency',
                     title='LLPFilter_25 Rates Comparison', output_file='../outdir/July2025/llpfilter_rates_with_ratios.png')

    plot_with_ratios(overall_frame_rates_2025, overall_frame_rates_2024, bins=20, xlabel='Rate (Hz)', ylabel='Frequency',
                     title='Overall Frame Rates Comparison', output_file='../outdir/July2025/overall_frame_rates_with_ratios.png')

    # Plot counts with ratios
    plot_with_ratios(counts_25_2025, counts_25_2024, bins=20, xlabel='Count', ylabel='Frequency',
                     title='LLPFilter_25 Counts Comparison', output_file='../outdir/July2025/llpfilter_counts_with_ratios.png')

    # plot_with_ratios(average_other_counts_2025, average_other_counts_2024, bins=20, xlabel='Count', ylabel='Frequency',
    #                  title='Average Other Filter Counts Comparison', output_file='../outdir/July2025/average_other_counts_with_ratios.png')

    # Plot average filter rates
    plot_average_filter_rates(dir_2025, '../outdir/July2025/average_filter_rates_2025.png')

if __name__ == "__main__":
    main()