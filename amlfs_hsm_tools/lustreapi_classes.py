import ctypes


class lu_fid(ctypes.Structure):
    _fields_ = [
        ("f_seq", ctypes.c_ulonglong),
        ("f_oid", ctypes.c_uint),
        ("f_ver", ctypes.c_uint),
        ]
