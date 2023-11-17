'''
This file contains useful lustre HSM constants
'''

HSM_NONE_STATE = 'NONE'
HSM_EXISTS_STATE = 'EXISTS'
HSM_DIRTY_STATE = 'DIRTY'
HSM_RELEASED_STATE = 'RELEASED'
HSM_ARCHIVED_STATE = 'ARCHIVED'
HSM_NORELEASE_STATE = 'NO_RELEASE'
HSM_NOARCHIVE_STATE = 'NO_ARCHIVE'
HSM_LOST_STATE = 'LOST'

HUA_NONE = "HUA_NONE"
HUA_ARCHIVE = "HUA_ARCHIVE"
HUA_RESTORE = "HUA_RESTORE"
HUA_RELEASE = "HUA_RELEASE"
HUA_REMOVE  = "HUA_REMOVE"
HUA_CANCEL = "HUA_CANCEL"


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

HSM_ACTION_MAP = {
    HUA_NONE:   1, 
	HUA_ARCHIVE: 10, 
	HUA_RESTORE:  11, 
	HUA_RELEASE:  12, 
	HUA_REMOVE:  13,  
	HUA_CANCEL:  14 
}

