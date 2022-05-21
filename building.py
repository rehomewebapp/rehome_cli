
import os
import math
from pathlib import Path
import numpy as np
import pandas as pd

import yaml

from ruamel.yaml import YAML # this version of pyyaml support dumping without loosing the comments in the .yaml file
yaml = YAML()

from pvlib import solarposition

import utilities
import constants as C

class Building:
    def __init__(self, building_path, verbose = False):
        ''' Initialize the building, read all parameters from the given '''

        # load building parameters from file
        with open(building_path, "r") as stream:
            try:
                building_params = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        
        for key, value in building_params.items():
            if verbose == True:
                print(f"    - {key}, {value}")
            setattr(self, key, value)

        # calculate building geometry
        self.calc_geometry()

        # get u-values
        if self.use_default_u_values == 1: # yes
            self.get_u_values(building_params, building_path)

        # load location dependend weather data
        self.weather = self.get_weather()


    def calc_geometry(self):
        '''This function calculates dimensions, areas and volume of the building
        according to the area-estimation-method by IWU 2005
        and own assumptions'''
        # Parameters for area estimation method according to IWU 2005
        f_basement = {'none' : 0, 'unheated' : 0, 'partly heated' : 0.5, 'fully heated' : 1} # partly heating factor basement
        f_attic = {'none' : 0, 'unheated' : 0, 'partly heated' : 0.5, 'fully heated' : 1} # partly heating factor attic 
        f_dormers = {'none' : 1, 'existing' : 1.3} # correction factor for dormers
        p_ground = 1.33 # [m^2 ground area / m^2 heated area per story]
        p_roof = {'none' : 1.33, 'unheated' : 0, 'partly heated' : 0.75, 'fully heated' : 1.5} # [m^2 roof area / m^2 heated area per story]
        p_upper_ceilig = {'none' : 0, 'unheated' : 1.33, 'partly heated' : 0.67, 'fully heated' : 0} # [m^2 upper ceiling area / m^2 heated area per story]
        p_facade = {'compact' : 0.66, 'elongated' : 0.8} # [m^2 facade area / m^2 heated area per story]
        p_window = 0.2 # [m^2 window area /m^2 heated living area]
        q_facade = {'detached' : 50, 'semi-detached' : 30, 'terraced' : 10} # [m^2] additional area per story
        h_story_nom = 2.5 # [m] nominal story height

        # Calculations according to IWU
        self.n_heated_stories = f_basement[self.basement] + self.stories + 0.75 * f_attic[self.attic] # arithmetic number of heated stories
        self.area_story_heated = self.area_floor / self.n_heated_stories # [m^2] heated area per story
        self.area_ground = p_ground * self.area_story_heated # [m^2]
        self.area_roof = f_dormers[self.dormers] * p_roof[self.attic] * self.area_story_heated # [m^2]
        self.area_upper_ceiling = p_upper_ceilig[self.attic] * self.area_story_heated # [m^2]
        self.area_facade_story = self.story_height / h_story_nom * (p_facade[self.shape] * self.area_story_heated + q_facade[self.neighbours]) #[m^2] facade area per story
        self.area_window = p_window * self.area_floor # [m^2]
        self.area_basement_wall = 0.5 * f_basement[self.basement] * self.area_facade_story # [m^2] basement wall areas agains soil / unheated basement
        self.area_facade = self.n_heated_stories * self.area_facade_story - self.area_basement_wall - self.area_window # [m^2] total opaque facade area
        #self.volume_heated = 4 * self.area_floor * self.story_height / h_story_nom # [m^3]
        self.volume_air = self.area_floor * h_story_nom # [m^3]

        # own assumption
        self.facade_orientations = np.array([0,90,180,-90]) + self.orientation_offset # [deg]

    def get_u_values(self, file, path):
        u_values = pd.read_csv("data/components/u_values.csv", index_col = "bac").loc[self.bac]
        window_types = {'0' : 'wood_single-glazed', '1' : 'wood_double-glazed', '2' : 'plastic_iso', '3' : 'metal_iso'}
        components = ['facade', 'roof', 'upper_ceiling', 'groundplate']
        for i, component in enumerate(components):
            construction_type = getattr(self, f"construction_{component}")
            u_value = float(u_values[f"{component}_{construction_type}"])
            setattr(self, f"u_value_{components[i]}", u_value)
            #print(f"u_value_{components[i]} = {u_value}")
            #print(getattr(self, f"u_value_{components[i]}"))

        self.u_value_window = float(u_values[f'window_{window_types[str(self.type_window)]}'])
        #print(f"window = {self.u_value_window}")

        components.append('window')
        # write u-values to bldg config file
        for component in components:
            u_value = getattr(self, f"u_value_{component}")
            #print(f"{component} = {u_value}")
            file[f"u_value_{component}"] = u_value
        with open(path, 'w') as f:
            yaml.dump(file, f)
        
        
    def get_weather(self):
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

        # calculate solar position with weather index and add to weather_df
        solar_position = solarposition.get_solarposition(df_weather.index, latitude, longitude)
        df_weather['solar_zenith [deg]'], df_weather['solar_azimuth [deg]'] = solar_position['zenith'], solar_position['azimuth']

        # calculate solar irradiance on vertical planes
        tilt_angle = 90 # [deg] vertical
        for orientation in self.facade_orientations:
            irrad_facade = utilities.calc_irradiance_on_tilted_plane(df_weather, tilt_angle, orientation)
            df_weather[f'G(v,{orientation}deg) [W/(m^2)'] = irrad_facade

        # calculate ground temperature dependent on ambient temperature
        df_weather['T_ground [degC]'] = 4.918 * (0.095 * (df_weather['T_amb [degC]'] - 10.545)).apply(math.tanh) + 8.261 # [degC]

        df_weather.reset_index(inplace = True)
        # print(df_weather.head())

        return df_weather


    def calc(self, user):
        '''calculate the annual heat demand of the building
        '''
        # parameters describing the heating state of attic and basement (based on IWU f_attic / f_basement)
        x_basement = {'none' : 1, 'unheated' : 0, 'partly heated' : 0.5, 'fully heated' : 1} # transmission factor basement
        x_attic = {'none' : 1, 'unheated' : 0, 'partly heated' : 0.5, 'fully heated' : 1} # transmission factor attic 

        # temperature differences
        dT = user.set_point_temperature - self.weather['T_amb [degC]'] # [degC]  between ambient and indoor temperature
        dT_ground = user.set_point_temperature - self.weather['T_ground [degC]'] # [degC] between ground and indoor temperature

        # temperatures of unheated adjacent rooms according to DIN 12831-1 Table 4
        bac = ['<1918', '1919-1948', '1949-1957', '1958-1968', '1969-1978', '1979-1983', '1984-1994', '>1995']
        temp_adj_data = [12, 12, 12, 12, 12, 14, 14, 16]
        temp_adj = pd.Series(temp_adj_data, index = bac)
        
        f_corr2ext = (user.set_point_temperature - temp_adj[self.bac]) / dT # [-] temperature correction factor against ambient
        f_corr2ground = (user.set_point_temperature - temp_adj[self.bac]) / dT_ground # [-] temperature correction factor against ground
    
        ventilation_losses  = self.ventilation_rate * self.volume_air * C.DENSITY_AIR * dT # [W]
        infiltration_losses  = self.infiltration_rate * self.volume_air * C.DENSITY_AIR * dT # [W]

        # Transmission losses
        # from heated space to exterior through building envelope
        transmission_losses_facade = self.u_value_facade * self.area_facade * dT # [W]
        transmission_losses_window = self.u_value_window * self.area_window * dT # [W]
        transmission_losses_roof_heated = x_attic[self.attic] * (self.u_value_roof * self.area_roof + self.u_value_upper_ceiling * self.area_upper_ceiling) * dT # [W]
        # from heated space to exterior through unheated space
        transmission_losses_roof_unheated = (1 - x_attic[self.attic]) * (self.u_value_roof * self.area_roof + self.u_value_upper_ceiling * self.area_upper_ceiling) * dT * f_corr2ext # [W]
        # from heated space to ground
        transmission_losses_ground_heated = self.u_value_groundplate * x_basement[self.basement] * (self.area_ground + self.area_basement_wall) * dT_ground # [W]
        # from heated space to ground through unheated space
        transmission_losses_ground_unheated = self.u_value_groundplate * (1 - x_basement[self.basement]) * (self.area_ground + self.area_basement_wall) * dT_ground * f_corr2ground # [W]
        # total
        transmission_losses = transmission_losses_facade + transmission_losses_window + transmission_losses_roof_heated + transmission_losses_roof_unheated + transmission_losses_ground_heated + transmission_losses_ground_unheated # [W]
        
        # solar gains assuming equally distributed window areas over orientations
        solar_gains = 0 # initialization
        for orientation in self.facade_orientations:
            solar_gain = self.g_value_window * (1 - self.shading_window) * self.weather[f'G(v,{orientation}deg) [W/(m^2)'] * self.area_window/4 # [W]
            solar_gains =+ solar_gain # [W]

        heatdemand = ventilation_losses + transmission_losses + infiltration_losses - solar_gains # [Wh] assuming hourly time steps
        
        annual_results = {'Annual heat demand [kWh/a]': heatdemand.sum()/1000,
                          'Transmission losses [kWh/a]': transmission_losses.sum()/1000,
                          'Transmission losses facade [kWh/a]': transmission_losses_facade.sum()/1000,
                          'Transmission losses roof [kWh/a]': transmission_losses_roof_heated.sum()/1000+transmission_losses_roof_unheated.sum()/1000,
                          'Transmission losses ground [kWh/a]': transmission_losses_ground_heated.sum()/1000+transmission_losses_ground_unheated.sum()/1000,
                          'Transmission losses window [kWh/a]': transmission_losses_window.sum()/1000,
                          'Ventilation losses [kWh/a]': ventilation_losses.sum()/1000,
                          'Infiltration losses [kWh/a]': infiltration_losses.sum()/1000,
                          'Solar gains [kWh/a]': solar_gains.sum()/1000}

        return annual_results, heatdemand