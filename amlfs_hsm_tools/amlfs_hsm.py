import os
import logging
import subprocess

import xattr

from .lustreapi_hsm import get_hsm_state, set_hsm_state
from .lfs_blob_client import LFSBlobClient
from .lustre_hsm_constants import HSM_ARCHIVED_STATE, HSM_DIRTY_STATE, HSM_EXISTS_STATE, HSM_LOST_STATE, HSM_NOARCHIVE_STATE, \
                                  HSM_NONE_STATE, HSM_NORELEASE_STATE, HSM_RELEASED_STATE
from .utilities import get_relative_path
from azure.core.exceptions import ResourceNotFoundError


class AzureManagedLustreHSM:
    def __init__(self) -> None:
        self.client = LFSBlobClient()

    @staticmethod
    def getHSMState(filePath):
        try:
            return get_hsm_state(filePath)
        except subprocess.CalledProcessError as error:
            logging.error('Failed in getting hsm_state correctly. Please check the file status.')
            raise error  

    def getBlobClient(self, filePath):
        return self.client.get_blob_client(container=self.client.containerName, blob=get_relative_path(filePath))
    
    def isFileOnHSM(self, filePath):
        return self.getBlobClient(filePath).exists()

    def isFileReleased(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return HSM_RELEASED_STATE in fileStatus
    
    def isFileArchived(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return HSM_ARCHIVED_STATE in fileStatus
    
    def isFileDirty(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return HSM_DIRTY_STATE in fileStatus
    
    def isFileLost(self, filePath):
        fileStatus = self.getHSMState(filePath)
        return HSM_LOST_STATE in fileStatus
    
    def markHSMState(self, state, filePath):
        try:
            set_hsm_state(filePath, [state], [], 1)
        except subprocess.CalledProcessError as error:
            logging.error('Failed in setting hsm_state correctly. Please check the file status.')
            raise error

    def markLost(self, filePath):
        self.markHSMState(HSM_LOST_STATE, filePath)

    def markDirty(self, filePath):
        self.markHSMState(HSM_DIRTY_STATE, filePath)

    def checkFileAlignment(self, filePath):
        lustreUUID = xattr.getxattr(get_relative_path(filePath), "trusted.lhsm_uuid")
        return not lustreUUID or lustreUUID == get_relative_path(filePath) 

    def isFileHealthyInHSM(self, absolutePath):
        isFileOnHSM = self.isFileOnHSM(absolutePath) or self.isFileArchived(absolutePath)
        isHSMAligned = self.checkFileAlignment(absolutePath)
        return isFileOnHSM and isHSMAligned

    def remove(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if force or not (self.isFileReleased(absolutePath) or not self.isFileArchived(absolutePath)):
            try:
                if not self.runHSMAction('hsm_remove', absolutePath):
                    blobClient = self.getBlobClient(absolutePath)
                    blobClient.delete_blob()
            except ResourceNotFoundError as error:
                if force:
                    logging.info('File {} seems not to be anymore on the HSM backend.'.format(absolutePath))
                else:
                    logging.error('File {} seems not to be anymore on the HSM backend even if hsm_state expects it to be there.'.format(filePath))
            try:
                self.markDirty(filePath)
                self.markLost(filePath)
            except subprocess.CalledProcessError:
                if force:
                    pass
                else:
                    logging.error('Failed in setting hsm_state correctly. Please check the file {} status.'.format(absolutePath))
        else:
            logging.error('Failed in setting hsm_state correctly. Please check the file {} status.'.format(absolutePath))

    def release(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        self.check(absolutePath)
        if self.isFileArchived and not self.isFileDirty(absolutePath) and not self.isFileLost(absolutePath):
            if self.runHSMAction('hsm_release', absolutePath):
                logging.info('File {} successfully released.'.format(absolutePath))
            else:
                logging.error('File {} failed to release.'.format(absolutePath))
        else:
            logging.error('File {} failed to release since not in archived clean state.'.format(absolutePath))
    
    def archive(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        self.check(absolutePath)
       
        if self.runHSMAction('hsm_archive', absolutePath):
            logging.info('File {} successfully archived.'.format(absolutePath))
        else:
            logging.error('File {} failed to archive.'.format(absolutePath))
    
    def check(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if not self.isFileHealthyInHSM(absolutePath):
            logging.error('File {} seems not to be anymore on the HSM backend. Marking as dirty and lost.'.format(absolutePath))
            self.markDirty(absolutePath)
            self.markLost(absolutePath)
        