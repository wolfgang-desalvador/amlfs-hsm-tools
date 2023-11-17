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

    @staticmethod
    def runHSMAction(action, filePath):
        try:
            subprocess.check_output(['lfs', action, filePath])
            return True
        except subprocess.CalledProcessError as error:
            logging.error('LFS command failed with error {}. '.format(str(error)))
            return False
        
    @staticmethod
    def getHSMPath(filePath):
        try:
            return xattr.getxattr(filePath, "trusted.lhsm_uuid").decode()
        except OSError:
            return None
    
    def getBlobClient(self, filePath):
        return self.client.get_blob_client(container=self.client.containerName, blob=get_relative_path(filePath))
    
    def isFileOnHSM(self, filePath):
        ifFileOnHSM = self.getBlobClient(filePath).exists()
        logging.info('File {} seems to be present on HSM location.'.format(filePath))
        return ifFileOnHSM

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

    def causesOverwriteWithDataLoss(self, filePath):
        HSMTargetPath = self.getHSMPath(filePath) or get_relative_path(filePath)
        causesDataLoss = self.isFileOnHSM(HSMTargetPath) and not self.isFileArchived(filePath)
        logging.warn('Writing down data to blob on file {} causes data loss. No action will be mode for archive.'.format(filePath))
        return causesDataLoss

    def checkFileAlignment(self, filePath):
        lustreUUID = self.getHSMPath()
        isFileAligned = not lustreUUID or lustreUUID == get_relative_path(filePath) 
        logging.info('File {} seems aligned with HSM location.'.format(filePath))
        return isFileAligned

    def isFileHealthyInHSM(self, filePath):
        if not self.isFileArchived(filePath):
            logging.info('File {} seems not to be archived. Nothing to check.'.format(filePath))
            return True
        else:
          return self.isFileOnHSM(filePath) and self.checkFileAlignment(filePath)

    def remove(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        try:
            self.check(filePath)
        except Exception as error:
            if force:
                logging.warn('File {} seems not to be anymore on Lustre, continuning since forcing.'.format(absolutePath))
            else:
                raise error
        
        if os.path.exists(filePath):
            if not (self.isFileReleased(filePath) or self.isFileDirty(filePath) or self.isFileLost(filePath)):
                if self.runHSMAction('hsm_remove', absolutePath):
                    logging.info('File {} successfully removed from HSM backend.'.format(absolutePath))
                else:
                    logging.error('File {} failed to remove from HSM backend.'.format(absolutePath))
        elif force:
            try:      
                blobClient = self.getBlobClient(absolutePath)
                blobClient.delete_blob()
            except ResourceNotFoundError as error:
                if force:
                    logging.warn('File {} seems not to be anymore on the HSM backend.'.format(absolutePath))
                else:
                    logging.warn('File {} seems not to be anymore on the HSM backend even if hsm_state expects it to be there.'.format(filePath))
        else:
            logging.error('Failed in setting hsm_state correctly. Please check the file {} status.'.format(absolutePath))

    def release(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)

        if self.check(absolutePath):
            if self.isFileReleased(absolutePath):
                logging.info('File {} already released.'.format(absolutePath))
            elif self.runHSMAction('hsm_release', absolutePath):
                logging.info('File {} successfully released.'.format(absolutePath))
            else:
                logging.error('File {} failed to release.'.format(absolutePath))
        else:
            logging.error('File {} cannot be released since it doesn''t exist anymore on HSM.'.format(absolutePath))
    
    def archive(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if self.check(absolutePath) and not self.causesOverwriteWithDataLoss(filePath):
            if self.runHSMAction('hsm_archive', absolutePath):
                logging.info('File {} successfully archived.'.format(absolutePath))
            else:
                logging.error('File {} failed to archive.'.format(absolutePath))
    
    def check(self, filePath, force=False):
        absolutePath = os.path.abspath(filePath)
        if not self.isFileHealthyInHSM(absolutePath):
            logging.warn('File {} seems not to be anymore on the HSM backend. Marking as dirty and lost.'.format(absolutePath))
            self.markDirty(absolutePath)
            self.markLost(absolutePath)

        return True
        