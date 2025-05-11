import csv
import json
import asyncio
import threading
import websockets
from typing import List, Union
from datetime import datetime
from kivy import Logger
from pydantic import BaseModel, field_validator
import os

STORE_HOST = os.environ.get("STORE_HOST") or "localhost"
STORE_PORT = os.environ.get("STORE_PORT") or 8000



class AccelerometerRecord(BaseModel):
    x: float
    y: float
    z: float


class GPSPoint(BaseModel):
    lat: float
    lon: float


class ProcessedAgentData(BaseModel):
    road_state: str
    user_id: int
    x: float
    y: float
    z: float
    latitude: float
    longitude: float
    timestamp: datetime

    @classmethod
    @field_validator("timestamp", mode="before")
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)


class DataSource:
    def __init__(self, user_id: int = None, use_network: bool = False):
        self.user_id = user_id
        self.use_network = use_network
        self.index = 0
        self.connection_status = None
        self._gps_data: List[GPSPoint] = []
        self._acc_data: List[AccelerometerRecord] = []
        self._new_points = []

        if use_network and user_id is not None:
            threading.Thread(target=self._start_loop, daemon=True).start()
        else:
            self.load_local_data("lab5/data.csv", "lab5/gps.csv")
            
    def load_local_data(self, acc_path: str, gps_path: str):
        with open(acc_path, newline='') as f:
            reader = csv.DictReader(f)
            self._acc_data = [
                AccelerometerRecord(x=float(r['X']), y=float(r['Y']), z=float(r['Z'])) for r in reader
            ]
        with open(gps_path, newline='') as f:
            reader = csv.DictReader(f)
            self._gps_data = [
                GPSPoint(lat=float(r['lat']), lon=float(r['lon'])) for r in reader
            ]

    async def connect_to_server(self):
        print("trying CONNECT TO SERVER..")
        uri = f"ws://localhost:8000/ws/"
        while True:
            print("CONNECT TO SERVER")
            try:
                async with websockets.connect(uri) as websocket:
                    self.connection_status = "Connected"
                    while True:
                        data = await websocket.recv()  
                        self.handle_received_data(data)
            except Exception as e:
                print(f"Connection failed: {e}")
                await asyncio.sleep(5)

    def handle_received_data(self, data):
        print(f"Received data: {data}")
        parsed_data = [
            ProcessedAgentData(**entry) for entry in json.loads(data)
        ]
        parsed_data.sort(key=lambda d: d.timestamp)
        for entry in parsed_data:
            self._gps_data.append(GPSPoint(lat=entry.latitude, lon=entry.longitude))
            self._acc_data.append(AccelerometerRecord(x=entry.x, y=entry.y, z=entry.z))

    def get_next_data_point(self) -> Union[tuple[GPSPoint, AccelerometerRecord], None]:
        if self.index < len(self._gps_data) and self.index < len(self._acc_data):
            result = (self._gps_data[self.index], self._acc_data[self.index])
            self.index += 1
            return result
        return None

    def get_all_gps(self) -> List[GPSPoint]:
        return self._gps_data
    
    def _start_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_to_server())
