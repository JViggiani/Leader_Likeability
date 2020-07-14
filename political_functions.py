# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 19:24:27 2020

@author: Josh
"""

import numpy as np

from political_data import Party, Region, Leader
from political_utility_functions import format_region, zero_negatives

def calculate_swing_2024(row, party):
    largest_nonparty_count = 0
    party_count = 0
    for item in row:
        if item.upper() in Party.__members__:
            continue
        elif item.replace("_share_2024", "").upper() in Party.__members__:
            if item.replace("_share_2024", "").upper() == Party.LD.name:
                party_count = float(row[item])
            elif type(row[item]) == float and row[item] > largest_nonparty_count:
                largest_nonparty_count = row[item]
    return (party_count - largest_nonparty_count) / 2

            






            
#Here a row is a row of a constituency fromt hr 2019 results



    


        
