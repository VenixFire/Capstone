"""
Docstring for raspi_src.scpi_util

Jack Chambers
1/28/2026
SCPI Utils

"""


"""
Turns a bool to ON or OFF for SCPI properties
"""
def BOOL_ONOFF(state : bool) -> str:
    if state:
        return "ON"
    else:
        return "OFF"
    

"""
Turns a bool to 1 or 0 for setting a SCPI flag
"""
def BOOL_INT(state : bool) -> int:
    if state:
        return 1
    else:
        return 0
