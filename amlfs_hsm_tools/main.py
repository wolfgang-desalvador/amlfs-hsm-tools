import os
import logging
import argparse

from .amlfs_hsm import AzureManagedLustreHSM

def main():
    parser = argparse.ArgumentParser(prog='Azure Managed Lustre HSM tools', description='This utility helps managing Lustre HSM with Azure Blob Lustre HSM backend.')

    parser.add_argument('action', choices=['release', 'archive', 'remove', 'check'])
    parser.add_argument('-f', '--force', default=False, required=False, action='store_true', help='This forces removal from Blob Storage independently from the HSM status. Use carefully.')     
    parser.add_argument('filenames', nargs='+', type=str)
    args, extras = parser.parse_known_args()
    
    logger = logging.getLogger()

    file_names = args.filenames
   
    for file in file_names:
        logger.info('Processing file {}'.format(file))
        if os.path.isdir(file):
            logger.error('HSM operates on files, not on folders. The input path refers to a folder. {} will be skipped.'.format(file))
        elif os.path.exists(file):
            azureManagedLustreHSM = AzureManagedLustreHSM()
            getattr(azureManagedLustreHSM, args.action)(file, args.force)
        else:
            logger.error('The file provided does not exist on the system. {} will be skipped.'.format(file))


if __name__ == '__main__':
    main()