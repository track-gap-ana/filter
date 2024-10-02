#!/usr/bin/env python
import os
import yaml
import logging
import glob
import datetime
import socket
import re

import ConfigHelper

logger = logging.getLogger(__name__)

class CondorFilter():
    """
    Class for online preprocessing of trigger files.

    Args:
        args: An object containing command line arguments. Passed by `track_gap_ana.py`.

    Attributes:
        args: An object containing command line arguments.
        TOP_DIR: The top directory path.
        SIGNAL_TYPES: A list of signal typrCoes.
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
        self.DIR_TYPES = list(samples['sig'].keys())[0]
        self.SIGNAL_TYPES = [samples['sig'][self.DIR_TYPES]]
        self.GCD_PATH = samples['gcd']
        self.VERSION = samples['version']

        self.TOP_DIR = self.args.sigs_path

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
        if "*" is signal_type:
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
            self.PROCESS="clean" if self.args.clean else self.args.type
            logger.info(f'TOP OUTPUTDIR: {self.OUTPUTDIR}')
            logger.info(f'TOP LOGDIR: {self.LOGDIR}')
            logger.info(f'TOP ERRORDIR: {self.ERRORDIR}')
            logger.info(f'TOP PROCESS: {self.PROCESS}')

    def makeSubDirs(self, SUB_DIR):
        
        self.ConfigHelper.makeDirs(os.path.join(self.OUTPUTDIR, SUB_DIR))
        self.ConfigHelper.makeDirs(os.path.join(self.LOGDIR, SUB_DIR))
        self.ConfigHelper.makeDirs(os.path.join(self.ERRORDIR, SUB_DIR))
    
    def writeDAG(self, counter, filenames, job_suffix, dag_file, indir, SUB_DIR):
        for infile in filenames:
            if 'LLPSimulation' in infile and (infile.endswith('.i3') or infile.endswith('.i3.gz')):
                logger.debug(f'Processing file: {infile}')
                input_file = os.path.join(indir, infile)
                BASENAME = os.path.basename(infile[:-7])
                if self.args.type == 'online':
                    UNIQUEJOBID = indir.split("/")[-1]
                elif self.args.type == 'offline' or self.args.type == 'stack':
                    UNIQUEJOBID = re.search(r'(LLPSimulation.*?\.i3(?:\.gz)?)$', infile).group(1)
                    
                JOBNAME = f'{self.VERSION}_{self.signal_type_name}_{job_suffix}_{datetime.datetime.now().strftime("%m%d%Y")}'
                JOBID = f"{JOBNAME}_{UNIQUEJOBID}_{self.args.version}"
                logger.debug(f'JOBID: {JOBID}')
                logger.debug(f'JOBNAME: {JOBNAME}')
                dag_file.write(f"JOB {JOBID} {self.EXEDIR}/DAGOneJob.submit\n")
                dag_file.write(f'VARS {JOBID} JOBNAME="{JOBNAME}" SUBDIR="{SUB_DIR}" GCD_FILE="{self.GCD_PATH}" INFILE="{input_file}" BASENAME="{BASENAME}"\n')
                counter += 1  # Increment file counter
            if self.args.fast and counter >= 5:  # Check again in case the limit is reached within the inner loop
                break
    def process_files(self, signal_types, job_suffix):
        """
        Generalized function to process files with directory counter logic.
        """
        logger.info("Processing files...")
        logger.info(f'SIGNAL_TYPES SELECTED: {signal_types}\n')
        logger.info(f'JOB_SUFFIX SELECTED: {job_suffix}\n')
        self.setDirs(exedirOnly=True)
        with open(f"{self.EXEDIR}/myJobs.dag", "w") as dag_file:
            for signal_type in signal_types:
                logger.info(f'Processing signal type: {signal_type}')
                dir_paths = glob.glob(f"{self.TOP_DIR}{signal_type}")
                self.signal_type_name = self.alter_name(signal_type)
                self.setDirs()
                os.system( f'. builddag.sh {self.OUTPUTDIR} {self.LOGDIR} {self.ERRORDIR} {self.EXEDIR} {self.PROCESS}')
                counter = 0  # Initialize directory counter
                for dir_path in dir_paths:
                    SUB_DIR = os.path.basename(dir_path)
                    logger.debug(f'Directory path: {dir_path}')
                    logger.debug(f'Setting sub-directory: {SUB_DIR}')  
                    self.makeSubDirs(SUB_DIR)
                    # Write DAG file for online preprocessing submission
                    if self.args.type == 'online':
                        for indir, dirnames, filenames in os.walk(dir_path):
                            logger.debug(f'Processing directory for online preprocessing: {indir}')
                            self.writeDAG(counter, filenames, job_suffix, dag_file, indir, SUB_DIR)
                    # Write DAG file for offline OR read_clean preprocessing submission
                    else:
                        filenames = os.listdir(dir_path)
                        if not filenames:
                            logger.warning(f'Directory empty, skipping: {dir_path}')
                            continue  # Skip empty directories
                        logger.debug(f'Processing directory for {job_suffix}: {dir_path}')
                        logger.debug(f'Files in directory: {filenames}')
                        self.writeDAG(counter, filenames, job_suffix, dag_file, dir_path, SUB_DIR)
                        
        os.system(f". SubmitDag.sh {self.EXEDIR}")

    # Assuming process_online_files is similar, refactor it as well
    def process_online_files(self):
        self.process_files(self.SIGNAL_TYPES, 'online_preprocess')

    # Refactor process_offline_files to use the generalized function
    def process_offline_files(self):
        self.process_files(self.SIGNAL_TYPES, 'offline_preprocess')
    
    def recoAndClean_files(self):
        self.process_files(self.SIGNAL_TYPES, 'recoAndClean_preprocess')

if __name__ == "__main__":
    # Create an instance of the Online class
    dag_proc = CondorFilter(args)
    # Call the process_files method
    dag_proc.process_online_files()
    dag_proc.process_offline_files()
    dag_proc.recoAndClean_files()
