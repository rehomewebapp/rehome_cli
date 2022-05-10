
import os
import math
from pathlib import Path
import numpy as np

import yaml
from pvlib import solarposition

import utilities
import constants as C

class Building:
    def __init__(self, building_path, verbose = False):
        ''' Initialize the building, read all parameters from the given '''

        # load building parameters from file
        with open(building_path, "r") as stream:
            try:
                building_params = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        for key, value in building_params.items():
            if verbose == True:
                print(f"    - {key}, {value}")
            setattr(self, key, value)

        # calculate additional building parameters
        self.floor_area = self.ground_area * self.stories #[m^2]
        self.volume = self.story_height * self.floor_area # [m^3]
        self.opaque_area = math.sqrt(self.floor_area) * 4 + 2 * self.floor_area #[m^2] assuming quadratic ground shape and flat roof

        # load location dependend weather data
        self.weather = self.load_weather()

    def load_weather(self):
        # If there is no weather data for the given location in the input directory download it
        latitude, longitude = self.location['latitude'], self.location['longitude']
        tmy_filename = f"TMY_lat{latitude}_lon{longitude}.json"
        #print(tmy_filename)
        
        weather_path = f"data/weather/{tmy_filename}" #Path.joinpath("data").joinpath("weather").joinpath(tmy_filename)
        if not os.path.isfile(weather_path):
            print(f'Downloading TMY data for latitude: {latitude}, longitude: {longitude}')
            data = utilities.get_tmy_data(latitude=latitude, longitude=longitude)
            utilities.save_tmy_data(data, weather_path)

        df_weather = utilities.read_tmy_data(weather_path)

        column_names = {
            'T2m':'T_amb [degC]', # Ambient air temperature [°C]
            'G(h)': 'G(h) [W/m^2]', # Global horizontal irradiance [W/m^2]
            'Gb(n)': 'Gb(n) [W/m^2]', # Normal beam irradiance [W/m^2]
            'Gd(h)': 'Gd(h) [W/m^2]', # Diffuse horizontal irradiance [W/m^2]
        }

        df_weather.rename(columns=column_names, inplace=True)

        #calculate solar position with weather index and add to weather_df
        solar_position = solarposition.get_solarposition(df_weather.index, latitude, longitude)
        df_weather['solar_zenith [deg]'], df_weather['solar_azimuth [deg]'] = solar_position['zenith'], solar_position['azimuth']

        df_weather.reset_index(inplace = True)
        # print(df_weather.head())
        return df_weather


    def calc(self, user):
        '''calculate the annual heat demand of the building
        '''
        dT = user.comfort_temperature - self.weather['T_amb [degC]'] # temperature difference between ambient air and comfort temperature

        ventilation_losses  = self.ventilation_rate * self.volume * C.DENSITY_AIR * dT # [W]
        transmission_losses = self.u_value * self.opaque_area * dT # [W]
        #solar_gains = 0 # [W] !ToDo iterate over windows and sum up solar heat gains
        heatdemand = ventilation_losses + transmission_losses # - solar_gains # [W]
        return {'Annual heat demand [kWh/a]': heatdemand.sum(), 'Transmission losses [kWh/a]':transmission_losses.sum(), 'Ventilation losses [kWh/a]':ventilation_losses.sum()}, heatdemand