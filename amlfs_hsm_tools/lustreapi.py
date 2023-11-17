import ctypes
import ctypes.util
import os

from .lustreapi_classes import lu_fid

liblocation = ctypes.util.find_library("lustreapi")
lustre = ctypes.CDLL(liblocation, use_errno=True)

def path2fid(filename):
    lufid = lu_fid()
    err = lustre.llapi_path2fid(
        filename.encode('utf8'),
        ctypes.byref(lufid))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return lufid
    


