from pydantic import BaseModel
from typing import List
import csv


class AccelerometerRecord(BaseModel):
    x: float
    y: float
    z: float

class GPSPoint(BaseModel):
    lat: float
    lon: float

# TODO: Замість читання з CSV реалізувати завантаження даних зі Store
class DataSource:
    @staticmethod
    def load_accelerometer_data(path: str) -> List[AccelerometerRecord]:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            return [AccelerometerRecord(x=float(r['X']), y=float(r['Y']), z=float(r['Z'])) for r in reader]

    @staticmethod
    def load_gps_data(path: str) -> List[GPSPoint]:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            return [GPSPoint(lat=float(r['lat']), lon=float(r['lon'])) for r in reader]
