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
from sklearn.linear_model import LinearRegression
from political_data import Party, Leader, Region
from political_functions import get_likeability_data_of_leader, get_constituency_column_name, find_wave, calculate_sum_weight, log_nested_dictionary
from political_utility_functions import format_constituency, format_region

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
        for party_opinion in Party:
            if party_opinion == Party.OTHER or party_opinion == Party.DK or party_opinion == Party.UNKNOWN:
                continue
            if party_opinion == Party.SNP and region != Region.SCOTLAND:
                continue
            if party_opinion == Party.PC and region != Region.WALES:
                continue
            ##The first number represents the sum of all likeabilities, the second represents the sum of responses to this catagory
            region_likeability[region][party_voted][party_opinion] = [0, 0] 

for polling_data_file in polling_data_files:
    
    #print("==Start region likeability==")
    #print(region_likeability)
    
    polling_data_file = polling_data_file.strip(' ')
    polling_data = open(polling_data_file)
    csv_pollingdata = csv.DictReader(polling_data)
    
    #print(region_likeability)
    print("Beginning likeability parsing")
    logging.info("Beginning likeability parsing")
    for row in csv_pollingdata:
        #wave_number = find_wave(row)
        #if not wave_number:
            #Could not determine the wave number to use on this row. Continuing
        #    logging.debug("Failed to determine wave number. Discarding.")
        #    continue
        
        #constituency_column_name = get_constituency_column_name(row, wave_number)
        constituency_column_name = "pcon"
        if row[constituency_column_name] not in regions_and_constituencies or regions_and_constituencies[row[constituency_column_name]][0] == "NOT_IN_A_PARLIAMENTARY_CONSTITUENCY":
            logging.debug("Failed to find constituency key: " + str(row[constituency_column_name]) + ". Discarding.")
            continue
        if row["p_past_vote_2019"] == " " or int(row["p_past_vote_2019"]) not in (e.value for e in Party) or Party(int(row["p_past_vote_2019"])) == Party.UNKNOWN:
            logging.debug("Failed to find party key: " + str(row["p_past_vote_2019"]) + ". Discarding.")
            continue
        #print(regions_and_constituencies[row[constituency_column_name]])
        region_from_file = Region.from_str(regions_and_constituencies[row[constituency_column_name]][1])
        party_voted_from_file = Party(int(row["p_past_vote_2019"])) 
        
        if party_voted_from_file not in region_likeability[region_from_file]:
            logging.debug("Party " + str(party_voted_from_file) + " is not active in region " + str(region_from_file)  + ". Discarding.")
            continue    
        
        for leader in Leader:
            if (leader == Leader.STURGEON and region_from_file != Region.SCOTLAND) or (leader == Leader.PRICE and region_from_file != Region.WALES):
                logging.debug("Ignoring opinions of leader " + leader.name + " from someone in region " + region_from_file.name + ". Discarding.")
                continue
            party = Party(leader.value)
            #print("Region: " + str(region_from_file))
            #print("Party voted: " + str(party_voted_from_file))
            #print("Party opinion: " + str(party))
            #new_region_likeability = get_likeability_data_of_leader(row, region_likeability[region_from_file][party_voted_from_file][party], leader, wave_number)
            logging.info("Old likeability: " + str(region_likeability[region_from_file][party_voted_from_file][party]))
            current_region_likeability = get_likeability_data_of_leader(row, region_likeability[region_from_file][party_voted_from_file][party], leader)
            if current_region_likeability:
                old_region_likeability = region_likeability[region_from_file][party_voted_from_file][party]
                region_likeability[region_from_file][party_voted_from_file][party] = [old_region_likeability[i] + current_region_likeability[i] for i in range(len(old_region_likeability))] 
            else:
                raise Exception("Failed to get the current region likeability!")
            logging.info("New likeability: " + str(region_likeability[region_from_file][party_voted_from_file][party]))
    
    #print("==End region likeability==")
    #print(region_likeability)
    sum_weight = calculate_sum_weight(region_likeability)
    logging.info("Current sum of weight: " + str(sum_weight))
    print("Sum weight: " + str(sum_weight))

#logging.info("\n" + yaml.dump(region_likeability, default_flow_style=False))
log_nested_dictionary(region_likeability)
sum_weight = calculate_sum_weight(region_likeability)
logging.info("Current sum of weight: " + str(sum_weight))

# define separate lists for different regions.. maybe a dictionary ?
# foreach constituency:
#   region_of_constituency = find_region()
#   party_vote_share = find_vote_share(desired_party)
#   constituency_likeability = 0
#   foreach voted party (5 parties):
#       foreach party (approx 5 parties):
#           regional_likeability_average = find_regional_average()
#           constituency_likeability = constituency_likeability + (regional_likeability_average * party_voters)
#           total_voters_accounted = total_voters_accounted + party_voters
#   add (constituency_likeability, party_vote_share) to a regional list of constituencies

