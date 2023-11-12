import os
import logging
import subprocess

from .lfs_blob_client import LFSBlobClient
from .utilities import get_relative_path
from azure.core.exceptions import ResourceNotFoundError

class AzureManagedLustreHSM:
    def __init__(self) -> None:
        self.client = LFSBlobClient()

    @staticmethod
    def getHSMState(filePath):
        try:
            fileStatus = str(subprocess.check_output(["lfs", "hsm_state", filePath]))
        except subprocess.CalledProcessError as error:
            logging.error('LFS command failed with error {}. Are you sure you are running the utility on a Lustre mount?'.format(str(error)))
            fileStatus = None

        return fileStatus
    
    @staticmethod
    def runHSMAction(action, filePath):
        try:
            subprocess.check_output(["lfs", action, filePath])
            return True
        except subprocess.CalledProcessError as error:
            logging.error('LFS command failed with error {}. '.format(str(error)))
            return False

    def getBlobClient(self, filePath):
        return self.client.get_blob_client(container=self.client.containerName, blob=get_relative_path(filePath))
    
    def isFileOnHSM(self,filePath):
        return self.getBlobClient(filePath).exists()

    def isFileReleased(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return 'released' in fileStatus
    
    def isFileArchived(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return 'archived' in fileStatus
    
    def isFileDirty(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return 'dirty' in fileStatus
    
    def isFileLost(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return 'lost' in fileStatus
    
    def markHSMState(self, state, filePath):
        try:
            subprocess.check_output(["lfs", "hsm_set", "--{}".format(state), filePath])
        except subprocess.CalledProcessError as error:
            logging.error("Failed in setting hsm_state correctly. Please check the file status.")
            raise error

    def markLost(self, filePath):
        self.markHSMState("lost", filePath)

    def markDirty(self, filePath):
        self.markHSMState("dirty", filePath)

    def remove(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if force or not (self.isFileReleased(absolutePath) or not self.isFileArchived(absolutePath)):
            try:
                blobClient = self.getBlobClient(absolutePath)
                blobClient.delete_blob()
            except ResourceNotFoundError as error:
                self.runHSMAction('hsm_remove', absolutePath)
                if force:
                    logging.info("File {} seems not to be anymore on the HSM backend.".format(absolutePath))
                else:
                    logging.error("File {} seems not to be anymore on the HSM backend even if hsm_state expects it to be there.".format(filePath))
            try:
                self.markDirty(filePath)
                self.markLost(filePath)
            except subprocess.CalledProcessError:
                if force:
                    pass
                else:
                    logging.error("Failed in setting hsm_state correctly. Please check the file {} status.".format(absolutePath))
        else:
            logging.error("Failed in setting hsm_state correctly. Please check the file {} status.".format(absolutePath))

    def release(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if not self.isFileOnHSM(absolutePath):
            logging.info("File {} seems not to be anymore on the HSM backend. Marking as dirty and lost.".format(absolutePath))
            self.markDirty(absolutePath)
            self.markLost(absolutePath)
        elif self.isFileArchived and not self.isFileDirty(absolutePath) and not self.isFileLost(absolutePath):
            if self.runHSMAction('hsm_release', absolutePath):
                logging.info("File {} successfully released.".format(absolutePath))
            else:
                logging.error("File {} failed to release.".format(absolutePath))
    
    def archive(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if not self.isFileOnHSM(absolutePath) and self.isFileArchived(absolutePath):
            logging.error("File {} seems not to be anymore on the HSM backend. Marking as dirty and lost.".format(absolutePath))
            self.markDirty(absolutePath)
            self.markLost(absolutePath)
       
        if self.runHSMAction('hsm_archive', absolutePath):
            logging.info("File {} successfully archived.".format(absolutePath))
        else:
            logging.error("File {} failed to archive.".format(absolutePath))