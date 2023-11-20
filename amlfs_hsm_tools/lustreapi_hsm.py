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
    """Returns a list of status from an hexadecimal HSM status string

    Args:
        status_flag (int): hexadecimal HSM status string

    Returns:
        list[str]: list of status containing HSM constants
    """
    return [state for state in HSM_STATE_MAP if status_flag & int(HSM_STATE_MAP[state], 16)]


def hsm_flags_from_states_list(status_list):
    """Genereates an hexadecimal status code from status list

    Args:
        status_list (list[str]): list of status from HSM constants

    Returns:
        int: hexadecimal status code
    """
    return sum(int(HSM_STATE_MAP[state], 16) for state in HSM_STATE_MAP if state in status_list)


def get_hsm_state(filename):
    """Gets the HSM state of a file from LustreAPI

    Args:
        filename (str): filen path on the file system

    Raises:
        IOError: the error in case API call fails

    Returns:
        str: HSM State from HSM constants
    """
    state = hsm_state()
    err = llapi_hsm_state_get(
        filename.encode(), ctypes.byref(state))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return hsm_states_list_from_status_flag(int(state.hus_states))


def set_hsm_state(filename, setmask, clearmask, archive_id):
    """Performs an HSM set state request using Lustre API

    Args:
        filename (str): filen path on the file system
        setmask (list[str]): list of states to be set from HSM constants
        clearmask (list[str]): list of states to be removed from HSM constants
        archive_id (int): archive id (default to 1)

    Raises:
        IOError: the error in case API call fails
    """
    err = llapi_hsm_state_set(
        filename.encode('utf8'),
        hsm_flags_from_states_list(setmask),
        hsm_flags_from_states_list(clearmask),
        archive_id)
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    

def hsm_request(filePath, action):
    """Performs an HSM request using Lustre API

    Args:
        filePath (str): file path on the file system
        action (str): action name from HSM constants

    Raises:
        IOError: the error in case API call fails
    """
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
    
