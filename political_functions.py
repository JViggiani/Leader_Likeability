# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 19:24:27 2020

@author: Josh
"""
import statistics
import logging
import csv
from political_data import Party, Region, Leader
from political_utility_functions import format_region, zero_negatives

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
            
#Here a row is a row of a constituency fromt hr 2019 results
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

def normalise_vote_shares(leader_vote_shares):
    #Normalise vote shares
    sum_vote_shares = sum(leader_vote_shares.values())
    if sum_vote_shares == 0:
        raise Exception("No vote shares recorded for this constituency.")
    else:
        for leader in leader_vote_shares:
            leader_vote_shares[leader] = float(leader_vote_shares[leader] / sum_vote_shares)
            
    return leader_vote_shares
    

def project(config, region_leader_fittings, regional_leader_likeability_votes):
    
    electiondata_2019 = open(config['InputDataFiles']['ElectionResults2019'])
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

def project_2024(libdem_leader, labour_leader, config, region_leader_fittings, regional_leader_likeability_votes, constituency_offset):
    
    electiondata_2019 = open(config['InputDataFiles']['ElectionResults2019'])
    csv_electiondata_2019 = csv.DictReader(electiondata_2019)
    
    #Build destination filepath name
    base_file_name = config['OutputDataFiles']['ElectionProjection'].split('.')
    file_name = base_file_name[0] + "_" + libdem_leader.name + "_" + labour_leader.name + '.' + base_file_name[1]
    targetdata_2024 = open(file_name, 'w', newline='')
    
    fieldnames = csv_electiondata_2019.fieldnames
    fieldnames.append('ld_swing_2019')
    fieldnames.append('result_2024')
    fieldnames.append('first_party_2024')
    fieldnames.append('second_party_2024')
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
        