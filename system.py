import yaml
import math
import pandas as pd
import numpy as np

from utilities import calc_irradiance_on_tilted_plane
import constants as c

class System:
    def __init__(self, system_path):
        # read system parameter file
        with open(system_path, "r") as stream:
            try:
                component_file = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self.components = {}
        # Add component instances as attributes
        for component, params in component_file.items():
            #print(component)
            constructor =  globals()[component] # create reference to component class
            #setattr(self, component, constructor(params)) # add component instance as attribute to the systems
            self.components[component] = constructor(params)

    def calc_energy(self, heat_demand, el_demand, weather):
        ''' Calculate heat and electricity balances
        '''
        # heat balance
        res = pd.DataFrame()

        #used_gas = self.GasBoiler.calc(heat_demand)
        for component in self.components:
            res[self.components[component].energy] = self.components[component].calc_energy(heat_demand, el_demand, weather) # [Wh]

        # electricity balance
        #pv_production = self.Photovoltaic.calc(weather)
        #balance = el_demand - pv_production
        #el_feedin = balance.where(balance < 0, 0)
        #el_supply = balance.where(balance > 0, 0)

        return res
        #return {'Gas consumption [kwh/a]': used_gas.sum()/1000, 'Electricity PV feed-in [kWh/a]': el_feedin.sum()/1000, 'Electricity grid supply [kWh/a]': el_supply.sum()/1000}, used_gas, el_feedin, el_supply
    
    def calc_emissions(self, year, scenario, system_results):
        spec_co2_gas = scenario.eco2_path['spec_CO2_gas [g/kWh]'].at[year]
        spec_co2_el = scenario.eco2_path['spec_CO2_el [g/kWh]'].at[year]
        spec_co2 = {'gas' : spec_co2_gas, 'el' : spec_co2_el}

        res = pd.DataFrame()
        for component in self.components:
            res[self.components[component].emission] = self.components[component].calc_emissions(system_results[self.components[component].energy], spec_co2) # [t]

        res['CO2 emissions total [t]'] = res.sum(axis = 1) # total co2 emissions [tons]

        return res 

    def calc_energy_cost(self, year, scenario, system_results):
        spec_cost_gas = scenario.eco2_path['cost_gas [ct/kWh]'].at[year]
        spec_cost_el_hh = scenario.eco2_path['cost_el_hh [ct/kWh]'].at[year]
        spec_cost_el_hp = scenario.eco2_path['cost_el_hp [ct/kWh]'].at[year]
        if 'Photovoltaic' in self.components:
            pv_feedin_tariff = self.components['Photovoltaic'].feedin_tariffs.at[year] # [ct/kWh]
            if pv_feedin_tariff == 0:
                print(f"The feed-in tariff payment period of your PV system is expired: {self.components['Photovoltaic'].feedin_tariffs.at[year-1]:.2f} ct/kWh -> {self.components['Photovoltaic'].feedin_tariffs.at[year]:.2f} ct/kWh\n")
        else:
            pv_feedin_tariff = 0
        
        spec_cost_energy = {'gas' : spec_cost_gas, 'el hh' : spec_cost_el_hh, 'el hp' : spec_cost_el_hp, 'pv feed-in' : pv_feedin_tariff}

        res = pd.DataFrame()
        
        for component in self.components:
            res[self.components[component].cost] = self.components[component].calc_energy_cost(system_results[self.components[component].energy], spec_cost_energy) # [Euro]

        res['Energy cost total [Euro]'] = res.sum(axis=1) # total energy costs [Euro]

        return res


    def calc_investment_cost(self):
        invest = {}
        
        for component in self.components:
            invest[self.components[component].invest] = self.components[component].calc_investment_cost() # [Euro]

        sum = 0
        for value in invest.values():
            sum += value
        invest['Investment cost total [Euro]'] = sum # total investment costs [Euro]

        return invest



class Component:
    def __init__(self, params, verbose = False):
        for key, value in params.items():
            if verbose == True:
                print(f"    - {key}, {value}")
            setattr(self, key, value)

