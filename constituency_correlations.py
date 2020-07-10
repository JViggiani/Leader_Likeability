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
import matplotlib.pyplot as plt
import numpy as np
import json
import jsonpickle
from political_data import Party, Leader, Region
from political_functions import log_nested_dictionary, calculate_constituency_likeability, project, project_2024
from political_utility_functions import format_region, to_serializable, get_num

start_time = time.time()

config = configparser.ConfigParser()
config.read('config.ini')

log_file_name = "constituency_correlations.log"
if os.path.exists(log_file_name):
  os.remove(log_file_name)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)

if not os.path.exists(config['OutputDataFiles']['ImageOutputFolder'] + "/"):
    os.makedirs(config['OutputDataFiles']['ImageOutputFolder'])
    
#Build destination filepath name
base_file_name = config['OutputDataFiles']['ElectionProjection'].split('.')
file_name_davey = base_file_name[0] + "_" + Leader.DAVEY.name + "_" + Leader.STARMER.name + '.' + base_file_name[1]
file_name_moran = base_file_name[0] + "_" + Leader.MORAN.name + "_" + Leader.STARMER.name + '.' + base_file_name[1]
if os.path.exists(file_name_davey):
    os.remove(file_name_davey)
if os.path.exists(file_name_moran):
    os.remove(file_name_moran)

region_likeability_string=''
with open(config['InputDataFiles']['LikeabilityJson'], "r") as in_likeability_json:
    region_likeability_string = json.load(in_likeability_json)
region_likeability_str = jsonpickle.decode(region_likeability_string)
region_likeability = {}
for region_str in region_likeability_str:
    region = Region(get_num(region_str))
    region_likeability[region] = {}
    for party_str in region_likeability_str[region_str]:
        party = Party(get_num(party_str))
        region_likeability[region][party] = {}
        for leader_str in region_likeability_str[region_str][party_str]:
            leader = Leader(get_num(leader_str))
            region_likeability[region][party][leader] = region_likeability_str[region_str][party_str][leader_str]
log_nested_dictionary(region_likeability)

electiondata_2019 = open(config['InputDataFiles']['ElectionResults2019'])
csv_electiondata_2019 = csv.DictReader(electiondata_2019)

#This will be used to store the constituency's (key) average likeability, party voting share and largest party (key tuple)
regional_leader_likeability_votes = {}
for region_iterator in Region:
    if region_iterator == Region.NORTHERN_IRELAND:
        continue
    regional_leader_likeability_votes[region_iterator] = {}
    for leader_iterator in Leader:
        regional_leader_likeability_votes[region_iterator][leader_iterator] = {}

logging.info("Beginning constituency 2019 calculations.")
for row in csv_electiondata_2019:
    if format_region(row['country_name']) == Region.NORTHERN_IRELAND.name:
        logging.debug("Skipping Northern Irish seats")
        continue
   
    logging.debug("Constituency: " + row["constituency_name"])
    logging.debug("Region: " + row["region_name"])
    
    region = Region.from_str(format_region(row["region_name"]))
    
    '''
    largest_nonparty = 0
    party_to_calculate_for_count = int(row[party_to_calculate_for.name.lower()])
    for item in row:
        if item.upper() in Party.__members__:
            if int(row[item]) > largest_nonparty and str(item) != party_to_calculate_for.name.lower():
                largest_nonparty = int(row[item])
                
    logging.debug("Libdem votes: " + str(party_to_calculate_for_count))
    logging.debug("Largest other votes: " + str(largest_nonparty))
    
    #swing = (party_to_calculate_for_count - largest_nonparty) / (2 * int(row['valid_votes']))
    #row['swing'] = swing
    '''
    
    for leader in Leader:
        if (leader == Leader.STURGEON and region != Region.SCOTLAND) or (leader == Leader.PRICE and region != Region.WALES):
            continue
        
        party_to_calculate_for = Leader.get_party(leader)
        party_to_calculate_for_count = int(row[party_to_calculate_for.name.lower()])
            
        if party_to_calculate_for_count == 0:
            #Did not stand in constituency
            continue
        
        #Returns a tuple: (average_likeability, party_to_calculate_for_vote_proportion, winning_party)
        average_likeability = calculate_constituency_likeability(row, leader, region, region_likeability)
        party_to_calculate_for_vote_proportion = int(row[party_to_calculate_for.name.lower()]) / int(row["valid_votes"])
        logging.debug("Party " + str(party_to_calculate_for) + " vote proportion: " + str(party_to_calculate_for_vote_proportion))
        winning_party = Party.from_str(row["first_party"].upper())
        
        regional_leader_likeability_votes[region][leader][row["constituency_name"]] = (average_likeability, party_to_calculate_for_vote_proportion, winning_party)
        
    #csv_targetdata_2024.writerow(row)
    
