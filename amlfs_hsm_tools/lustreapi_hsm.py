import ctypes
import os

from .lustre_hsm_constants import HSM_STATE_MAP, HSM_ACTION_MAP

from .lustreapi import lustre, path2fid
from .lustre_hsm_classes import hsm_state, hsm_user_request


lustre.llapi_hsm_state_get.argtypes = [ctypes.c_char_p, ctypes.POINTER(hsm_state)]
lustre.llapi_hsm_state_set.argtypes = [ctypes.c_char_p, ctypes.c_uint,
                                       ctypes.c_uint, ctypes.c_uint]
lustre.llapi_hsm_user_request_alloc.restype = hsm_user_request
lustre.llapi_hsm_request.argtypes = [ctypes.c_char_p, ctypes.POINTER(hsm_user_request)]


llapi_hsm_state_get = lustre.llapi_hsm_state_get
llapi_hsm_state_set = lustre.llapi_hsm_state_set
llapi_hsm_user_request_alloc = lustre.llapi_hsm_user_request_alloc
llapi_hsm_request = lustre.llapi_hsm_request


def hsm_states_list_from_status_flag(status_flag):
    '''
    Returns an HSM state list from a status flag
    '''
    return [state for state in HSM_STATE_MAP if status_flag & int(HSM_STATE_MAP[state], 16)]


def hsm_flags_from_states_list(status_list):
    '''
    Returns an HSM state from a flag
    '''
    return sum(int(HSM_STATE_MAP[state], 16) for state in HSM_STATE_MAP if state in status_list)


def get_hsm_state(filename):
    state = hsm_state()
    err = llapi_hsm_state_get(
        filename.encode(), ctypes.byref(state))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return hsm_states_list_from_status_flag(int(state.hus_states))


def set_hsm_state(filename, setmask, clearmask, archive_id):
    err = llapi_hsm_state_set(
        filename.encode('utf8'),
        hsm_flags_from_states_list(setmask),
        hsm_flags_from_states_list(clearmask),
        archive_id)
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    

def hsm_request(filePath, action):

    hsm_user_request = llapi_hsm_user_request_alloc(1, 1)
    hsm_user_request.hur_request.hr_action = HSM_ACTION_MAP[action]
    hsm_user_request.hur_request.hr_archive_id = 0
    hsm_user_request.hur_request.hr_archive_id = 0

    hsm_user_request.hur_user_item[0].hui_fid = path2fid(filePath)
    hsm_user_request.hur_user_item[0].hui_extent.offset = 0
    #hsm_user_request.hur_user_item[0].hui_extent.length = ctypes.-1LL;

    hsm_user_request.hur_request.hr_itemcount = 1
    hsm_user_request.hur_request.hr_data_len = 1

    err = llapi_hsm_request(filePath.encode('utf-8'), ctypes.byref(hsm_user_request))

    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    