class GasBoiler(Component):
    def __init__(self, params):
        Component.__init__(self, params)
        self.energy = "GasBoiler Gas Consumption [Wh]"
        self.emission = "GasBoiler CO2 emissions [t]"
        self.cost = "GasBoiler Gas cost [Euro]"
        self.invest = "GasBoiler Invest [Euro]"

    def calc_energy(self, heat_demand, el_demand, weather):
        used_fuel = heat_demand / self.efficiency
        return used_fuel

    def calc_emissions(self, energy, spec_co2):
        co2_emissions = energy * spec_co2['gas'] / 1e9   # [Wh]/1000 * [g/kWh]/1e6 = [tons]
        return co2_emissions

    def calc_energy_cost(self, energy, spec_cost):
        energy_cost = energy/1000 * spec_cost['gas']/100 # [Wh]/1000 * [ct/kWh]/100 = [Euro]
        return energy_cost

    def calc_investment_cost(self):
        cost = 0 # ToDo add calculation and power_nom
        return cost
    

class Photovoltaic(Component): 
    def __init__(self, params):
        Component.__init__(self, params)
        self.energy = "PV El. Production [Wh]"
        self.emission = "PV CO2 emissions [t]"
        self.cost = "PV feed-in revenue [Euro]"
        self.invest = "PV Invest [Euro]"
        if self.construction_year >= c.START_YEAR:
            self.feedin_tariff = self.calc_feedin_tariff()
        self.feedin_tariffs = self.set_feedin_tariffs()

    def calc_feedin_tariff(self):
        ''' Calculate the constant feed-in tariff for the PV System based on its year of construction.
        Returns
        -------
        float
            feed-in tariff [ct/kWh]
        '''
        # PV feed-in tariff for installation in Jan 2022 
        # https://www.photovoltaik4all.de/aktuelle-eeg-verguetungssaetze-fuer-photovoltaikanlagen-2017
        feedin_tariff_ref = 6.83 # [ct/kWh]
        ref_year = 2022
        # monthly basic degression of feed-in tariff, stated in EEG 2021, value adopted every quarter depending on PV installaton rate
        # https://www.solaranlagen-portal.com/photovoltaik-grossanlage/wirtschaftlichkeit/degression-einspeiseverguetung
        degression_rate = 0.4 # [%] monthly
        
        n_months = (self.construction_year - ref_year) * 12 # number of months passed since reference year Jan 2022
        feedin_tariff = feedin_tariff_ref * math.pow(1 - degression_rate/100, n_months) # [ct/kWh]
        
        return feedin_tariff

    def set_feedin_tariffs(self):
        ''' Set feedin-tariff for a duration of 20 years.
        Returns
        -------
        pd.Series
            feed-in tariff for PV system in the game period 2022-2045
        '''
        duration = 20 # [a] validity of feedin tariff
        index = np.linspace(c.START_YEAR, c.END_YEAR, c.END_YEAR-c.START_YEAR+1)
        feedin_tariffs = pd.Series(0, index) # initialize series with zeros
        start_feedin = max(self.construction_year, c.START_YEAR)
        feedin_tariffs.loc[start_feedin : self.construction_year + duration] = self.feedin_tariff
        #print(feedin_tariffs)
        return feedin_tariffs



    def calc_energy(self, heat_demand, el_demand, weather):
        ''' calculate PV power
        Parameters
        ----------
        weather : pandas_df
            weather['G(h) [W/m^2]']  : global horizontal irradiance [W/m^2]
            weather['Gb(n) [W/m^2]'] : beam normal irradiance on PV module [W/m^2]
            weather['Gd(h) [W/m^2]'] : diffuse horizontal irradiance on PV module [W/m^2]
            weather['T_amb [degC]']  : ambient temperature [degC]
        
        Returns
        -------
        float
            power produced by the PV modules [W]
        '''

        # calculate irradiance on tilted plane
        irradiance_tilted = calc_irradiance_on_tilted_plane(weather, self.tilt_angle, self.azimuth_angle)

        temp_amb = weather['T_amb [degC]']

        #constant parameters
        a0 = 0.8249     #constant eff. parameter
        a1 = 0.0007     #linear eff. parameter
        a2 = -1E-6      #quadratic eff. parameter
        a3 = 4E-10      #cubic eff. parameter
        u_pv = 12.0     #PV voltage [V]
        c_th_pv = 0.5   #thermal capacity of PV module [kJ/kgK]
        area_spec = 6.5 #specific area of PV module [m²/kW]
        irrad_norm = 1.0#standard irradiance [kW/m²]
        temp_stc = 25   #standard test condition temperature [°C]
        
        if self.power_nom != 0:
            eta = a0 + a1*irradiance_tilted + a2* irradiance_tilted.pow(2) + a3* irradiance_tilted.pow(3) # efficiency curve
            area_total = area_spec * self.power_nom # total area [m²]
            eta_nom = self.power_nom / (irrad_norm * area_total) # nominal efficiency [-]
            eta = eta * self.efficiency_param * eta_nom # efficiency
            temp_pv = temp_amb + c_th_pv * irradiance_tilted / u_pv # temperature of PV module [degC]
            power_pv_opt = eta * irradiance_tilted / 1000 * area_total # PV power without temperature losses [kW]
            power = power_pv_opt * (1 - self.neg_temp_coeff/100 * (temp_pv - temp_stc)) * 1000 # PV power [W]
        else:
            power = 0
        
        return power # W

    def calc_emissions(self, energy, spec_co2):
        co2_emissions = 0   # [Wh]/1000 * [g/kWh]/1e6 = [tons]
        return co2_emissions

    def calc_energy_cost(self, energy, spec_cost):
        energy_cost = - energy/1000 * spec_cost['pv feed-in']/100 # [Wh]/1000 * [ct/kWh]/100 = [Euro]
        return energy_cost
    
    def calc_investment_cost(self):
        cost = self.power_nom * self.cost_value_a * math.pow(self.power_nom, self.cost_value_b)
        return cost

