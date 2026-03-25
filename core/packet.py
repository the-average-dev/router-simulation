# filename: core/packet.py

"""
This File Define the Packet Class
Packet Class is the structure of a Network Packet
"""

# Priority Map: Lower Number <-> Higher Priority
CLASS_PRIORITY = {
    "voip": 1,
    "bulk": 2,
    "best_effort": 3,
}

class Packet:
    
    # Constructor
    def __init__(
        self,
        id: int,
        size: int, # will be in bytes
        source: str, 
        destination: str,
        traffic_type: str,
        arrival_time: float,
    ):
        self.id = id
        self.size = size
        self.src = source
        self.dst = destination
        self.traffic_type = traffic_type
        self.arrival_time = arrival_time
        
        # check traffic type 
        if traffic_type not in CLASS_PRIORITY:
            raise ValueError(f"Unknown Traffic Type: {traffic_type}")
            
        self.priority = CLASS_PRIORITY[traffic_type]

    # Less than comparator for Priority Comparision
    def __lt__(
        self,
        other: "Packet"
    ) -> bool:
        
        if self.priority != other.priority:
            return self.priority < other.priority
            
        return self.arrival_time < other.arrival_time

    # Representation of a Packet
    def __repr__(self) -> str:
        return (
            f"Packet(id={self.id}, class={self.traffic_type}, src={self.src}, dst={self.dst}, size={self.size} bytes)"
        )
