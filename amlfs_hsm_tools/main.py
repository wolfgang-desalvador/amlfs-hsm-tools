import os
import logging
import argparse

from .amlfs_hsm import AzureManagedLustreHSM

def main():
    parser = argparse.ArgumentParser(prog='Azure Managed Lustre HSM tools', description='This utility helps managing Lustre HSM with Azure Blob Lustre HSM backend.')

    parser.add_argument('action', choices=['release', 'archive', 'remove', 'check'])
    parser.add_argument('-f', '--force', default=False, required=False, action='store_true', help='This forces removal from Blob Storage independently from the HSM status. Use carefully.')     
    parser.add_argument('filenames', nargs='+', type=str)
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args, _ = parser.parse_known_args()
    
    
    logging.basicConfig(format='%(filename)s: '    
                                '%(levelname)s: '
                                '%(funcName)s(): '
                                '%(lineno)d:\t'
                                '%(message)s')
    
    logger = logging.getLogger()
    if args.verbose == 0:
        logger.setLevel(logging.WARN)
    elif args.verbose == 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    file_names = args.filenames
   
    for file in file_names:
        logger.info('Processing file {}'.format(file))
        if os.path.isdir(file):
            logger.warn('HSM operates on files, not on folders. The input path refers to a folder. {} will be skipped.'.format(file))
        elif os.path.exists(file):
            azureManagedLustreHSM = AzureManagedLustreHSM()
            getattr(azureManagedLustreHSM, args.action)(file, args.force)
        else:
            logger.warn('The file provided does not exist on the system. {} will be skipped.'.format(file))


if __name__ == '__main__':
    main()