class HeatPumpAir(Component):
    def __init__(self, params):
        Component.__init__(self, params)
        self.energy = "HeatPumpAir El. Consumption [Wh]"
        self.emission = "HeatPumpAir CO2 emissions [t]"
        self.cost = "HeatPumpAir El. cost [Euro]"
        self.invest = "HeatPumpAir Invest [Euro]"

    def calc_energy(self, heat_demand, el_demand, weather):
        # calculate sink temperature with heating curve
        temp_sink = self.hc_const + self.hc_lin * weather['T_amb [degC]'] + self.hc_quad * np.power(weather['T_amb [degC]'],2)
        
        #calculate temperature difference between source and sink
        delta_temp = temp_sink - weather['T_amb [degC]']
        if isinstance(delta_temp, pd.Series):
            delta_temp.clip(lower = 0, inplace=True)
        else:
            if delta_temp < 0: #if source temperature is higher than sink temperature
                delta_temp = 0 #set temperature difference to zero

        #calculate thermal power of the heat pump
        if isinstance(heat_demand, pd.Series):
            if heat_demand.max()/1000 > self.power_nom:
                print(f'Heating load can not be covered by the Heat Pump! Maximum heat load : {heat_demand.max()/1000:.2f} kW')
            power_th = heat_demand.clip(upper = self.power_nom * 1000)
        else:
            if heat_demand/1000 < self.power_nom: #if the heating load can be covered by the heat pump
                power_th = heat_demand #heat delivered by the heat pump equals the heating load
            else: #if the heating load is bigger than the max heat pump power
                power_th = self.power_nom * 1000 #heat delivered by the heat pump is max heat pump power
                print(f'Heating load can not be covered by the Heat Pump! Heat load : {heat_demand/1000:.2f} kW')

        #calculate COP
        cop = self.c_eff_const + self.c_eff_lin * delta_temp + self.c_eff_quad * np.power(delta_temp,2)
        
        #calculate electrical power of the heat pump
        power_el = power_th / cop
        return power_el

    def calc_emissions(self, energy, spec_co2):
        co2_emissions = energy * spec_co2['el'] / 1e9   # [Wh]/1000 * [g/kWh]/1e6 = [tons]
        return co2_emissions

    def calc_energy_cost(self, energy, spec_cost):
        energy_cost = energy/1000 * spec_cost['el hp']/100 # [Wh]/1000 * [ct/kWh]/100 = [Euro]
        return energy_cost

    def calc_investment_cost(self):
        cost = self.power_nom * self.cost_value_a * math.pow(self.power_nom, self.cost_value_b)
        return cost