electiondata_2019 = open(config['InputDataFiles']['ElectionResults2019'])
csv_electiondata_2019 = csv.DictReader(electiondata_2019)

party_to_calculate_for = Party.LD

region_likeability_votes = dict.fromkeys([Region.EAST_MIDLANDS, 
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
for region in region_likeability_votes:
    region_likeability_votes[region] = {}

logging.info("Beginning constituency calculations.")
for row in csv_electiondata_2019:
    if format_region(row['country_name']) == Region.NORTHERN_IRELAND.name:
        logging.debug("Skipping Northern Irish seats")
        continue
   
    logging.debug("Constituency: " + row["constituency_name"])
    logging.debug("Region: " + row["region_name"])
    
    region = Region.from_str(format_region(row["region_name"]))
    
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
    
    constituency_total_likeability = 0
    total_voters_accounted = 0
    for party_voted in Party:
        if party_voted == Party.OTHER or party_voted == Party.DK or party_voted == Party.UNKNOWN:
            continue
        if party_voted == Party.SNP and region != Region.SCOTLAND:
            continue
        if party_voted == Party.PC and region != Region.WALES:
            continue
        likeability_item = region_likeability[region][party_voted][party_to_calculate_for]
        if likeability_item[1] == 0:
            continue
        else:
            num_of_party_voters = int(row[party_voted.name.lower()])
            total_voters_accounted += num_of_party_voters
            constituency_total_likeability += (likeability_item[0] / likeability_item[1]) * num_of_party_voters
    
    average_likeability = constituency_total_likeability / total_voters_accounted
    party_to_calculate_for_vote_proportion = party_to_calculate_for_count / int(row["valid_votes"])
    winning_party = Party.from_str(row["first_party"].upper())
    region_likeability_votes[region][row["constituency_name"]] = (average_likeability, party_to_calculate_for_vote_proportion, winning_party)
    
    logging.debug("Voters accounted for: " + str(total_voters_accounted) + " out of total: " + row["valid_votes"] + " = " + str((total_voters_accounted/int(row["valid_votes"]))*100) + "%.")
    logging.debug("Average likeability: " + str(average_likeability))
    logging.debug("Party " + str(party_to_calculate_for) + " vote proportion: " + str(party_to_calculate_for_vote_proportion))
    #csv_targetdata_2024.writerow(row)
    
log_nested_dictionary(region_likeability_votes)

for region in region_likeability_votes:
    print("Region: " + str(region))
    x = []
    y = []
    colour = []
    for constituency in region_likeability_votes[region]:
        x.append(region_likeability_votes[region][constituency][0])
        y.append(region_likeability_votes[region][constituency][1])
        
        if region_likeability_votes[region][constituency][2] == Party.CON:
            colour.append("#0087dc") #conservative blue
        elif region_likeability_votes[region][constituency][2] == Party.LAB:
            colour.append("#d50000") #labour red
        elif region_likeability_votes[region][constituency][2] == Party.LD:
            colour.append("#FDBB30") #libdem orange         
        elif region_likeability_votes[region][constituency][2] == Party.GREEN:
            colour.append("#008066") #green green
        elif region_likeability_votes[region][constituency][2] == Party.SNP:
            colour.append("#FFF95D") #snp yellow
        elif region_likeability_votes[region][constituency][2] == Party.PC:
            colour.append("#3F8428") #plaid green
        else:
            colour.append("0.75") #plaid green
            logging.warn("Unknown party. Will plot a grey point")

#        print("Constituency: " + str(constituency))
#        print("Likeability (x): " + str(region_likeability_votes[region][constituency][0]))
#        print("Vote share (y): " + str(region_likeability_votes[region][constituency][1])) 
    #print(str(x))
    #print(str(y))    

    # Create scatter plot
    plt.scatter(x, y, color=colour)

    # Add correlation line
    axes = plt.gca()
    axes.set_xlim([0,5])
    axes.set_ylim([0,0.6])
    m, b = np.polyfit(x, y, 1)
    X_plot = np.linspace(axes.get_xlim()[0],axes.get_xlim()[1],100)
    plt.plot(X_plot, m*X_plot + b, '-')
    plt.title(region.name)
    plt.xlabel("Average Constituency Likeability")
    plt.ylabel("Party " + party_to_calculate_for.name + " Constituency Vote Share")
    operator = ''
    if b > 0:
        operator = '+ '
    equation = 'y = ' + str(round(m,4)) + 'x ' + operator + str(round(b,4))
    plt.text(0.2, 0.9,equation, horizontalalignment='center',
    verticalalignment='center',
    transform=axes.transAxes)
    plt.savefig(config['OutputDataFiles']['ImageOutputFolder'] + "/" + region.name + ".png")
    plt.show()


print("Calculation performed in " + str(time.time() - start_time) + " seconds.")

logging.shutdown()