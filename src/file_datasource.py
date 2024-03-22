from csv import reader
from datetime import datetime
from domain.aggregated_data import AggregatedData
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.parking import Parking

class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str, parking_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.parking_filename = parking_filename

    def read(self) -> AggregatedData:
        """Метод повертає дані отримані з датчиків"""
        # read line of csv data
        try:
            accelerometer_data = next(self.accelerometer_reader)
            gps_data = next(self.gps_reader)
            parking_data = next(self.parking_reader)
        except StopIteration:
            raise IndexError("No data available from one of the sensors")
        
        # unpacking
        accelerometer = Accelerometer(*map(int, accelerometer_data))
        gps = Gps(*map(float, gps_data))
        empty_count, *gps_coordinates = map(float, parking_data)
        parking = Parking(empty_count=empty_count, gps=Gps(*gps_coordinates))

        time = datetime.now()

        return AggregatedData(1, accelerometer, gps, parking, time)
    
    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""
        self.accelerometer_file = open(self.accelerometer_filename, 'r')
        self.gps_file = open(self.gps_filename, 'r')
        self.parking_file = open(self.parking_filename, 'r')

        self.accelerometer_reader = reader(self.accelerometer_file)
        self.gps_reader = reader(self.gps_file)
        self.parking_reader = reader(self.parking_file)

        # skip headers of csv file
        self.accelerometer_reader.__next__()
        self.gps_reader.__next__()
        self.parking_reader.__next__()
    
    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""
        self.accelerometer_file.close()
        self.gps_file.close()
        self.parking_file.close()