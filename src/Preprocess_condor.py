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
        SIG_TOP: The top directory path.
        SAMPLE_TYPES: A list of signal types.
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
        hostname = socket.gethostname()
        if 'submit-1' not in hostname:
            logger.warning("Please log into submit-1.icecube.wisc.edu to run this script.")
            logger.error("This script can only be run on a condor submission node.")

    def load_samples(self):
        with open(self.args.config_samples, 'r') as file:
            samples = yaml.safe_load(file)
        self.DIR_TYPES = list(samples['sig'].keys())[0]
        self.SAMPLE_TYPES = [samples['sig'][self.DIR_TYPES]]
        self.GCD_PATH = samples['gcd']
        self.VERSION = samples['version']
        self.SIG_TOP = self.args.sigs_path
        self.BKG_TOP = self.args.bkg_path

    def alter_name(self, sample_type):
        if self.args.fast:
            print("fast mode")
            sample_type = f"{sample_type}_test"
        elif "*" is sample_type:
            sample_type = "full"
        else:
            sample_type = sample_type
        return sample_type.replace("*", "")

    def set_dirs(self, exedir_only=False):
        current_date = datetime.datetime.now().strftime("%d%m%y")
        if exedir_only:
            self.EXEDIR = os.path.join(os.getcwd(), "condor_exe_dirs", f"condor-{current_date}")
            self.ConfigHelper.makeDirs(self.EXEDIR)
            logger.info(f'TOP EXEDIR: {self.EXEDIR}')
        else:
            self.OUTPUTDIR = f"{self.args.outdir}/output/{self.VERSION}/{current_date}/{self.file_type_name}/"
            self.LOGDIR = f"{self.args.outdir}/output/{self.VERSION}/{current_date}/{self.file_type_name}/out/"
            self.ERRORDIR = f"{self.args.outdir}/error/{self.VERSION}/{current_date}/{self.file_type_name}/"
            self.PROCESS = "clean" if self.args.clean else self.args.type
            logger.info(f'TOP OUTPUTDIR: {self.OUTPUTDIR}')
            logger.info(f'TOP LOGDIR: {self.LOGDIR}')
            logger.info(f'TOP ERRORDIR: {self.ERRORDIR}')
            logger.info(f'TOP PROCESS: {self.PROCESS}')

    def make_sub_dirs(self, sub_dir):
        self.ConfigHelper.makeDirs(os.path.join(self.OUTPUTDIR, sub_dir))
        self.ConfigHelper.makeDirs(os.path.join(self.LOGDIR, sub_dir))
        self.ConfigHelper.makeDirs(os.path.join(self.ERRORDIR, sub_dir))

    def write_dag(self, counter, filenames, job_suffix, dag_file, indir, sub_dir):
        logger.debug(f'Files in directory: {filenames[:3]}')
        for infile in filenames:
            if infile.endswith('.i3') or infile.endswith('.i3.gz') or infile.endswith('.i3.zst') and ("corsika" in infile or 'LLPSimulation' in infile):
                logger.debug(f'Processing file: {infile}')
                input_file = os.path.join(indir, infile)
                basename = os.path.basename(infile[:-7])
                logger.debug(f"Basename: {basename}")
                if self.args.withbkg:
                    unique_job_id = infile.split(".")[-3]
                else:
                    unique_job_id = indir.split("/")[-1] if self.args.type == 'online' else re.search(r'(LLPSimulation.*?\.i3(?:\.gz)?)$', infile).group(1)
                job_name = f'{self.VERSION}_{self.file_type_name}_{job_suffix}_{datetime.datetime.now().strftime("%m%d%Y")}'
                job_id = f"{job_name}_{unique_job_id}_{self.args.version}"
                logger.debug(f'JOBID: {job_id}')
                logger.debug(f'JOBNAME: {job_name}')
                dag_file.write(f"JOB {job_id} {self.EXEDIR}/DAGOneJob.submit\n")
                dag_file.write(f'VARS {job_id} JOBNAME="{job_name}" SUBDIR="{sub_dir}" GCD_FILE="{self.GCD_PATH}" INFILE="{input_file}" BASENAME="{basename}"\n')
                counter += 1
            if self.args.fast and counter >= 5:
                break

    def process_files(self, SAMPLE_TYPES, job_suffix):
        logger.info("Processing files...")
        logger.info(f'JOB_SUFFIX SELECTED: {job_suffix}\n')
        self.set_dirs(exedir_only=True)
        if self.args.withbkg:
            logger.info(f'Processing CORSIKA files...')
            self.process_single_dir(self.BKG_TOP, job_suffix)
        else:
            logger.info(f'SAMPLE_TYPES SELECTED: {SAMPLE_TYPES}\n')
            with open(f"{self.EXEDIR}/myJobs.dag", "w") as dag_file:
                for sample_type in SAMPLE_TYPES:
                    self.process_sample_type(sample_type, job_suffix, dag_file)
        os.system(f". SubmitDag.sh {self.EXEDIR}")

    def process_sample_type(self, sample_type, job_suffix, dag_file):
        logger.info(f'Processing sample type: {sample_type}')
        dir_paths = glob.glob(f"{self.SIG_TOP}{sample_type}")
        self.file_type_name = self.alter_name(sample_type)
        self.set_dirs()
        os.system(f'. builddag.sh {self.OUTPUTDIR} {self.LOGDIR} {self.ERRORDIR} {self.EXEDIR} {self.PROCESS}')
        counter = 0
        for dir_path in dir_paths:
            self.process_directory(dir_path, job_suffix, dag_file, counter)

    def process_directory(self, dir_path, job_suffix, dag_file, counter):
        sub_dir = os.path.basename(dir_path)
        logger.debug(f'Directory path: {dir_path}')
        logger.debug(f'Setting sub-directory: {sub_dir}')
        self.make_sub_dirs(sub_dir)
        if self.args.type == 'online':
            for indir, dirnames, filenames in os.walk(dir_path):
                logger.debug(f'Processing directory for online preprocessing: {indir}')
                self.write_dag(counter, filenames, job_suffix, dag_file, indir, sub_dir)
        else:
            filenames = os.listdir(dir_path)
            if not filenames:
                logger.warning(f'Directory empty, skipping: {dir_path}')
                return
            logger.debug(f'Processing directory for {job_suffix}: {dir_path}')
            logger.debug(f'Files in directory: {filenames}')
            self.write_dag(counter, filenames, job_suffix, dag_file, dir_path, sub_dir)

    def process_single_dir(self, dir_path, job_suffix):
        logger.info(f'Processing single directory: {dir_path}')
        self.set_dirs(exedir_only=True)
        with open(f"{self.EXEDIR}/myJobs.dag", "w") as dag_file:
            sub_dir = os.path.basename(dir_path)
            self.file_type_name = self.alter_name("CORSIKA")
            self.set_dirs()
            os.system(f'. builddag.sh {self.OUTPUTDIR} {self.LOGDIR} {self.ERRORDIR} {self.EXEDIR} {self.PROCESS}')
            self.make_sub_dirs(sub_dir)
            filenames = os.listdir(dir_path)
            if not filenames:
                logger.warning(f'Directory empty, skipping: {dir_path}')
                return
            self.write_dag(0, filenames, job_suffix, dag_file, dir_path, sub_dir)

    def process_online_files(self):
        self.process_files(self.SAMPLE_TYPES, 'online_preprocess')

    def process_offline_files(self):
        self.process_files(self.SAMPLE_TYPES, 'offline_preprocess')

    def reco_and_clean_files(self):
        self.process_files(self.SAMPLE_TYPES, 'recoAndClean_preprocess')

if __name__ == "__main__":
    # Create an instance of the CondorFilter class
    dag_proc = CondorFilter(args)
    # Call the process_files method
    dag_proc.process_online_files()
    dag_proc.process_offline_files()
    dag_proc.reco_and_clean_files()
    # Example of processing a single directory