logging.info("Regional leader likeability with votes per constituency:")
log_nested_dictionary(regional_leader_likeability_votes)

leaders_2019 = [Leader.JOHNSON, Leader.CORBYN, Leader.SWINSON, Leader.STURGEON, Leader.PRICE, Leader.BARTLEYBERRY, Leader.FARAGE]

logging.info("Beginning constituency 2019 plotting.")
#This will be used to store m, b - the fitting coefficients for the 2019 election
region_leader_fittings = {}
for region_iterator in Region:
    if region_iterator == Region.NORTHERN_IRELAND:
        continue
    region_leader_fittings[region_iterator] = {}
    for leader_iterator in leaders_2019:
        if (leader_iterator == Leader.STURGEON and region_iterator != Region.SCOTLAND) or (leader_iterator == Leader.PRICE and region_iterator != Region.WALES):
            continue
        region_leader_fittings[region_iterator][leader_iterator] = [0, 0]

for region in regional_leader_likeability_votes:
    for leader in leaders_2019:
        if (leader == Leader.STURGEON and region != Region.SCOTLAND) or (leader == Leader.PRICE and region != Region.WALES):
            continue
        x = []
        y = []
        colour = []
        for constituency in regional_leader_likeability_votes[region][leader]:
            total_likeability = regional_leader_likeability_votes[region][leader][constituency][0]
            total_weight = regional_leader_likeability_votes[region][leader][constituency][1]
            x.append(total_likeability)
            y.append(total_weight)
               
            colour.append(Party.get_colour_hex(regional_leader_likeability_votes[region][leader][constituency][2]))
    
    #        print("Constituency: " + str(constituency))
    #        print("Likeability (x): " + str(region_likeability_votes[region][constituency][0]))
    #        print("Vote share (y): " + str(region_likeability_votes[region][constituency][1])) 
        #print(str(x))
        #print(str(y))    
    
        # Create scatter plot
        plt.scatter(x, y, color=colour)
    
        # Add correlation line
        axes = plt.gca()
        axes.set_xlim([0,10])
        axes.set_ylim([0,1])
        m, b = np.polyfit(x, y, 1)
        region_leader_fittings[region][leader] = [m, b]
        X_plot = np.linspace(axes.get_xlim()[0],axes.get_xlim()[1],100)
        plt.plot(X_plot, m*X_plot + b, '-')
        plt.title(region.name + " - " + leader.name)
        plt.xlabel("Average Constituency Likeability")
        plt.ylabel("Party " + Leader.get_party(leader).name + " Constituency Vote Share")
        operator = ''
        if b > 0:
            operator = '+ '
        equation = 'y = ' + str(round(m,4)) + 'x ' + operator + str(round(b,4))
        plt.text(0.2, 0.9,equation, horizontalalignment='center',
        verticalalignment='center',
        transform=axes.transAxes)
        plt.savefig(config['OutputDataFiles']['ImageOutputFolder'] + "/" + region.name + "_" + leader.name + ".png")
        plt.show()

logging.debug("Constituency projection values dictionary:")
log_nested_dictionary(region_leader_fittings)

logging.info("Beginning constituency 2024 calculations.")

# regional_leader_likeability_votes[region][leader][constituency]
# contains data like #Returns a tuple: (average_likeability, party_to_calculate_for_vote_proportion, winning_party)

constituency_offset = project(config, region_leader_fittings, regional_leader_likeability_votes)

project_2024(Leader.DAVEY, Leader.STARMER, config, region_leader_fittings, regional_leader_likeability_votes, constituency_offset)
project_2024(Leader.MORAN, Leader.STARMER, config, region_leader_fittings, regional_leader_likeability_votes, constituency_offset)

logging.debug("Constituency offset dictionary:")
logging.debug(constituency_offset)

print("Calculation performed in " + str(time.time() - start_time) + " seconds.")

logging.shutdown()