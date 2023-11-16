import ctypes
import ctypes.util
import os



liblocation = ctypes.util.find_library("lustreapi")
# See if liblustreapi.so is in the same directory as the module
if not liblocation:
    modlocation, module = os.path.split(__file__)
    liblocation = os.path.join(modlocation, "liblustreapi.so")

lustre = ctypes.CDLL(liblocation, use_errno=True)


HSM_NONE_STATE = 'NONE'
HSM_EXISTS_STATE = 'EXISTS'
HSM_DIRTY_STATE = 'DIRTY'
HSM_RELEASED_STATE = 'RELEASED'
HSM_ARCHIVED_STATE = 'ARCHIVED'
HSM_NORELEASE_STATE = 'NO_RELEASE'
HSM_NOARCHIVE_STATE = 'NO_ARCHIVE'
HSM_LOST_STATE = 'LOST'


HSM_STATE_MAP = {
    HSM_NONE_STATE: '0x00000000',
    HSM_EXISTS_STATE: '0x00000001',
    HSM_DIRTY_STATE: '0x00000002',
    HSM_RELEASED_STATE: '0x00000004',
    HSM_ARCHIVED_STATE: '0x00000008',
    HSM_NORELEASE_STATE: '0x00000010',
    HSM_NOARCHIVE_STATE: '0x00000020',
    HSM_LOST_STATE:  '0x00000040'
}

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



class hsm_state(ctypes.Structure):
    _fields_ = [
        ("hus_states", ctypes.c_uint),
        ("hus_archive_id", ctypes.c_uint),
        ]


lustre.llapi_hsm_state_get.argtypes = [ctypes.c_char_p, hsm_state]
lustre.llapi_hsm_state_set.argtypes = [ctypes.c_char_p, ctypes.c_uint,
                                       ctypes.c_uint, ctypes.c_uint]

def get_hsm_state(filename):
    state = hsm_state()
    err = lustre.llapi_hsm_state_get(
        filename.encode('utf8'),
        ctypes.byref(hsm_state))
    if err < 0:
        err = 0 - err
        raise IOError(err, os.strerror(err))
    return hsm_states_list_from_status_flag(int(state.hus_states))
