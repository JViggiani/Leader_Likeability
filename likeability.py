# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 19:17:33 2020

@author: Josh
"""

import configparser
#import pandas
import csv
import time
import logging
import os
import json
import jsonpickle
import statistics
from political_data import Party, Leader, Region
from political_utility_functions import format_constituency, format_region, log_nested_dictionary

###     GLOBAL ITEMS
start_time = time.time()

config = configparser.ConfigParser()
config.read('config.ini')

###    END GLOBAL ITEMS

###    CONFIG
log_file_name = "likeability.log"
if os.path.exists(log_file_name):
  os.remove(log_file_name)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
###    END CONFIG

###    FUNCTION DEFINITIONS
def get_weight(row):
    weight_column_name = ""
    if "wt" in row:
        weight_column_name = "wt"
    elif "wt_new_W17W18W19" in row:
        weight_column_name = "wt_new_W17W18W19"
    else:
        raise Exception("Failed to find weight column")
    
    weight_string = row[weight_column_name]
    if not weight_string or weight_string == " ":
        logging.debug("Failed to find any weighting data for column: " + weight_column_name + ". Returning 0 weight.")
        return 0
    else:
        if weight_string.startswith("."):
            weight_string = "0" + weight_string
        return float(weight_string)

def get_leader_likeability_column_names(row, leader):
    if leader == Leader.BARTLEYBERRY:
        basic_leader_likeability_column_name_Bartley = "likeBartley"
        basic_leader_likeability_column_name_Berry = "likeBerry"
        if basic_leader_likeability_column_name_Bartley  in row:
            return [basic_leader_likeability_column_name_Bartley, basic_leader_likeability_column_name_Berry]
        else:
            raise Exception("Failed to find column name: " + basic_leader_likeability_column_name_Bartley)
    else:
        basic_leader_likeability_column_name = "like" + leader.name[0].upper() + leader.name[1:].lower()
        if basic_leader_likeability_column_name  in row:
            return [basic_leader_likeability_column_name]
        else:
            raise Exception("Failed to find column name: " + basic_leader_likeability_column_name)

#These rows are those from the polling data, not the results of the 2019 election
def get_likeability_data_of_leader(row, current_likeability_list, leader):
    logging.debug("Entering likeability function")
    weight = get_weight(row)
    logging.debug("Row weight " + str(weight))
    
    this_weighted_likeability = 0
    
    #The below is set up in quite a confusing way because sometimes parties can have multiple leaders. 
    #Strictly we aren't calculating "leader likeability for each leader" but instead "party leadership likeability"
    #   so instead we find the leader(s) of a party, weight the responses and average them to find eg the Green 
    #   party leadership likeability
    leader_column_names = get_leader_likeability_column_names(row, leader)
    logging.debug("Leader likeability column name(s) for leader " + leader.name + " are: " + str(leader_column_names))
    if leader_column_names:
        this_weighted_likeability_leader_list = []
        for leader_column_name in leader_column_names:
            if row[leader_column_name] != " " and int(row[leader_column_name]) >= 0 and int(row[leader_column_name]) <= 10:
                this_weighted_likeability_leader_list.append(weight * int(row[leader_column_name]))
            else:
                logging.debug("Failed to find valid likeability data for column: " + leader_column_name)
        if not this_weighted_likeability_leader_list:
            logging.debug("Failed to find valid likeability data. Returning [0, 0]")
            return [0, 0]
        else:
            logging.debug("Found likeability data. Will assess the average likeability of: " + str(this_weighted_likeability_leader_list))
            this_weighted_likeability = statistics.mean(this_weighted_likeability_leader_list)

    return [this_weighted_likeability, weight]

def calculate_sum_weight(region_likeability):
    sum_weight = 0
    for region in region_likeability:
        for party_voted in region_likeability[region]:
            for leader_opinion in region_likeability[region][party_voted]:
                sum_weight = sum_weight + region_likeability[region][party_voted][leader_opinion][1]
    return sum_weight
###    END FUNCTION DEFINITIONS

#################################################################################################################################
    
###    SCRIPT

polling_data_files = config['Likeability_Input']['PollingDataWaves'].split(',')

constituencies = open(config['Likeability_Input']['Constituencies'])
csv_constituencies = csv.DictReader(constituencies)

print("Initialising constituency reference dictionary")
logging.info("Initialising constituency reference dictionary")
regions_and_constituencies = {}
for row in csv_constituencies:
    regions_and_constituencies[row['Index']] = (format_constituency(row['Constituency']), format_region(row['Region']))

region_likeability = dict.fromkeys([Region.EAST_MIDLANDS, 
                                   Region.EAST, 
                                   Region.LONDON, 
                                   Region.NORTH_EAST, 
                                   Region.NORTH_WEST, 
                                   Region.SCOTLAND, 
                                   Region.SOUTH_EAST, 
                                   Region.SOUTH_WEST, 
                                   Region.WALES, 
                                   Region.WEST_MIDLANDS,
                                   Region.YORKSHIRE_AND_THE_HUMBER])
    
print("Initialising likeability matrix")
logging.info("Initialising likeability matrix")
#This will be used to store a matrix of the likeability polling data, as a regional breakdown of who voted for what party and what their opinions are of various party leaders grouped by the party they voted for. 
for region in region_likeability:
    region_likeability[region] = {}
    for party_voted in Party:
        if party_voted == Party.OTHER or party_voted == Party.DK or party_voted == Party.UNKNOWN:
            continue
        if party_voted == Party.SNP and region != Region.SCOTLAND:
            continue
        if party_voted == Party.PC and region != Region.WALES:
            continue
        region_likeability[region][party_voted] = {}
        for leader_opinion in Leader:
            if Leader.get_party(leader_opinion) == Party.OTHER or Leader.get_party(leader_opinion) == Party.DK or Leader.get_party(leader_opinion) == Party.UNKNOWN:
                continue
            if Leader.get_party(leader_opinion) == Party.SNP and region != Region.SCOTLAND:
                continue
            if Leader.get_party(leader_opinion) == Party.PC and region != Region.WALES:
                continue
            ##The first number represents the sum of all likeabilities, the second represents the sum of responses to this catagory
            region_likeability[region][party_voted][leader_opinion] = [0, 0] 

for polling_data_file in polling_data_files:
    
    polling_data_file = polling_data_file.strip(' ')
    polling_data = open(polling_data_file)
    csv_pollingdata = csv.DictReader(polling_data)
    
    #print(region_likeability)
    print("Beginning likeability parsing")
    logging.info("Beginning likeability parsing")
    for row in csv_pollingdata:

        constituency_column_name = "pcon"
        if row[constituency_column_name] not in regions_and_constituencies or regions_and_constituencies[row[constituency_column_name]][0] == "NOT_IN_A_PARLIAMENTARY_CONSTITUENCY":
            logging.debug("Failed to find constituency key: " + str(row[constituency_column_name]) + ". Discarding.")
            continue
        if row["p_past_vote_2019"] == " " or int(row["p_past_vote_2019"]) not in (e.value for e in Party) or Party(int(row["p_past_vote_2019"])) == Party.UNKNOWN:
            logging.debug("Failed to find party key: " + str(row["p_past_vote_2019"]) + ". Discarding.")
            continue

        region_from_file = Region.from_str(regions_and_constituencies[row[constituency_column_name]][1])
        
        party_leanings = Party.from_party_id(int(row["partyId"])) 
        party_voted_from_file = Party(int(row["p_past_vote_2019"])) 
        
        # For some reason, in wave 19, nobody was recorded to have voted for the Brexit party. 
        # Despite 32,000+ responses in the survey and BXT getting 2% of the vote, nobody could be found?? Strange. 
        # I will instead measure their sentiments by those who said they lean towards them
        if party_leanings == Party.BREXIT:
            party_voted_from_file = party_leanings
        
        if party_voted_from_file not in region_likeability[region_from_file]:
            logging.debug("Party " + str(party_voted_from_file) + " is not active in region " + str(region_from_file)  + ". Discarding.")
            continue    
        
        for leader in Leader:
            if (leader == Leader.STURGEON and region_from_file != Region.SCOTLAND) or (leader == Leader.PRICE and region_from_file != Region.WALES):
                logging.debug("Ignoring opinions of leader " + leader.name + " from someone in region " + region_from_file.name + ". Discarding.")
                continue

            current_region_likeability = get_likeability_data_of_leader(row, region_likeability[region_from_file][party_voted_from_file][leader], leader)
            if current_region_likeability:
                old_region_likeability = region_likeability[region_from_file][party_voted_from_file][leader]
                region_likeability[region_from_file][party_voted_from_file][leader] = [old_region_likeability[i] + current_region_likeability[i] for i in range(len(old_region_likeability))] 
            else:
                raise Exception("Failed to get the current region likeability!")
    
    #print("==End region likeability==")
    #print(region_likeability)
    #sum_weight = calculate_sum_weight(region_likeability)
    #logging.info("Current sum of weight: " + str(sum_weight))

#logging.info("\n" + yaml.dump(region_likeability, default_flow_style=False))
logging.info("Finished likeability parsing. Saving into json")
log_nested_dictionary(region_likeability)
sum_weight = calculate_sum_weight(region_likeability)
logging.info("Sum of weight: " + str(sum_weight))
#with open(config['OutputDataFiles']['LikeabilityJson'], "w") as jsonfile:
#    json.dump(jsonfile, region_likeability, default=to_serializable)
    
#This prints everything to one line. With a complex data structure like this I am not sure how to properly format it. But it does the job in reducing computational time for the next scripts
#   TODO: make me human readable for neatness
with open(config['Likeability_Output']['LikeabilityJson'], "w") as out_likeability_json:
    region_likeability_pickle = jsonpickle.encode(region_likeability)
    json.dump(region_likeability_pickle, out_likeability_json, indent=4, separators=(',', ': '))
    
print("Finished generating likeability json from polling data.")
logging.info("Finished generating likeability json from polling data.")

print("Calculation performed in " + str(time.time() - start_time) + " seconds.")
    
logging.shutdown()