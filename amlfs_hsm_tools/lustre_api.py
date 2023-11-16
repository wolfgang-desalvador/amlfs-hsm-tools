import ctypes
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
    

lustre.llapi_hsm_state_get.argtypes = [ctypes.c_char_p, ctypes.POINTER(hsm_state)]
lustre.llapi_hsm_state_set.argtypes = [ctypes.c_char_p, ctypes.c_uint,
                                       ctypes.c_uint, ctypes.c_uint]


llapi_hsm_state_get = lustre.llapi_hsm_state_get
llapi_hsm_state_set = lustre.llapi_hsm_state_set