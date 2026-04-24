# filename: traffic/traffic_classes.py

"""
The File Defines the Traffic Class
This file contains definitions used by PacketFactory and queue disciplines.
"""


class TrafficClass:
    VOIP = "voip"
    BULK = "bulk"
    BEST_EFFORT = "best_effort"

    ALL = [VOIP, BULK, BEST_EFFORT]

    PRIORITY = {
        VOIP: 1,
        BULK: 2,
        BEST_EFFORT: 3,
    }

    MEAN_SIZE = {
        VOIP: 160,  
        BULK: 1400,  
        BEST_EFFORT: 512, 
    }
