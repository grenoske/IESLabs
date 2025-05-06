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

    def read(self, batch_size=5) -> list[AggregatedData]:
        """Метод повертає дані отримані з датчиків"""
        result = []
        for _ in range(batch_size):
            # use _get_next() to get next row or reset reader if at EOF
            accelerometer_data = self._get_next('accelerometer_reader', 'accelerometer_file', self.accelerometer_filename)
            gps_data = self._get_next('gps_reader', 'gps_file', self.gps_filename)
            parking_data = self._get_next('parking_reader', 'parking_file', self.parking_filename)
        
            # unpacking
            accelerometer = Accelerometer(*map(int, accelerometer_data))
            gps = Gps(*map(float, gps_data))
            empty_count, *gps_coordinates = map(float, parking_data)
            parking = Parking(empty_count=empty_count, gps=Gps(*gps_coordinates))

            time = datetime.now()
            result.append(AggregatedData(1, accelerometer, gps, parking, time))

        return result
    
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

    

    def _reset_reader(self, filename):
        """Reopen and reinitialize reader after reaching end of file method"""
        file = open(filename, 'r')
        csv_reader = reader(file)
        next(csv_reader)  
        return file, csv_reader
    
    def _get_next(self, reader_attr, file_attr, filename):
        try:
            return next(getattr(self, reader_attr))
        except StopIteration:
            getattr(self, file_attr).close()
            new_file, new_reader = self._reset_reader(filename)
            setattr(self, file_attr, new_file)
            setattr(self, reader_attr, new_reader)
            return next(new_reader)