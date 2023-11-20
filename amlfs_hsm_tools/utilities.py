import json
import os


def loadConfiguration(file):
    with open(file, 'r') as fid:
        configuration = json.load(fid)
    return configuration

def get_relative_path(path):
    mountPath = os.path.abspath(path)
    while not os.path.ismount(mountPath):
        mountPath = os.path.dirname(mountPath)

    relativePath = os.path.abspath(path).replace(mountPath, '')    

    if relativePath[0] == '/':
        relativePath = relativePath[1:]
    
    return relativePath