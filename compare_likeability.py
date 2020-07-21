# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 16:25:44 2020

@author: Josh
"""

import configparser
#import pandas
import csv
import time
import logging
import os
from political_data import Party, Leader, Region
from political_functions import calculate_swing

###    GLOBAL ITEMS
start_time = time.time()

config = configparser.ConfigParser()
config.read('config.ini')
###   END GLOBAL ITEMS

###    CONFIG
log_file_name = "compare_likeability.log"
if os.path.exists(log_file_name):
    os.remove(log_file_name)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
###    END CONFIG

###    FUNCTION DEFINITIONS

    
###    END FUNCTION DEFINITIONS
    
#################################################################################################################################
    
###    SCRIPT
    
#Build destination filepath name
base_file_name = config['CompareLikeability_Output']['ComparisonOutput']
if os.path.exists(base_file_name):
    os.remove(base_file_name)

compared_likeability = open(config['CompareLikeability_Input']['Likeability'])
csv_compared_likeability = csv.DictReader(compared_likeability)

leader_1 = Leader.from_str(config['CompareLikeability_Input']['NameOne'])
leader_2 = Leader.from_str(config['CompareLikeability_Input']['NameTwo'])

# Must find the maximum likeability in order to be able to normalise the figures
maximum_likeability = 0

leader_likeability = {}

for row in csv_compared_likeability:
    leader_likeability[row["constituency_name"]] = {}
    
    for leader in leader_1, leader_2:
        leader_likeability[row["constituency_name"]][leader] = float(row[leader.name + "_likeability"])
        
        if float(row[leader.name + "_likeability"]) > maximum_likeability:
            maximum_likeability = float(row[leader.name + "_likeability"])
            
for constituency in leader_likeability:
    for leader in leader_likeability[constituency]:
        leader_likeability[constituency][leader] = leader_likeability[constituency][leader] / maximum_likeability
        
compared_likeability = open(config['CompareLikeability_Input']['Likeability'])
csv_compared_likeability = csv.DictReader(compared_likeability)

output = open(config["CompareLikeability_Output"]["ComparisonOutput"], 'w', newline='')
fieldnames = csv_compared_likeability.fieldnames
fieldnames.append("ld_swing_2019")
fieldnames.append("relative_likeability")
csv_output = csv.DictWriter(output, fieldnames=fieldnames)
csv_output.writeheader()

for row in csv_compared_likeability:
    row["relative_likeability"] = leader_likeability[row["constituency_name"]][leader_1] - leader_likeability[row["constituency_name"]][leader_2]
    row["ld_swing_2019"] = calculate_swing(row, Party.LD)
    csv_output.writerow(row)
output.close()

print("Calculation performed in " + str(time.time() - start_time) + " seconds.")

logging.shutdown()