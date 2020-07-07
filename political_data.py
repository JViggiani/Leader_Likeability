# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 18:34:37 2020

@author: Josh
"""

from enum import Enum
from political_utility_functions import format_region, format_party

class Party(Enum):
    CON = 1
    LAB = 2
    LD = 3
    SNP = 4
    PC = 5
    BREXIT = 6
    GREEN = 7
    OTHER = 98
    DK = 99
    UNKNOWN = 9999
    
    @staticmethod
    def from_str(label):
        label = format_party(label)
        if label == "CON":
            return Party.CON
        elif label == "LAB":
            return Party.LAB
        elif label == "LD":
            return Party.LD
        elif label == "SNP":
            return Party.SNP
        elif label == "PC":
            return Party.PC
        elif label == "BREXIT":
            return Party.BREXIT
        elif label == "GREEN":
            return Party.GREEN
        elif label == "OTHER":
            return Party.OTHER
        elif label == "DK":
            return Party.DK
        elif label == "UNKNOWN":
            return Party.UNKNOWN
        else:
            if label == "SPK":
                return Party.OTHER
            print(label)
            raise NotImplementedError
    
class Leader(Enum):
    JOHNSON = 1
    CORBYN = 2
    SWINSON = 3
    STURGEON = 4
    PRICE = 5
    FARAGE = 6
    BARTLEYBERRY = 7
    
class Region(Enum):
    EAST_MIDLANDS = 1
    EAST = 2
    LONDON = 3
    NORTH_EAST = 4
    NORTH_WEST = 5
    SCOTLAND = 6
    SOUTH_EAST = 7
    SOUTH_WEST = 8
    WALES = 9
    WEST_MIDLANDS = 10
    YORKSHIRE_AND_THE_HUMBER = 11
    NORTHERN_IRELAND = 99
    
    @staticmethod
    def from_str(label):
        label = format_region(label)
        if label == "EAST_MIDLANDS":
            return Region.EAST_MIDLANDS
        elif label == "EAST":
            return Region.EAST
        elif label == "LONDON":
            return Region.LONDON
        elif label == "NORTH_EAST":
            return Region.NORTH_EAST
        elif label == "NORTH_WEST":
            return Region.NORTH_WEST
        elif label == "SCOTLAND":
            return Region.SCOTLAND
        elif label == "SOUTH_EAST":
            return Region.SOUTH_EAST
        elif label == "SOUTH_WEST":
            return Region.SOUTH_WEST
        elif label == "WALES":
            return Region.WALES
        elif label == "WEST_MIDLANDS":
            return Region.WEST_MIDLANDS
        elif label == "YORKSHIRE_AND_THE_HUMBER":
            return Region.YORKSHIRE_AND_THE_HUMBER
        elif label == "NORTHERN_IRELAND":
            return Region.NORTHERN_IRELAND
        else:
            raise NotImplementedError