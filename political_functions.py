# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 19:24:27 2020

@author: Josh
"""
import statistics
import logging
from political_data import Party, Region, Leader

def find_wave(row):
    #Need to calculate the latest wave
    for wave in range(19, 0, -1):
        if "wave" + str(wave) in row:
            wavevalue = row["wave" + str(wave)]
            #print("Wave: " + str(wave))
            #print("Wavestring: " + "wave" + str(wave))
            #print("Wavevalue: " + wavevalue)
            if wavevalue != " " and int(wavevalue) == 1:
                return wave
    #If we finish the iterationw ithout finding the latest constituency, we have no wave data and must discard the entry when returning 0
    #print(row)
    return 0

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
            for party_opinion in region_likeability[region][party_voted]:
                sum_weight = sum_weight + region_likeability[region][party_voted][party_opinion][1]
    return sum_weight

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
    