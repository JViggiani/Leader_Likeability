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
import json
import jsonpickle
import matplotlib.pyplot as plt
import numpy as np
from political_data import Party, Leader, Region
from political_utility_functions import format_region, to_serializable, get_num, log_nested_dictionary, zero_negatives
from political_functions import calculate_swing_2024

###    GLOBAL ITEMS
start_time = time.time()

config = configparser.ConfigParser()
config.read('config.ini')
###   END GLOBAL ITEMS

###    CONFIG
log_file_name = "correlations.log"
if os.path.exists(log_file_name):
    os.remove(log_file_name)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)
###    END CONFIG

###    FUNCTION DEFINITIONS
def calculate_swing(row, party):
    largest_nonparty_count = 0
    party_count = 0
    for item in row:
        if item.upper() in Party.__members__:
            if item.upper() == Party.LD.name:
                party_count = int(row[item])
            elif int(row[item]) > largest_nonparty_count:
                largest_nonparty_count = int(row[item])
    return (party_count - largest_nonparty_count) / (2 * int(row['valid_votes']))

def normalise_vote_shares(leader_vote_shares):
    #Normalise vote shares
    sum_vote_shares = sum(leader_vote_shares.values())
    if sum_vote_shares == 0:
        raise Exception("No vote shares recorded for this constituency.")
    else:
        #key_max = max(leader_vote_shares.keys(), key=(lambda k: leader_vote_shares[k]))
        #key_min = min(leader_vote_shares.keys(), key=(lambda k: leader_vote_shares[k]))
        
        for leader in leader_vote_shares:
            leader_vote_shares[leader] = float(leader_vote_shares[leader] / sum_vote_shares)
            #leader_vote_shares[leader] = (leader_vote_shares[leader] - leader_vote_shares[key_min]) / (leader_vote_shares[key_max] - leader_vote_shares[key_min])
            
    return leader_vote_shares

def project(config, region_leader_fittings, regional_leader_likeability_votes):
    
    electiondata_2019 = open(config['Correlations_Input']['ElectionResults2019'])
    csv_electiondata_2019 = csv.DictReader(electiondata_2019)
    
    constituency_likeability_conversion_factor = {}
    
    for row in csv_electiondata_2019:
        if format_region(row['country_name']) == Region.NORTHERN_IRELAND.name:
            logging.debug("Skipping Northern Irish seats")
            continue
        
        constituency_likeability_conversion_factor[row["constituency_name"]] = {}
        
        region = Region.from_str(format_region(row["region_name"]))
        
        likeability_model_leader_vote_shares = {}
        
        for leader_2019 in region_leader_fittings[region]:
            if (leader_2019 == Leader.STURGEON and region != Region.SCOTLAND) or (leader_2019 == Leader.PRICE and region != Region.WALES):
                continue
            
            constituency_likeability_conversion_factor[row["constituency_name"]][leader_2019] = 0
    
            m = region_leader_fittings[region][leader_2019][0]
            b = region_leader_fittings[region][leader_2019][1]
    
            implied_vote_share_2024_unnormalised = 0
            if row["constituency_name"] in regional_leader_likeability_votes[Region.from_str(row["region_name"])][leader_2019]:
                likeability_data = regional_leader_likeability_votes[Region.from_str(row["region_name"])][leader_2019][row["constituency_name"]]
                constituency_leader_likeability = likeability_data[0]
                implied_vote_share_2024_unnormalised = (m * constituency_leader_likeability) + b
            likeability_model_leader_vote_shares[leader_2019] = implied_vote_share_2024_unnormalised
                
        likeability_model_leader_vote_shares = normalise_vote_shares(likeability_model_leader_vote_shares)
                
        for leader in constituency_likeability_conversion_factor[row["constituency_name"]]:
            constituency_likeability_conversion_factor[row["constituency_name"]][leader] = (int(row[Leader.get_party(leader).name.lower()]) / int(row["valid_votes"])) - likeability_model_leader_vote_shares[leader] 
    
    return constituency_likeability_conversion_factor

