from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from datasource import DataSource
from kivy.uix.image import Image
import os
from scipy.signal import find_peaks
import numpy as np


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.acc_data = []
        self.gps_data = []
        self.index = 0
        self.car_marker = None
        self.line_layer = LineMapLayer()
        self.z_window = []
    
    def on_start(self):
        """
        Встановлює необхідні маркери, викликає функцію для оновлення мапи
        """
        self.acc_data = DataSource.load_accelerometer_data("lab5/data.csv")
        self.gps_data = DataSource.load_gps_data("lab5/gps.csv")

        if self.gps_data:
            first_point = self.gps_data[0]
            self.car_marker = MapMarker(lat=first_point.lat, lon=first_point.lon, source="lab5/images/car.png")
            self.mapview.add_marker(self.car_marker)

        Clock.schedule_interval(self.update, 0.5)

    def update(self, *args):
        """
        Викликається регулярно для оновлення мапи
        """
        if self.index >= len(self.gps_data):
            return

        gps_point = self.gps_data[self.index]
        self.update_car_marker(gps_point)
        self.line_layer.add_point([gps_point.lat, gps_point.lon])

        if self.index < len(self.acc_data):
            z = self.acc_data[self.index].z
            self.z_window.append(z)
            if len(self.z_window) >= 20:
                self.check_road_quality()
                self.z_window = []

        self.index += 1

    def check_road_quality(self):
        """
        Аналізує дані акселерометра для подальшого визначення
        та відображення ям та лежачих поліцейських
        """
        z = np.array(self.z_window)
        peaks, _ = find_peaks(z, height=16690, distance=2, prominence=20)
        valleys, _ = find_peaks(-z, height=-16640, distance=2, prominence=20)

        current_gps = self.gps_data[self.index]

        for _ in peaks:
            self.set_bump_marker(current_gps)

        for _ in valleys:
            self.set_pothole_marker(current_gps)

    def update_car_marker(self, point):
        """
        Оновлює відображення маркера машини на мапі
        :param point: GPS координати
        """
        self.car_marker.lat = point.lat
        self.car_marker.lon = point.lon

    def set_pothole_marker(self, point):
        """
        Встановлює маркер для ями
        :param point: GPS координати
        """

        pothole = MapMarker(lat=point.lat, lon=point.lon, source="lab5/images/pothole.png")
        self.mapview.add_marker(pothole)

    def set_bump_marker(self, point):
        """
        Встановлює маркер для лежачого поліцейського
        :param point: GPS координати
        """
        bump = MapMarker(lat=point.lat, lon=point.lon, source="lab5/images/bump.png")
        self.mapview.add_marker(bump)

    def build(self):
        """
        Ініціалізує мапу MapView(zoom, lat, lon)
        :return: мапу
        """
        self.mapview = MapView(zoom=16, lat=50.45, lon=30.52)
        self.mapview.add_layer(self.line_layer, mode="scatter")
        return self.mapview


if __name__ == "__main__":
    MapViewApp().run()
