import os
import yaml
import logging
import glob

#!/usr/bin/env python

logger = logging.getLogger(__name__)

class Online:
    """
    Class for online preprocessing of trigger files.

    Args:
        args: An object containing command line arguments. Passed by `track_gap_ana.py`.

    Attributes:
        args: An object containing command line arguments.
        TOP_DIR: The top directory path.
        SIGNAL_TYPES: A list of signal types.
        GCD_PATH: The path to the GCD file.
        VERSION: The version of the samples.

    Methods:
        load_samples: Loads the samples from a configuration file.
        alter_name: Alters the name of a signal type.
        process_files: Processes the files.

    """

    def __init__(self, args):
        self.args = args
        self.load_samples()

    def load_samples(self):
        """
        Loads the samples from a configuration file.
        """
        with open(self.args.config_samples, 'r') as file:
            samples = yaml.safe_load(file)

        self.TOP_DIR = list(samples['sig'].keys())[0]
        self.SIGNAL_TYPES = [samples['sig'][self.TOP_DIR]]
        self.GCD_PATH = samples['gcd']
        self.VERSION = samples['version']

    def alter_name(self, signal_type):
        """
        Alters the name of a signal type.

        Args:
            signal_type: The original signal type located in samples.yaml.

        Returns:
            The altered signal type.

        """
        if "*" == signal_type:
            return "full"
        if self.args.fast:
            return f"{signal_type}_test"
        return signal_type

    def process_files(self):
        """
        Processes the files.
        """
        logger.info("Processing files...")
        logger.debug(f'TOP_DIR: {self.TOP_DIR}')
        logger.info(f'SIGNAL_TYPES SELECTED: {self.SIGNAL_TYPES}\n')

        for signal_type in self.SIGNAL_TYPES:
            logger.info(f'Processing signal type: {signal_type}')
            dir_paths = glob.glob(f"{self.TOP_DIR}{signal_type}")
            signal_type = self.alter_name(signal_type)

            for dir_path in dir_paths:
                for dirpath, dirnames, filenames in os.walk(dir_path):
                    logger.debug(f'Processing directory {dirpath}')
                    if self.args.fast: filenames = filenames[:5]
                    for file in filenames:
                        if file.endswith('.i3') or file.endswith('.i3.gz'):
                            input_file = os.path.join(dirpath, file)
                            logger.info(f'Processing file: {input_file}')
                            command = f'PFRaw_to_DST_condor.sh {input_file} {self.VERSION} {self.GCD_PATH} {signal_type.replace("*","")} {self.args.outdir}'
                            logger.debug(f'Running shell script with command:\n\n{command}\n')
                            os.system(command)
                            logger.info(f'File {input_file} processed successfully.')

if __name__ == "__main__":
    # Create an instance of the Online class
    online = Online(args)
    # Call the process_files method
    online.process_files()
