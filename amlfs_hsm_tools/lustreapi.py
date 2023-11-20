import ctypes
import ctypes.util
import os

from .lustreapi_classes import lu_fid

liblocation = ctypes.util.find_library("lustreapi")
lustre = ctypes.CDLL(liblocation, use_errno=True)


def path2fid(filename):
    """Invokes LustreAPI to get FID from filename

    Args:
        filename (str): the file path on the filesystem

    Raises:
        IOError: the error in case API call fails

    Returns:
        lu_fid: lu_fid object for the file
    """
    lufid = lu_fid()
    err = lustre.llapi_path2fid(
        filename.encode('utf8'),
        ctypes.byref(lufid))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return lufid
    


