import os
import yaml
import logging
import glob
import datetime
import socket

import ConfigHelper

#!/usr/bin/env python

logger = logging.getLogger(__name__)

class CondorFilter():
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
        self.ConfigHelper = ConfigHelper.ConfigHelper(config_var=args.config_var, config_samples=args.config_samples)


    def check_socket(self):
        # Get the current hostname
        hostname = socket.gethostname()

        # Check if the hostname is not 'submit-1'
        if 'submit-1' not in hostname:
            logger.warning("Please log into submit-1.icecube.wisc.edu to run this script.")
            logger.error("This script can only be run on a condor submission node.")

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
        if self.args.fast is True:
            print("fast mode")
            signal_type = "test"
        if "*" in signal_type:
            signal_type = "full"
        return signal_type.replace("*","")
    
    def setDirs(self, exedirOnly=False):
        CURRENTDATE = datetime.datetime.now().strftime("%d%m%y")
        if exedirOnly:
            self.EXEDIR = os.path.join(os.getcwd(), "condor_exe_dirs", f"condor-{CURRENTDATE}")
            self.ConfigHelper.makeDirs(self.EXEDIR)
            logger.info(f'TOP EXEDIR: {self.EXEDIR}')
        else:
            self.OUTPUTDIR=f"{self.args.outdir}/output/{self.VERSION}/{CURRENTDATE}/{self.signal_type_name}/"
            self.LOGDIR=f"{self.args.outdir}/output/{self.VERSION}/{CURRENTDATE}/{self.signal_type_name}/out/"
            self.ERRORDIR=f"{self.args.outdir}/error/{self.VERSION}/{CURRENTDATE}/{self.signal_type_name}/" 
            logger.info(f'TOP OUTPUTDIR: {self.OUTPUTDIR}')
            logger.info(f'TOP LOGDIR: {self.LOGDIR}')
            logger.info(f'TOP ERRORDIR: {self.ERRORDIR}')

    def makeSubDirs(self, SUB_DIR):
        
        self.ConfigHelper.makeDirs(os.path.join(self.OUTPUTDIR, SUB_DIR))
        self.ConfigHelper.makeDirs(os.path.join(self.LOGDIR, SUB_DIR))
        self.ConfigHelper.makeDirs(os.path.join(self.ERRORDIR, SUB_DIR))
    
    def process_online_files(self):
        """
        Processes the files.
        """
        logger.info("Processing files...")
        logger.debug(f'TOP_DIR: {self.TOP_DIR}')
        logger.info(f'SIGNAL_TYPES SELECTED: {self.SIGNAL_TYPES}\n')
        self.setDirs(exedirOnly=True)

        with open(f"{self.EXEDIR}/myJobs.dag", "w") as dag_file:
            for signal_type in self.SIGNAL_TYPES:
                logger.info(f'Processing signal type: {signal_type}')
                dir_paths = glob.glob(f"{self.TOP_DIR}{signal_type}")
                self.signal_type_name = self.alter_name(signal_type)
                self.setDirs()
                os.system( f'. builddag.sh {self.OUTPUTDIR} {self.LOGDIR} {self.ERRORDIR} {self.EXEDIR} {self.args.type}')
                dir_counter = 0  # Initialize directory counter
                for dir_path in dir_paths:
                    SUB_DIR = os.path.basename(dir_path)
                    logger.debug(f'Setting sub-directory: {SUB_DIR}')  
                    self.makeSubDirs(SUB_DIR)
                    
                    for indir, dirnames, filenames in os.walk(dir_path):
                        if self.args.fast and dir_counter >= 5:  # Check if fast mode is enabled and limit is reached
                            break  # Exit the loop after processing 5 directories
                        for infile in filenames:
                            if infile.startswith('LLP') and (infile.endswith('.i3') or infile.endswith('.i3.gz')):
                                input_file = os.path.join(indir, infile)
                                BASENAME = os.path.basename(infile[:-7])
                                UNIQUEJOBID = indir.split("/")[-1]
                                JOBNAME = f'{self.VERSION}_{self.signal_type_name}_online_preprocess_{datetime.datetime.now().strftime("%m%d%Y")}'
                                JOBID = f"{JOBNAME}_{UNIQUEJOBID}_{self.args.version}"
                                dag_file.write(f"JOB {JOBID} {self.EXEDIR}/DAGOneJob.submit\n")
                                dag_file.write(f'VARS {JOBID} JOBNAME="{JOBNAME}" SUBDIR="{SUB_DIR}" GCD_FILE="{self.GCD_PATH}" INFILE="{input_file}" BASENAME="{BASENAME}"\n')
                        dir_counter += 1  # Increment directory counter
                        if self.args.fast and dir_counter >= 5:  # Check again in case the limit is reached within the inner loop
                            break
        os.system(f". SubmitDag.sh {self.EXEDIR}")

    def process_offline_files(self):
        """
        Processes the files.
        """
        logger.info("Processing files...")
        logger.info(f'SIGNAL_TYPES SELECTED: {self.SIGNAL_TYPES}\n')
        EXEDIR = self.setExeDir()
        with open(f"{self.EXEDIR}/myJobs.dag", "w") as dag_file:
            for signal_type in self.SIGNAL_TYPES:
                logger.info(f'Processing signal type: {signal_type}')
                signal_type = self.alter_name(signal_type)
                os.system( f'. builddag.sh {self.args.outdir} {self.VERSION} {signal_type} {self.EXEDIR} {self.args.type}')
                logger.debug(f'Execution directory: {self.EXEDIR}')
                # bit hacky but the dir has bias files in it as well - need to filter them out at some point, but for now looping through the first 100 will only select 6 non-bias files to process
                if self.args.fast is True: indir = os.listdir(self.args.sigs_path)[:100]
                else: indir = os.listdir(self.args.sigs_path)
                logger.debug(f'Processing files in directory: {self.args.sigs_path}')
                for infile in indir:
                    if infile.endswith('.i3.gz') and 'bias' not in infile:
                        logger.debug(f'Processing file: {infile}')
                        input_file = os.path.join(self.args.sigs_path, infile)
                        BASENAME = "LLPSimulation" + infile.split("LLPSimulation")[1].split(".i3.gz")[0]
                        JOBNAME = f'{self.VERSION}_{signal_type}_offline_preprocess_{datetime.datetime.now().strftime("%m%d%Y")}'
                        JOBID = f"{JOBNAME}_{BASENAME}_{self.args.version}"
                        dag_file.write(f"JOB {JOBID} {self.EXEDIR}/DAGOneJob.submit\n")
                        dag_file.write(f'VARS {JOBID} JOBNAME="{JOBNAME}" GCD_FILE="{self.GCD_PATH}" INFILE="{input_file}" BASENAME="{BASENAME}"\n')

        os.system(f". SubmitDag.sh {self.EXEDIR}")
        

if __name__ == "__main__":
    # Create an instance of the Online class
    dag_proc = CondorFilter(args)
    # Call the process_files method
    dag_proc.process_online_files()
    dag_proc.process_offline_files()
