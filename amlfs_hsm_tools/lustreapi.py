import ctypes
import ctypes.util
import os

liblocation = ctypes.util.find_library("lustreapi")
lustre = ctypes.CDLL(liblocation, use_errno=True)


class hsm_extent(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_ulong),
        ("length", ctypes.c_ulong),
]


class hsm_state(ctypes.Structure):
    _fields_ = [
        ("hus_states", ctypes.c_uint),
        ("hus_archive_id", ctypes.c_uint),
        ("hus_in_progress_state", ctypes.c_uint),
        ("hus_in_progress_action", ctypes.c_uint),
        ("hus_in_progress_location", hsm_extent),
        ("hus_extended_info", ctypes.c_char),
        ]

class hsm_request(ctypes.Structure):
     _fields_ = [
         ("hr_action", ctypes.c_uint),
         ("hr_archive_id", ctypes.c_uint),
         ("hr_flags", ctypes.c_ulong),
         ("hr_itemcount", ctypes.c_uint),
         ("hr_data_len", ctypes.c_uint),
     ]

class lu_fid(ctypes.Structure):
    _fields_ = [
        ("f_seq", ctypes.c_ulonglong),
        ("f_oid", ctypes.c_uint),
        ("f_ver", ctypes.c_uint),
        ]
    
class hsm_user_item(ctypes.Structure):
        _fields_ = [
          ("hui_fid", lu_fid),
          ("hui_extent", hsm_extent),
        ]


class hsm_user_request(ctypes.Structure):
     _fields_ = [
         ("hur_request", hsm_request),
         ("hur_user_item[0]", hsm_user_item)
     ]


def path2fid(filename):
    lufid = lu_fid()
    err = lustre.llapi_path2fid(
        filename.encode('utf8'),
        ctypes.byref(lufid))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return lufid

lustre.llapi_hsm_state_get.argtypes = [ctypes.c_char_p, ctypes.POINTER(hsm_state)]
lustre.llapi_hsm_state_set.argtypes = [ctypes.c_char_p, ctypes.c_uint,
                                       ctypes.c_uint, ctypes.c_uint]
lustre.llapi_hsm_user_request_alloc.restype = hsm_user_request
lustre.llapi_hsm_request.argtypes = [ctypes.c_char_p, ctypes.POINTER(hsm_user_request)]

llapi_hsm_state_get = lustre.llapi_hsm_state_get
llapi_hsm_state_set = lustre.llapi_hsm_state_set
llapi_hsm_user_request_alloc = lustre.llapi_hsm_user_request_alloc
llapi_hsm_request = lustre.llapi_hsm_request
