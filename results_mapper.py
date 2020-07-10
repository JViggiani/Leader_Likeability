# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 22:10:50 2020

@author: Josh
"""

#The purpose of this script is to take csv data for Layla and Davey and map the results onto a seat projection in the UK (hex?)
'''
Maps to generate:
    Constituency (hex?) result map of libdems under Davey
    Constituency (hex?) result map of libdems under Moran
    Constituency (hex?) 2nd place map of libdems under Davey
    Constituency (hex?) 2nd place map of libdems under Moran
    Heat map of absolute libdem vote share under Davey
    Heat map of absolute libdem vote share under Moran
    Comparison map where each constituency is coloured:
        Orange if won by both
        Grey if won by neither
        Yellow if won by Davey
        Redorange if won by Moran
'''

import configparser
import logging
import time
import csv
import json
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

start_time = time.time()

log_file_name = "constituency_correlations.log"
if os.path.exists(log_file_name):
  os.remove(log_file_name)
logging.basicConfig(filename=log_file_name,level=logging.DEBUG)

config = configparser.ConfigParser()
config.read('config.ini')

input_file_names = config['InputDataFiles']['ElectionProjections'].split(',')
input_file_davey = ''
input_file_moran = ''
for filename in input_file_names:
    if "DAVEY" in filename.upper():
        input_file_davey = filename
    elif "MORAN" in filename:
        input_file_moran = filename

if len(input_file_names) != 2 or input_file_davey == '' or input_file_moran == '':
    raise Exception("Could not find the Davey or Moran file")

data_df_davey = pd.read_csv(input_file_davey, skipinitialspace=True) #open(input_file_davey, 'r')
data_df_moran = pd.read_csv(input_file_moran, skipinitialspace=True)

data_df_davey.fillna(0, inplace=True)
data_df_moran.fillna(0, inplace=True)

map_df = gpd.read_file(config["InputDataFiles"]["Shapefile"])
# map_df is a Pandas dataframe

# Combine the two dataframes by their constituencies
combined_davey = map_df.set_index("pcon19nm").join(data_df_davey.set_index("constituency_name")).reset_index()
combined_moran = map_df.set_index("pcon19nm").join(data_df_moran.set_index("constituency_name")).reset_index()

combined_davey.fillna(0, inplace=True)
combined_moran.fillna(0, inplace=True)

#with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#    print(combined_davey)

##start map
fig, ax = plt.subplots(1, figsize=(60, 60))
combined_davey.plot(column="ld_share_2024", cmap="viridis", 
                   linewidth=0.8, ax=ax)
ax.axis("off")

vmin = 0.
vmax = 100.
sm = plt.cm.ScalarMappable(cmap="viridis")
sm._A = []
cbar = fig.colorbar(sm)
plt.savefig('davey.png')
##end map

##start map
fig, ax = plt.subplots(1, figsize=(60, 60))
combined_moran.plot(column="ld_share_2024", cmap="viridis", 
                   linewidth=0.8, ax=ax)
ax.axis("off")

vmin = 0.
vmax = 100.
sm = plt.cm.ScalarMappable(cmap="viridis")
sm._A = []
cbar = fig.colorbar(sm)
plt.savefig('moran.png')
##end map

print("Calculation performed in " + str(time.time() - start_time) + " seconds.")

logging.shutdown()