def project_base_scenario_2024(libdem_leader, labour_leader, config, region_leader_fittings, regional_leader_likeability_votes, constituency_offset):
    
    electiondata_2019 = open(config['Correlations_Input']['ElectionResults2019'])
    csv_electiondata_2019 = csv.DictReader(electiondata_2019)
    
    #Build destination filepath name
    base_file_name = config['Correlations_Output']['ElectionProjection'].split('.')
    file_name = base_file_name[0] + "_" + libdem_leader.name + "_" + labour_leader.name + "_base" + '.' + base_file_name[1]
    targetdata_2024 = open(file_name, 'w', newline='')
    
    fieldnames = csv_electiondata_2019.fieldnames
    fieldnames.append('ld_swing_2019')
    fieldnames.append('result_2024')
    fieldnames.append('first_party_2024')
    fieldnames.append('second_party_2024')
    fieldnames.append('valid_votes_2024')
    for party in Party:
        if party == Party.DK or party == Party.UNKNOWN:
            continue
        fieldnames.append(party.name.lower() + '_share_2024')
    fieldnames.append('ld_swing_2024')
    #print(fieldnames)
    csv_targetdata_2024 = csv.DictWriter(targetdata_2024, fieldnames=csv_electiondata_2019.fieldnames)
    csv_targetdata_2024.writeheader()
    
    for row in csv_electiondata_2019:
        if format_region(row['country_name']) == Region.NORTHERN_IRELAND.name:
            logging.debug("Skipping Northern Irish seats")
            continue
        region = Region.from_str(format_region(row["region_name"]))
        
        likeability_model_leader_vote_shares = {}
        
        for leader_2019 in region_leader_fittings[region]:
            if (leader_2019 == Leader.STURGEON and region != Region.SCOTLAND) or (leader_2019 == Leader.PRICE and region != Region.WALES):
                continue
            
            leader_2024 = leader_2019
            if leader_2019 == Leader.SWINSON:
                leader_2024 = libdem_leader
            elif leader_2019 == Leader.CORBYN:
                leader_2024 = labour_leader
    
            m = region_leader_fittings[region][leader_2019][0]
            b = region_leader_fittings[region][leader_2019][1]
    
            implied_vote_share_2024_unnormalised = 0
            if row["constituency_name"] in regional_leader_likeability_votes[Region.from_str(row["region_name"])][leader_2024]:
                likeability_data = regional_leader_likeability_votes[Region.from_str(row["region_name"])][leader_2024][row["constituency_name"]]
                constituency_leader_likeability = likeability_data[0]
                implied_vote_share_2024_unnormalised = (m * constituency_leader_likeability) + b
            likeability_model_leader_vote_shares[leader_2024] = implied_vote_share_2024_unnormalised
                
        new_electorate = sum(likeability_model_leader_vote_shares.values()) * int(row["valid_votes"])
        
        row["valid_votes_2024"] = new_electorate
        
        likeability_model_leader_vote_shares = normalise_vote_shares(likeability_model_leader_vote_shares)    
    
        fixed_model_leader_vote_shares = {}
        
        for leader_2024 in likeability_model_leader_vote_shares:
            leader_2019 = leader_2024
            if leader_2019 == Leader.STARMER:
                leader_2019 = Leader.CORBYN
            if leader_2019 == Leader.MORAN or leader_2019 == Leader.DAVEY:
                leader_2019 = Leader.SWINSON
            fixed_model_leader_vote_shares[leader_2024] = likeability_model_leader_vote_shares[leader_2024] + constituency_offset[row["constituency_name"]][leader_2019]
    
        fixed_model_leader_vote_shares = zero_negatives(fixed_model_leader_vote_shares)
        
        fixed_model_leader_vote_shares = normalise_vote_shares(fixed_model_leader_vote_shares)    
        
        logging.info("Implied vote values for constituency " + row["constituency_name"])
        log_nested_dictionary(fixed_model_leader_vote_shares)
        
        LD_swing_2019 = calculate_swing(row, Party.LD)
        row['ld_swing_2019'] = LD_swing_2019
        
        '''
        fieldnames.append('result_2024')
        fieldnames.append('first_party_2024')
        fieldnames.append('second_party_2024')
        '''
        
        row['first_party_2024'] = Leader.get_party(max(fixed_model_leader_vote_shares, key=fixed_model_leader_vote_shares.get)).name.upper()
        row['first_party'] = row['first_party'].upper()
        
        #sorted_temp_leader_vote_shares = sorted(leader_vote_shares.items(),key=(lambda i: i[1]))
        
        #find second party
        #row['second_party_2024'] = Leader.get_party(Leader.from_str(sorted_temp_leader_vote_shares[-3][0].name.upper())).name.upper()
        
        list_of_results_tuples = list(fixed_model_leader_vote_shares.items())
        list_of_results_tuples = [(sub[1], sub[0]) for sub in list_of_results_tuples] 
        list_of_results_tuples.sort()
        row['second_party_2024'] = Leader.get_party(list_of_results_tuples[-2][1]).name
        
        row['second_party'] = row['second_party'].upper()
        
        row['result'] = row['result'].upper()
        new_result_string = ''
        if row['first_party'] == row['first_party_2024']:
            new_result_string = row['first_party'] + " HOLD"
        else:
            new_result_string = row['first_party_2024'] + " GAIN FROM " + row['first_party']
        row['result_2024'] = new_result_string
        
        for leader_iterator in Leader:
            if (leader_iterator == Leader.STURGEON and region != Region.SCOTLAND) or (leader_iterator == Leader.PRICE and region != Region.WALES):
                continue
            if (leader_iterator == Leader.CORBYN and labour_leader != Leader.CORBYN) or (leader_iterator == Leader.STARMER and labour_leader != Leader.STARMER) or (leader_iterator == Leader.SWINSON and libdem_leader != Leader.SWINSON) or (leader_iterator == Leader.DAVEY and libdem_leader != Leader.DAVEY) or (leader_iterator == Leader.MORAN and libdem_leader != Leader.MORAN):
                #unused leaders, discard
                continue
            elif leader_iterator == Leader.DAVEY and libdem_leader != Leader.DAVEY:
                continue
            elif leader_iterator == Leader.MORAN and libdem_leader != Leader.MORAN:
                continue
            elif leader_iterator == Leader.STARMER and labour_leader != Leader.STARMER:
                continue
            else:
                row[Leader.get_party(leader_iterator).name.lower() + '_share_2024'] = fixed_model_leader_vote_shares[leader_iterator]
        
        row['ld_swing_2024'] = calculate_swing_2024(row, Party.LD)
        
        csv_targetdata_2024.writerow(row)
        
