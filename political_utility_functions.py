# -*- coding: utf-8 -*-
"""
Created on Sat Jul  4 00:56:10 2020

@author: Josh
"""

import enum
import logging

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

## This probably shouldn't be used to bluntly get rid of bad voter share projections
    #todo explore how to get rid of it
def zero_negatives(dictionary):
    key_min = min(dictionary.keys(), key=(lambda k: dictionary[k]))
    
    if dictionary[key_min] < 0:
        for item in dictionary:
            dictionary[item] = dictionary[item] + abs(dictionary[key_min])
    return dictionary

def log_nested_dictionary(d, indent=0):
    for key, value in d.items():
        heading = ''
        if isinstance(value, dict):
            heading = str(key.name)
        else:
            heading = str(key)
        logging.info('\t' * indent + heading)
        if isinstance(value, dict):
            log_nested_dictionary(value, indent+1)
        else:
            logging.info('\t' * (indent+1) + str(value))
            
def get_constituency_column_name(row, wave):
    if "pcon" in row:
        return "pcon"
    else:
        #Need to calculate the latest wave
        if "pconW" + str(wave) in row:
            return "pconW" + str(wave)
        else:
            #No constituency data for the provided wave
            raise Exception("Failed to calculate constituency column name")
            
def isclose(a, b, rel_tol=1e-06, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
            

            