import ctypes
import ctypes.util
import os

from .lustre_hsm_constants import HSM_STATE_MAP

from .lustre_api import llapi_hsm_state_get, llapi_hsm_state_set, hsm_state


def hsm_states_list_from_status_flag(status_flag):
    '''
    Returns an HSM state list from a status flag
    '''
    return [state for state in HSM_STATE_MAP if status_flag & int(HSM_STATE_MAP[state], 16)]


def hsm_flag_from_state(state):
    '''
    Returns an HSM state from a flag
    '''
    return HSM_STATE_MAP[state]


def get_hsm_state(filename):
    state = hsm_state()
    err = llapi_hsm_state_get(
        filename.encode(), ctypes.byref(state))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return hsm_states_list_from_status_flag(int(state.hus_states))