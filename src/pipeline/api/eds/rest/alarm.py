
"""
Alarm-specific EDS REST API functions copied manually by Clayton on 1 December 2025 from eds.py.
"""
@lru_cache()
def get_stat_alarm_definitions():
    """
    Returns a dictionary where each key is the bitmask integer value from the EDS alarm types,
    and each value is a tuple: (description, quality_code).

    | Quality Flag | Meaning      | Common Interpretation                            |
    | ------------ | ------------ | ------------------------------------------------ |
    | `G`          | Good         | Value is reliable/valid                          |
    | `B`          | Bad          | Value is invalid/unreliable                      |
    | `U`          | Uncertain    | Value may be usable, but not guaranteed accurate |
    | `S`          | Substituted  | Manually entered or filled in                    |
    | `N`          | No Data      | No value available                               |
    | `Q`          | Questionable | Fails some validation                            |

    Source: eDocs/eDocs%203.8.0%20FP3/Index/en/OPH070.pdf

    """
    return {
        1: ("ALMTYPE_RETURN", "G"),
        2: ("ALMTYPE_SENSOR", "B"),
        4: ("ALMTYPE_HIGH", "G"),
        8: ("ALMTYPE_HI_WRS", "G"),
        16: ("ALMTYPE_HI_BET", "G"),
        32: ("ALMTYPE_HI_UDA", "G"),
        64: ("ALMTYPE_HI_WRS_UDA", "G"),
        128: ("ALMTYPE_HI_BET_UDA", "G"),
        256: ("ALMTYPE_LOW", "G"),
        512: ("ALMTYPE_LOW_WRS", "G"),
        1024: ("ALMTYPE_LOW_BET", "G"),
        2048: ("ALMTYPE_LOW_UDA", "G"),
        4096: ("ALMTYPE_LOW_WRS_UDA", "G"),
        8192: ("ALMTYPE_LOW_BET_UDA", "G"),
        16384: ("ALMTYPE_SP_ALM", "B"),
        32768: ("ALMTYPE_TIME_OUT", "U"),
        65536: ("ALMTYPE_SID_ALM", "U"),
        131072: ("ALMTYPE_ALARM", "B"),
        262144: ("ALMTYPE_ST_CHG", "G"),
        524288: ("ALMTYPE_INCR_ALARM", "G"),
        1048576: ("ALMTYPE_HIGH_HIGH", "G"),
        2097152: ("ALMTYPE_LOW_LOW", "G"),
        4194304: ("ALMTYPE_DEVICE", "U"),
    }
def decode_stat(stat_value):
    '''
    Example:
    >>> decode_stat(8192)
    [(8192, 'ALMTYPE_LOW_BET_UDA', 'G')]

    >>> decode_stat(8192 + 2)
    [(2, 'ALMTYPE_SENSOR', 'B'), (8192, 'ALMTYPE_LOW_BET_UDA', 'G')]
    '''
    alarm_dict = get_stat_alarm_definitions()
    active_flags = []
    for bitmask, (description, quality) in alarm_dict.items():
        if stat_value & bitmask:
            active_flags.append((bitmask, description, quality))
    return active_flags