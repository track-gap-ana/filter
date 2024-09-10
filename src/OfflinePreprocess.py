import subprocess
import os
import yaml
import logging

logger = logging.getLogger(__name__)

class OfflineFilter:
    """
    Class representing an offline filter for processing files in a directory.

    Args:
        indir (str): The input directory containing the files to be processed.
        outdir (str): The output directory where the processed files will be saved.
        config_samples (str): The path to the configuration file containing sample information.
        fast (bool, optional): Flag indicating whether to process files quickly. Defaults to False.
    """

    def __init__(self, outdir, config_samples, indir, fast):
        self.outdir = outdir
        self.config_samples = config_samples
        self.indir = indir
        self.n = 500 if fast is True else -1

    def configure(self):
        """
        Unpacks the YAML file containing sample information.
        """
        with open(self.config_samples, 'r') as file:
            samples = yaml.safe_load(file)

        self.TOP_DIR = list(samples['sig'].keys())[0]
        self.GCD_PATH = samples['gcd']
        self.VERSION = samples['version']
        logger.debug("Unpacked YAML file")

    def construct_command(self, filename):
        """
        Constructs the command for executing the shell script.

        Args:
            filename (str): The name of the file to be processed.

        Returns:
            str: The constructed command.
        """
        self.configure()
        infile = os.path.join(self.indir, filename)
        outdir = os.path.join(self.outdir, self.VERSION)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        output_file = os.path.join(self.outdir, filename.replace("online", "offline"))
        logger.debug(f"Infile: {infile}")
        logger.debug(f"Outdir: {outdir}")
        logger.debug(f"Output file: {output_file}")
        return f"python /home/vparrish/icecube/llp_ana/reco_studies/icetray/src/offline_filterscripts/resources/scripts/filter_SDST.py -i {infile} -g {self.GCD_PATH} -o {output_file} -n {self.n}"

    def run(self):
        """
        Runs the offline filter on the files in the input directory.
        """
        logger.debug("Starting the run method")
        # Iterate through the files in the input directory
        logger.debug(f"Input directory: {self.indir}")
        for filename in os.listdir(self.indir):
            if filename.endswith(".i3.gz"):
                logger.debug(f"Processing file: {filename}")
                command = self.construct_command(filename)
                # Execute the shell script
                try:
                    logger.debug(f"Executing shell script for {filename}")
                    subprocess.run(command, shell=True, check=True)
                    logger.debug(f"Shell script executed successfully for {filename}.")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error executing shell script for {filename}: {e}")

if __name__ == "__main__":
    # Create an instance of OfflineFilter and run it
    offline_filter = OfflineFilter()
    offline_filter.run()
