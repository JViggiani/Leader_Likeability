# -*- coding: utf-8 -*-
"""
Created on Sat Jul  4 00:56:10 2020

@author: Josh
"""

import enum

def format_region(region_name):
    if region_name.strip().upper() == "EASTERN":
        return "EAST"
    return region_name.strip().upper().replace(" ","_")

def format_constituency(constituency_name):
    return constituency_name.strip().replace('"', '').replace(",", "").replace(" ", "_").upper()

def format_party(party_name):
    return party_name.upper()

def to_serializable(val):
    """JSON serializer for objects not serializable by default"""

    if isinstance(val, enum.Enum):
        return val.value
    elif hasattr(val, '__dict__'):
        return val.__dict__

    return val

def get_num(x):
    return int(''.join(ele for ele in x if ele.isdigit()))