# FILE: GitCommitter.py

import subprocess
import os
import sys
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GitCommitter:
    @staticmethod
    def buildMessage(zodiac, version, commit_message):
        logger.info(f"Building commit message for {zodiac} version {version}")
        return f"[{zodiac}] Version {version}: {commit_message}"

    @staticmethod
    def commit_changes(commit_message):
        # Create a metadata file with the current run line
        metadata_content = f"Run command: {' '.join(sys.argv)}\nTimestamp: {datetime.now()}"
        logger.info(f"Creating metadata file with run line: {metadata_content}")
        metadata_filename = "runLine.txt"
        with open(metadata_filename, "w") as metadata_file:
            metadata_file.write(metadata_content)

        # Add the metadata file to the staging area
        subprocess.run(["git", "add", metadata_filename], check=True)

        # Commit the changes with the provided commit message
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        logger.info(f"Committed changes with message: {commit_message}")
        # Remove the metadata file from the local directory
        os.remove(metadata_filename)