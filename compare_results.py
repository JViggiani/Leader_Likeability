# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 11:31:24 2020

@author: Josh
"""

import configparser
#import pandas
import csv
import time
import logging
import os
import collections
import numpy as np
from political_data import Party, Leader, Region
from political_utility_functions import log_nested_dictionary, isclose
from political_functions import calculate_swing_2024

###     GLOBAL ITEMS
start_time = time.time()

config = configparser.ConfigParser()
config.read('config.ini')
###    END GLOBAL ITEMS

###    CONFIG

###    END CONFIG

###    FUNCTIONS

###    END FUNCTION DEFINITIONS

#################################################################################################################################
    
###    SCRIPT

log_file_name = "compare.log"
if os.path.exists(log_file_name):
    os.remove(log_file_name)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)

#print("Finding constituency sum data")
#logging.info("Finding constituency sum data")

projection_two = open(config['Compare_Input']['ProjectionTwo'])
csv_projection_two = csv.DictReader(projection_two)

projection_two_name = config['Compare_Input']['NameTwo']

constituency_two_dict = {}

for row in csv_projection_two:
    constituency_two_dict[row["constituency_name"]] = row

projection_one = open(config['Compare_Input']['ProjectionOne'])
csv_projection_one = csv.DictReader(projection_one)

projection_one_name = config['Compare_Input']['NameOne']

fieldnames = ['ons_id', 'ons_region_id', 'constituency_name', 'region_name', 'result_2024_' + projection_one_name, 'first_party_2024_' + projection_one_name, 'second_party_2024_' + projection_one_name, 'result_2024_' + projection_two_name, 'first_party_2024_' + projection_two_name, 'second_party_2024_' + projection_two_name, 'compared_result', 'compared_second']

output = open(config["Compare_Output"]["ComparisonOutput"], 'w', newline='')
csv_output = csv.DictWriter(output, fieldnames=fieldnames)
csv_output.writeheader()

for row_one in csv_projection_one:
    
    new_row = collections.OrderedDict()
    new_row['ons_id'] = row_one['ons_id']
    new_row['ons_region_id'] = row_one['ons_region_id']
    new_row['constituency_name'] = row_one['constituency_name']
    new_row['region_name'] = row_one['region_name']
    
    new_row['result_2024_' + projection_one_name] = row_one['result_2024']
    new_row['first_party_2024_' + projection_one_name] = row_one['first_party_2024']
    new_row['second_party_2024_' + projection_one_name] = row_one['second_party_2024']
    
    new_row['result_2024_' + projection_two_name] = constituency_two_dict[row_one["constituency_name"]]['result_2024']
    new_row['first_party_2024_' + projection_two_name] = constituency_two_dict[row_one["constituency_name"]]['first_party_2024']
    new_row['second_party_2024_' + projection_two_name] = constituency_two_dict[row_one["constituency_name"]]['second_party_2024']
    
    compared_result = ''

    if new_row['first_party_2024_' + projection_one_name] == "LD" and new_row['first_party_2024_' + projection_two_name] == "LD":
        compared_result = "WON BY " + projection_one_name + " AND " + projection_two_name
    elif new_row['first_party_2024_' + projection_one_name] == "LD" and new_row['first_party_2024_' + projection_two_name] != "LD":
        compared_result = "WON BY " + projection_one_name + " ONLY " 
    elif new_row['first_party_2024_' + projection_one_name] != "LD" and new_row['first_party_2024_' + projection_two_name] == "LD":
        compared_result = "WON BY " + projection_two_name + " ONLY "
    else:
        compared_result = "WON BY NEITHER"

    compared_second = ''

    if new_row['second_party_2024_' + projection_one_name] == "LD" and new_row['second_party_2024_' + projection_two_name] == "LD":
        compared_second = "SECOND BY " + projection_one_name + " AND " + projection_two_name
    elif new_row['second_party_2024_' + projection_one_name] == "LD" and new_row['second_party_2024_' + projection_two_name] != "LD":
        compared_second = "SECOND BY " + projection_one_name + " ONLY " 
    elif new_row['second_party_2024_' + projection_one_name] != "LD" and new_row['second_party_2024_' + projection_two_name] == "LD":
        compared_second = "SECOND BY " + projection_two_name + " ONLY "
    else:
        compared_second = "SECOND BY NEITHER"
        
    new_row['compared_result'] = compared_result
    new_row['compared_second'] = compared_second
    
    csv_output.writerow(new_row)
#csv_output.flush()
output.close()
    
print("Calculation performed in " + str(time.time() - start_time) + " seconds.")
    
logging.shutdown()