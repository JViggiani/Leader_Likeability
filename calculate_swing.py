# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 15:13:09 2020

@author: Josh
"""

#Python script to take the base scenario and translate it using input for overall vote share

import configparser
#import pandas
import csv
import time
import logging
import os
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
def validate_party_power_dict(constituency_party_power_dict):
    sum_constituencies = 0
    party_count_dict = dict.fromkeys(party for party in Party)
    for constituency in constituency_party_power_dict:
        sum_constituencies += 1
        for party in constituency_party_power_dict[constituency]:
            if party_count_dict[party] is None:
                party_count_dict[party] = constituency_party_power_dict[constituency][party]
            else:
                party_count_dict[party] += constituency_party_power_dict[constituency][party]
    for party in party_count_dict:
        if party == Party.OTHER or party == Party.UNKNOWN or party == Party.DK:
            continue
        if not isclose((party_count_dict[party] / sum_constituencies), 1):
            if party == Party.CON or party == party.LAB or party == Party.LD: #JOSH remove me!
                raise Exception("Bad averaging. Party power dict not verified. Party power for party " + party.name + " is " + str(party_count_dict[party] / sum_constituencies) + " but it should be 1")    
    logging.info("Party power dictionary validated.")
    
def validate_constituency_power_dict(constituency_power_dict):
    sum_powers = 0
    for constituency in constituency_power_dict:
        sum_powers += constituency_power_dict[constituency]
        
    if not isclose(sum_powers, 1):
        raise Exception("Bad averaging. Constutuency power dict not verified. Average power found to be " + str(sum_powers / len(constituency_power_dict)) + " but it should be 1")    
    logging.info("Constituency power dictionary validated.")

def validate_input_vote_shares(row):
    vote_share_sum = 0
    for party in Party:
        #This is the sum of party power for our region
        if party == Party.OTHER or party == Party.DK or party == Party.UNKNOWN:
            continue    #todo implement OTHER parties
        if not row[party.name.lower() + "_share_2024"]:
            continue
        vote_share_sum += float(row[party.name.lower() + "_share_2024"])
    #if not isclose(vote_share_sum, 1):
        #raise Exception("Input data is not normalised. Vote shares do not sum to 1")

def validate_adjusted_vote_shares(adjusted_vote_shares):
    for constituency in adjusted_vote_shares:
        sum_constituency_shares = 0
        for party in adjusted_vote_shares[constituency]:
            if adjusted_vote_shares[constituency][party] is None:
                continue
            sum_constituency_shares += adjusted_vote_shares[constituency][party]
        if not isclose(sum_constituency_shares, 1):
            raise Exception("New vote shares are not normalised for constituency: " + constituency + ". Error!")
            
def validate_adjusted_votes(adjusted_votes, valid_votes):
    sum_votes = 0
    for party in adjusted_votes:
        if adjusted_votes[party] is None:
            continue
        sum_votes += float(adjusted_votes[party])
    if not isclose(sum_votes, int(valid_votes)):
        raise Exception("New vote shares are not normalised for constituency. Error!")
#################################################################################################################################
    
###    SCRIPT
        
log_file_name = "swing.log"
if os.path.exists(log_file_name):
    os.remove(log_file_name)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)

print("Finding constituency sum data")
logging.info("Finding constituency sum data")

base_projection_davey = open(config['Swing_Input']['ElectionProjectionRaw'])
csv_base_projection_davey = csv.DictReader(base_projection_davey)

#Build destination filepath name
output_file_name_davey = config['Swing_Output']['ElectionProjection']
if os.path.exists(output_file_name_davey):
    os.remove(output_file_name_davey)

for row in csv_base_projection_davey:
    validate_input_vote_shares(row)
   
base_projection_davey = open(config['Swing_Input']['ElectionProjectionRaw'])
csv_base_projection_davey = csv.DictReader(base_projection_davey)    

sum_constituencies = 0
sum_votes = 0
party_power_sum = dict.fromkeys(party for party in Party)
raw_total_party_votes = dict.fromkeys(party for party in Party)
#raw_constituency_party_votes = {}

for row in csv_base_projection_davey:
    if Region.from_str(row["region_name"]) == Region.NORTHERN_IRELAND:
        continue
    
    sum_constituencies += 1
    
    sum_votes += float(row["valid_votes_2024"])
    
    #raw_constituency_party_votes[row["constituency_name"]] = {}
    
    for party in Party:
        #This is the sum of party power for our region
        if party == Party.OTHER or party == Party.DK or party == Party.UNKNOWN:
            continue    #todo implement OTHER parties
        if not row[party.name.lower() + "_share_2024"]:
            continue
        
        if party_power_sum[party] is None:
            party_power_sum[party] = float(row[party.name.lower() + "_share_2024"])
        else:
            party_power_sum[party] += float(row[party.name.lower() + "_share_2024"])
            
        if raw_total_party_votes[party] is None:
            raw_total_party_votes[party] = float(row[party.name.lower() + "_share_2024"]) * float(row["valid_votes_2024"])
        else:
            raw_total_party_votes[party] += float(row[party.name.lower() + "_share_2024"]) * float(row["valid_votes_2024"])
            
        #raw_constituency_party_votes[row["constituency_name"]][party] = float(row[party.name.lower() + "_share_2024"]) * float(row["valid_votes"])
            
logging.debug(party_power_sum)

leader_con = Leader.JOHNSON
leader_lab = Leader.STARMER
leader_ld = Leader.DAVEY
leader_snp = Leader.STURGEON
leader_pc = Leader.PRICE
leader_brexit = Leader.FARAGE
leader_green = Leader.BARTLEYBERRY

leaders_projection = (leader_con, leader_lab, leader_ld, leader_snp, leader_pc, leader_brexit, leader_green)
constituency_party_power_dict = {}
constituency_power_dict = {}

print("Finding constituency party power data")
logging.info("Finding constituency party power data")

base_projection_davey = open(config['Swing_Input']['ElectionProjectionRaw'])
csv_base_projection_davey = csv.DictReader(base_projection_davey)

for row in csv_base_projection_davey:
    constituency_power_dict[row["constituency_name"]] = float(row["valid_votes_2024"]) / sum_votes
    
    constituency_party_power_dict[row["constituency_name"]] = {}
    for leader in leaders_projection:
        if Leader.get_party(leader) == Party.OTHER or Leader.get_party(leader) == Party.DK or Leader.get_party(leader) == Party.UNKNOWN:
            continue    #todo implement OTHER parties
            
        vote_share = row[Leader.get_party(leader).name.lower() + "_share_2024"]
        if not vote_share or raw_total_party_votes[Leader.get_party(leader)] == 0:
            constituency_party_power_dict[row["constituency_name"]][Leader.get_party(leader)] = 0
        else:
            #print("Vote share: " + str(vote_share))
            #print("Valid votes 2024: " + str(row["valid_votes_2024"]))
            #print("Total party votes: " + str(raw_total_party_votes[Leader.get_party(leader)]))
            #print("Sum constituencies: " + str(sum_constituencies))
            constituency_party_power_dict[row["constituency_name"]][Leader.get_party(leader)] = ((float(vote_share) * float(row["valid_votes_2024"])) / raw_total_party_votes[Leader.get_party(leader)]) * sum_constituencies
        
logging.debug(constituency_party_power_dict)

validate_party_power_dict(constituency_party_power_dict)
validate_constituency_power_dict(constituency_power_dict) 

print("Calculating difference between model and config vote demand")
logging.info("Calculating difference between model and config vote demand")

#Get desired shares and normalise to sum 1
desired_shares_dict = {}
for party in Party:
    if party == Party.OTHER or party == Party.DK or party == Party.UNKNOWN:
        continue
    desired_shares_dict[party] = float(config["Swing_Input"]["Share" + party.name[:1].upper() + party.name[1:]])
    
unnormalised_sum = 0
for party in desired_shares_dict:
    if desired_shares_dict[party] is None:
        continue        
    unnormalised_sum += desired_shares_dict[party]
for party in desired_shares_dict:
    if desired_shares_dict[party] is None:
        continue
    desired_shares_dict[party] = desired_shares_dict[party] / unnormalised_sum 

#print(desired_shares_dict)

vote_shares_differences = dict.fromkeys(party for party in Party)
for party in Party:
    if party == Party.OTHER or party == Party.UNKNOWN or party == Party.DK:
        continue
    desired_shares = desired_shares_dict[party]
    #actual_shares = party_power_sum[party] / sum_constituencies
    actual_shares = 0
    if raw_total_party_votes[party] is not None:
        actual_shares = raw_total_party_votes[party] / sum_votes
    vote_shares_differences[party] = desired_shares - actual_shares
    
    #print("Party: " + party.name)
    #print("Desired shares: " + str(desired_shares))
    #print("Actual shares: " + str(actual_shares))
    #print("Difference: " + str(vote_shares_differences[party]))

logging.debug("Vote share differences:")
logging.debug(vote_shares_differences)

print("Adapting vote shares for vote share compliancy")
logging.info("Adapting vote shares for vote share compliancy")

base_projection_davey = open(config['Swing_Input']['ElectionProjectionRaw'])
csv_base_projection_davey = csv.DictReader(base_projection_davey)

adjusted_votes = {}

for row in csv_base_projection_davey:
    logging.debug("Constituency: " + str(row["constituency_name"]))
    adjusted_votes[row["constituency_name"]] = dict.fromkeys(party for party in Party)
    for party in Party:
        if party == Party.OTHER or party == Party.UNKNOWN or party == Party.DK:
            continue
        offset = (constituency_party_power_dict[row["constituency_name"]][party] * vote_shares_differences[party]) / (sum_constituencies * constituency_power_dict[row["constituency_name"]])
        original_vote = row[party.name.lower() + "_share_2024"]
        if not original_vote:
            original_vote = 0
        #JOSH problems around here
        #if float(original_vote) == 0:
            #adjusted_votes[row["constituency_name"]][party] = 0
        #elif float(original_vote) == -offset:
            #adjusted_votes[row["constituency_name"]][party] = 1
        #else:
        adjusted_votes[row["constituency_name"]][party] = (float(original_vote) + offset) #* int(row["valid_votes"])
#raw_constituency_party_votes[con][party]

logging.debug("Adjusted votes:")
logging.debug(adjusted_votes)

print("Calculating new electorate sizes.")
logging.info("Calculating new electorate sizes.")

base_projection_davey = open(config['Swing_Input']['ElectionProjectionRaw'])
csv_base_projection_davey = csv.DictReader(base_projection_davey)

new_electorate_sizes = {}
for row in csv_base_projection_davey:
    sum_unnormalised_shares = 0
    for party in Party:
        if party == Party.OTHER or party == Party.DK or party == Party.UNKNOWN:
            continue
        sum_unnormalised_shares += adjusted_votes[row["constituency_name"]][party]
    new_electorate = sum_unnormalised_shares * float(row["valid_votes_2024"])
    new_electorate_sizes[row["constituency_name"]] = new_electorate

logging.debug("Adjusted electorate sizes:")
logging.debug(new_electorate_sizes)
    
print("Normalising new shares.")
logging.info("Normalising new shares.")    

for constituency in adjusted_votes:
    #print("Constituency: " + constituency)
    #print(adjusted_votes[constituency])
    unnormalised_sum = 0
    for party in adjusted_votes[constituency]:
        if adjusted_votes[constituency][party] is None:
            continue        
        unnormalised_sum += adjusted_votes[constituency][party]
    for party in adjusted_votes[constituency]:
        if adjusted_votes[constituency][party] is None:
            continue
        #print("Constituency: " + constituency)
        #print("Party: " + party.name)
        #print("Current unnormalised vote: " + str(adjusted_votes[constituency][party]))
        #print("Unnormalised sum: " + str(unnormalised_sum))
        adjusted_votes[constituency][party] = adjusted_votes[constituency][party] / unnormalised_sum
        
logging.debug("Normalised vote shares:")
logging.debug(adjusted_votes)

print("Printing projection to file.")
logging.info("Printing projection to file.")

base_projection_davey = open(config['Swing_Input']['ElectionProjectionRaw'])
csv_base_projection_davey = csv.DictReader(base_projection_davey)

fieldnames = csv_base_projection_davey.fieldnames
targetdata_2024 = open(config["Swing_Output"]["ElectionProjection"], 'w', newline='')
csv_targetdata_2024 = csv.DictWriter(targetdata_2024, fieldnames=fieldnames)
csv_targetdata_2024.writeheader()

for row in csv_base_projection_davey:
    for party in Party:
        if party == Party.UNKNOWN or party == Party.DK:
            continue
        
        if adjusted_votes[row["constituency_name"]][party] is None or isclose(adjusted_votes[row["constituency_name"]][party], 0):
            row[party.name.lower() + "_share_2024"] = 0
        else:
            row[party.name.lower() + "_share_2024"] = adjusted_votes[row["constituency_name"]][party]
    row["valid_votes_2024"] = new_electorate_sizes[row["constituency_name"]]
    
    row["ld_swing_2024"] = calculate_swing_2024(row, Party.LD)
    
    #print(adjusted_votes[row["constituency_name"]].get)
    
    list_of_results_tuples = list(adjusted_votes[row["constituency_name"]].items())
    list_of_results_tuples = [(sub[1], sub[0]) for sub in list_of_results_tuples]
    #print(list_of_results_tuples)
    list_of_results_tuples = sorted(list_of_results_tuples, key=lambda x: x[0] if x[0] != None else 0)
    #print("Sorted:")
    #print(list_of_results_tuples)
    #print("First party: " + list_of_results_tuples[-1][1].name.upper())
    #print("Second party: " + list_of_results_tuples[-2][1].name.upper())
    
    row["first_party_2024"] = list_of_results_tuples[-1][1].name.upper()
    row["second_party_2024"] = list_of_results_tuples[-2][1].name.upper()
    
    row['result'] = row['result'].upper()
    new_result_string = ''
    if row['first_party'] == row['first_party_2024']:
        new_result_string = row['first_party'] + " HOLD"
    else:
        new_result_string = row['first_party_2024'] + " GAIN FROM " + row['first_party']
    row['result_2024'] = new_result_string
    
    if "CHORLEY" in str(row["constituency_name"]).upper():
        row['first_party_2024'] = "SPEAKER"
    #print(row)
    
    csv_targetdata_2024.writerow(row)
    
targetdata_2024.close()

print("Calculation performed in " + str(time.time() - start_time) + " seconds.")
    
logging.shutdown()