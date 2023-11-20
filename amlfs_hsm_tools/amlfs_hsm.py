import os
import logging
import xattr
import time

from .lustreapi_hsm import get_hsm_state, set_hsm_state
from .lfs_blob_client import LFSBlobClient
from .lustre_hsm_constants import HSM_ARCHIVED_STATE, HSM_DIRTY_STATE, HSM_LOST_STATE, HSM_RELEASED_STATE, \
                                HUA_ARCHIVE, HUA_REMOVE, HUA_RELEASE, HUA_RESTORE
from .utilities import get_relative_path
from .lustreapi_hsm import hsm_request

from azure.core.exceptions import ResourceNotFoundError


class AzureManagedLustreHSM:
    """This class contains the basic functionality to wrap liblustreapi for safe AMLFS HSM operations
    """
    def __init__(self) -> None:
        self.client = LFSBlobClient()

    @staticmethod
    def getHSMState(filePath):
        """This function takes as an input a filePath on a Lustre mount point 
        and returns the file status in HSM

        Args:
            filePath (str): file path to check.

        Raises:
            error: if the get state fails, it raises the related error

        Returns:
            (list[str]): The Lustre HSM state of the filePath
        """
        try:
            return get_hsm_state(filePath)
        except Exception as error:
            logging.error('Failed in getting hsm_state correctly. Please check the file status.')
            raise error  

    @staticmethod
    def runHSMAction(action, filePath):
        """Runs a specified HSM action on a file

        Args:
            action (str): Name describing the action according to HSM defined constants
            filePath (str): Name describing the file path of the file on which the action should be triggered

        Returns:
            bool: True if action is successful, False if it fails
        """
        try:
            hsm_request(filePath, action)
            return True
        except Exception as error:
            logging.error('LFS command failed with error {}. '.format(str(error)))
            return False
        
    @staticmethod
    def copyToolPath(filePath):
        """Returns the HSM file path that is written in the UUID attribute.
        This parameter is the path effectively used by copytool for subsequent operations 
        after file archive. If file gets moved or renamed, the copytool will still refer to
        this path for release/restore operations. It is updated if file is marked as dirty.

        Args:
            filePath (str): file path on which the HSM path needs to be determined.

        Returns:
            (str | None): string describing the copytool path or None if not available
        """
        try:
            return xattr.getxattr(filePath, "trusted.lhsm_uuid").decode()
        except OSError:
            return None
    
    def getBlobClient(self, filePath):
        """Returns a blob client pointing to the filepath in the Blob backend.

        Args:
            filePath (str): filePath for which the blob client is requested.

        Returns:
            (LustreBlobClient): Lustre blob client pointing to the target file path
        """
        return self.client.get_blob_client(container=self.client.containerName, blob=filePath)
    
    def callActionAndWaitStatus(self, action, filePath, targetAddStates, targetRemoveStates, interval=1):
        if self.runHSMAction(action, filePath):
            while (targetRemoveStates and any(state in self.getHSMState(filePath) for state in targetRemoveStates)) \
                  or (targetAddStates and not all(state in self.getHSMState(filePath) for state in targetAddStates)):
                time.sleep(interval)

    def fileNeedsArchive(self, filePath):
        """Returns if a file needs archival. This may be for two reasons:
        - File is not archived
        - File is marked as distry and lost

        Args:
            filePath (str): File path of the file on which to perform the HSM action 

        Returns:
            bool: True if ile needs archive, False if file doesn't need archive.
        """
        return (self.isFileDirty(filePath) and self.isFileLost(filePath)) or not self.isFileArchived(filePath)
    
    def isFileOnHSM(self, filePath):
        """Checks on the blob backend if there is a file in the correct position on HSM.

        Args:
            filePath (str): file path on the file system

        Returns:
            bool: describing if file is on the backend
        """
        isFileOnHSM = self.getBlobClient(filePath).exists()
        if isFileOnHSM:
            logging.info('File {} seems to be present on HSM location.'.format(filePath))
        else:
            logging.info('File {} is not on HSM in the expected position.'.format(filePath))
        return isFileOnHSM

    def isFileReleased(self, filePath):
        """Checks if file is releaed

        Args:
            filePath (str): file path on the file system

        Returns:
            bool: describing if the state is released
        """
        fileStatus = self.getHSMState(filePath)
        return HSM_RELEASED_STATE in fileStatus
    
    def isFileArchived(self, filePath):
        """Checks if file is archived

        Args:
            filePath (str): file path on the file system

        Returns:
            bool: describing if the state is archived
        """
        fileStatus = self.getHSMState(filePath)
        return HSM_ARCHIVED_STATE in fileStatus
    
    def isFileDirty(self, filePath):
        """Checks if file is dirty

        Args:
            filePath (str): file path on the file system

        Returns:
            bool: describing if the state is dirty
        """
        fileStatus = self.getHSMState(filePath)
        return HSM_DIRTY_STATE in fileStatus
    
    def isFileLost(self, filePath):
        """Checks if file is lost

        Args:
            filePath (str): file path on the file system

        Returns:
            bool: describing if the state is lost
        """
        fileStatus = self.getHSMState(filePath)
        return HSM_LOST_STATE in fileStatus
    
    def markHSMState(self, state, filePath):
        """Marks a file with a desired HSM state

        Args:
            state (str): String describing a state from HSM constants
            filePath (str): file path on the AMLFS

        Raises:
            error: Raises an error if the state set fails
        """
        try:
            set_hsm_state(filePath, [state], [], 1)
        except Exception as error:
            logging.error('Failed in setting hsm_state correctly. Please check the file status.')
            raise error

    def markLost(self, filePath):
        """Mark file as lost

        Args:
            filePath (str): file path on the file system
        """
        self.markHSMState(HSM_LOST_STATE, filePath)

    def markDirty(self, filePath):
        """Mark file as dirty

        Args:
            filePath (str): file path on the file system
        """
        self.markHSMState(HSM_DIRTY_STATE, filePath)

    def causesOverwriteWithDataLoss(self, filePath):
        """Checks if triggering an archive/release operation on the specific file
        can cause data loss. The logic of this function is that:
        - if file is archived in clean state, it checks if the copytool path exists on blob
        - if file is not archived in clean state, it checks that the official file path is not present
        on blob

        Args:
            filePath (str): file path on the file system
        Returns:
            bool: describing if data loss may happen from an operation
        """
        if self.fileNeedsArchive(filePath):
            HSMTargetPath = get_relative_path(filePath)
        else:
            HSMTargetPath = self.copyToolPath(filePath)
        causesDataLoss = self.isFileOnHSM(HSMTargetPath) and self.fileNeedsArchive(filePath)
        if causesDataLoss:
            logging.error('Writing down data to blob on file {} causes data loss. No action will be made for archive.'.format(filePath))
        return causesDataLoss

    def isFilePathAlignedInHSM(self, filePath):
        """Checks if the relative file path on AMLFS is coincident to the one
        of the copytool

        Args:
            filePath (str): file path on the file system

        Returns:
            bool: describing if the two file paths are aligned
        """
        lustreUUID = self.copyToolPath(filePath)
        isFileAligned = not lustreUUID or lustreUUID == get_relative_path(filePath)
        if isFileAligned:
            logging.info('File {} seems aligned with HSM location.'.format(filePath))
        else:
            logging.error('File {} seems to point to another HSM location {}.'.format(filePath, lustreUUID))
        return isFileAligned

    def isFileHealthyInHSM(self, filePath):
        """Determines health HSM state for archived file on the basis of two criteria, both required:
        - The current file path is aligned with the copytool filepath
        - The current file path has a file in HSM

        Args:
            filePath (str): file path on the file system 

        Returns:
            bool: describing if the file is in an healthy HSM state
        """
        if not self.isFileArchived(filePath):
            logging.info('File {} seems not to be archived. Nothing to check.'.format(filePath))
            return True
        else:
          return self.isFileOnHSM(get_relative_path(filePath)) and self.isFilePathAlignedInHSM(filePath)

    def remove(self, filePath, force=False):
        """Removes a file from the HSM backend. 
        - It checks the status of the file in terms of health, if not healthy it exits (if no force)
        - In case OS Path exists and the file is in proper archive state, trigger HSM remove from standard API
        - If the remove has to be forced, it removes the file directly from Blob. Useful in case file is removed
        from AMLFS without HSM remove.

        Args:
            filePath (str): file path on the file system
            force (bool, optional): If remove should be forced. Defaults to False.

        Raises:
            error: raises error in case file is not in healthy state
        """
        absolutePath = os.path.abspath(filePath)
        try:
            self.check(filePath)
        except Exception as error:
            if force:
                logging.warn('File {} seems not to be anymore on Lustre, continuning since forcing.'.format(absolutePath))
            else:
                raise error
        
        if os.path.exists(filePath) and not self.fileNeedsArchive(filePath):
            if not self.isFileReleased(filePath):
                if self.runHSMAction(HUA_REMOVE, absolutePath):
                    logging.info('File {} successfully removed from HSM backend.'.format(absolutePath))
                else:
                    logging.error('File {} failed to remove from HSM backend.'.format(absolutePath))
                self.markDirty(filePath)
                self.markLost(filePath)
        elif force:
            try:      
                blobClient = self.getBlobClient(get_relative_path(absolutePath))
                blobClient.delete_blob()
            except ResourceNotFoundError as error:
                if force:
                    logging.error('File {} seems not to be anymore on the HSM backend.'.format(absolutePath))
                else:
                    logging.error('File {} seems not to be anymore on the HSM backend even if hsm_state expects it to be there.'.format(filePath))
        else:
            logging.error('Failed in setting hsm_state correctly. Please check the file {} status.'.format(absolutePath))

    def restore(self, filePath, force=False):
        self.runHSMAction(HUA_RESTORE, filePath)

    def release(self, filePath, force=False):
        """Releases a file to the HSM backend. 
        - It checks the status of the file in terms of health, if not healthy it exits
        - if file is already released, it exits
        - If file is not already released, it releases it

        Args:
            filePath (str): file path on the file system
            force (bool, optional): Release is not forced, just keeping for common signature. Defaults to False.
        """
        absolutePath = os.path.abspath(filePath)

        if self.check(absolutePath):
            if self.isFileReleased(absolutePath):
                logging.info('File {} already released.'.format(absolutePath))
            elif self.runHSMAction(HUA_RELEASE, absolutePath):
                logging.info('File {} successfully released.'.format(absolutePath))
            else:
                logging.error('File {} failed to release.'.format(absolutePath))
        else:
            logging.error('File {} cannot be released since it doesn''t exist anymore on HSM.'.format(absolutePath))
    
    def archive(self, filePath, force=False):
        """Archives a file to the HSM backend. 
        - It checks the status of the file in terms of health, if not healthy it exits
        - It archives the file

        Args:
            filePath (str): file path on the file system
            force (bool, optional): Release is not forced, just keeping for common signature. Defaults to False.
        """
        absolutePath = os.path.abspath(filePath)
        if self.check(absolutePath) and not self.causesOverwriteWithDataLoss(filePath):
            if self.runHSMAction(HUA_ARCHIVE, absolutePath):
                logging.info('File {} successfully archived.'.format(absolutePath))
            else:
                logging.error('File {} failed to archive.'.format(absolutePath))
        else:
            logging.error('File {} is not healthy, cannot archive.'.format(absolutePath))
    
    def check(self, filePath, force=False):
        """Checks a file state on the HSM backend. 
        - It checks the status of the file in terms of health
        - If file is not healthy, it tries to recover data from Blob if it has been released
        - It marks it as dirty and lost

        Args:
            filePath (str): file path on the file system
            force (bool, optional): Release is not forced, just keeping for common signature. Defaults to False.

        Return:
            bool: if the file is healthy
        """
        absolutePath = os.path.abspath(filePath)
        if not self.isFileHealthyInHSM(absolutePath) and not self.fileNeedsArchive(filePath):
            logging.error('File {} seems not to be anymore on the HSM backend. Marking as dirty and lost.'.format(absolutePath))
            if self.isFileReleased(filePath):
                logging.error('File {} seems to be released. Trying to restore the content.'.format(absolutePath))
                self.callActionAndWaitStatus(HUA_RESTORE, filePath, [], [HSM_RELEASED_STATE])
            self.markDirty(absolutePath)
            self.markLost(absolutePath)
            return False
        else:
            return True
        