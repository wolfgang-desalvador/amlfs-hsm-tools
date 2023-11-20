import ctypes

from .lustreapi_classes import lu_fid


class hsm_extent(ctypes.Structure):
    _fields_ = [
        ("offset", ctypes.c_ulonglong),
        ("length", ctypes.c_ulonglong),
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
         ("hr_flags", ctypes.c_ulonglong),
         ("hr_itemcount", ctypes.c_uint),
         ("hr_data_len", ctypes.c_uint),
     ]


class hsm_user_item(ctypes.Structure):
        _fields_ = [
          ("hui_fid", lu_fid),
          ("hui_extent", hsm_extent),
        ]


class hsm_user_request(ctypes.Structure):
     _fields_ = [
         ("hur_request", hsm_request),
         ("hur_user_item", hsm_user_item * 1)
     ]

