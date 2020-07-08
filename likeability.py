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
import yaml
import matplotlib.pyplot as plt
import statsmodels.api as sm
import numpy as np
import pylab
import pandas as pd
import json
import jsonpickle
from sklearn.linear_model import LinearRegression
from political_data import Party, Leader, Region
from political_functions import get_likeability_data_of_leader, get_constituency_column_name, find_wave, calculate_sum_weight, log_nested_dictionary, calculate_constituency_likeability, calculate_swing, calculate_swing_2024, project
from political_utility_functions import format_constituency, format_region, to_serializable, get_num

start_time = time.time()

config = configparser.ConfigParser()
config.read('config.ini')

log_file_name = "likeability.log"
if os.path.exists(log_file_name):
  os.remove(log_file_name)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)

if not os.path.exists(config['OutputDataFiles']['ImageOutputFolder'] + "/"):
    os.makedirs(config['OutputDataFiles']['ImageOutputFolder'])

polling_data_files = config['InputDataFiles']['PollingDataWaves'].split(',')

constituencies = open(config['InputDataFiles']['Constituencies'])
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
    
with open(config['OutputDataFiles']['LikeabilityJson'], "w") as out_likeability_json:
    region_likeability_json = jsonpickle.encode(region_likeability)
    json.dump(region_likeability_json, out_likeability_json)
    
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
                
            if regional_leader_likeability_votes[region][leader][constituency][2] == Party.CON:
                colour.append("#0087dc") #conservative blue
            elif regional_leader_likeability_votes[region][leader][constituency][2] == Party.LAB:
                colour.append("#d50000") #labour red
            elif regional_leader_likeability_votes[region][leader][constituency][2] == Party.LD:
                colour.append("#FDBB30") #libdem orange         
            elif regional_leader_likeability_votes[region][leader][constituency][2] == Party.GREEN:
                colour.append("#008066") #green green
            elif regional_leader_likeability_votes[region][leader][constituency][2] == Party.SNP:
                colour.append("#FFF95D") #snp yellow
            elif regional_leader_likeability_votes[region][leader][constituency][2] == Party.PC:
                colour.append("#3F8428") #plaid green
            else:
                colour.append("0.75") #plaid green
                logging.warning("Unknown party. Will plot a grey point")
    
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

log_nested_dictionary(region_leader_fittings)

logging.info("Beginning constituency 2024 calculations.")

# regional_leader_likeability_votes[region][leader][constituency]
# contains data like #Returns a tuple: (average_likeability, party_to_calculate_for_vote_proportion, winning_party)
#project(Leader.DAVEY, Leader.STARMER, config, region_leader_fittings, regional_leader_likeability_votes)
#project(Leader.MORAN, Leader.STARMER, config, region_leader_fittings, regional_leader_likeability_votes)
project(Leader.SWINSON, Leader.CORBYN, config, region_leader_fittings, regional_leader_likeability_votes)


print("Calculation performed in " + str(time.time() - start_time) + " seconds.")

logging.shutdown()