#Here a row is a row of a constituency fromt hr 2019 results
def calculate_constituency_likeability(row, leader, region, region_likeability):        
    constituency_total_likeability = 0
    total_voters_accounted = 0
    for party_voted in Party:
        if party_voted == Party.OTHER or party_voted == Party.DK or party_voted == Party.UNKNOWN:
            continue
        if party_voted == Party.SNP and region != Region.SCOTLAND:
            continue
        if party_voted == Party.PC and region != Region.WALES:
            continue
        likeability_item = region_likeability[region][party_voted][leader]
        if likeability_item[1] == 0:
            continue
        else:
            #logging.debug("Party voted: " + party_voted.name)
            #logging.debug("Likeability item: " + str(likeability_item))
            #logging.debug("Item leader: " + str(leader))
            num_of_party_voters = int(row[party_voted.name.lower()])
            #logging.debug("Num of party voters: " + str(num_of_party_voters))
            total_voters_accounted += num_of_party_voters
            #logging.debug("Average likeability for party voters: " + str((likeability_item[0] / likeability_item[1])))
            constituency_total_likeability += (likeability_item[0] / likeability_item[1]) * num_of_party_voters
        
    average_likeability = constituency_total_likeability / total_voters_accounted
	
    logging.debug("Voters accounted for: " + str(total_voters_accounted) + " out of total: " + row["valid_votes"] + " = " + str((total_voters_accounted/int(row["valid_votes"]))*100) + "%.")
    logging.debug("Average likeability: " + str(average_likeability))
	
    return average_likeability
        
def plot_likeability(x, y, colour, m, b, region, leader, config):
    # Create scatter plot
    plt.scatter(x, y, color=colour)
    
    # Add correlation line
    axes = plt.gca()
    axes.set_xlim([0,10])
    axes.set_ylim([0,1])
    
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
    
###    END FUNCTION DEFINITIONS
    
#################################################################################################################################
    
###    SCRIPT

if not os.path.exists(config['Correlations_Output']['ImageOutputFolder'] + "/"):
    os.makedirs(config['Correlations_Output']['ImageOutputFolder'])
    
#Build destination filepath name
base_file_name = config['Correlations_Output']['ElectionProjection'].split('.')
file_name_davey = base_file_name[0] + "_" + Leader.DAVEY.name + "_" + Leader.STARMER.name + '.' + base_file_name[1]
file_name_moran = base_file_name[0] + "_" + Leader.MORAN.name + "_" + Leader.STARMER.name + '.' + base_file_name[1]
if os.path.exists(file_name_davey):
    os.remove(file_name_davey)
if os.path.exists(file_name_moran):
    os.remove(file_name_moran)

region_likeability_string=''
with open(config['Correlations_Input']['LikeabilityJson'], "r") as in_likeability_json:
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

electiondata_2019 = open(config['Correlations_Input']['ElectionResults2019'])
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
        
        m, b = np.polyfit(x, y, 1)
        region_leader_fittings[region][leader] = [m, b]
        
        if config['Correlations_Output']['PlotLikeabilityCorrelations'].replace(" ", "").lower() == "true":
            plot_likeability(x, y, colour, m, b, region, leader, config)


logging.debug("Constituency projection values dictionary:")
log_nested_dictionary(region_leader_fittings)

logging.info("Beginning constituency 2024 calculations.")

# regional_leader_likeability_votes[region][leader][constituency]
# contains data like #Returns a tuple: (average_likeability, party_to_calculate_for_vote_proportion, winning_party)

constituency_offset = project(config, region_leader_fittings, regional_leader_likeability_votes)

project_base_scenario_2024(Leader.DAVEY, Leader.STARMER, config, region_leader_fittings, regional_leader_likeability_votes, constituency_offset)
project_base_scenario_2024(Leader.MORAN, Leader.STARMER, config, region_leader_fittings, regional_leader_likeability_votes, constituency_offset)

logging.debug("Constituency offset dictionary:")
logging.debug(constituency_offset)

print("Calculation performed in " + str(time.time() - start_time) + " seconds.")

logging.shutdown()