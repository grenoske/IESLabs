from dataclasses import dataclass
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking

@dataclass
class AggregatedData:
    user_id: int
    accelerometer: Accelerometer
    gps: Gps
    parking: Parking
    timestamp: datetime