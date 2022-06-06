import yaml
import math
import pandas as pd
import numpy as np

from utilities import calc_irradiance_on_tilted_plane
import constants as c

class System:
    def __init__(self, system_path):
        self.components = {}
        try:
            # read system parameter file
            with open(system_path, "r") as stream:
                try:
                    component_file = yaml.safe_load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
            # Add component instances as attributes
        
            for component, params in component_file.items():
                #print(component)
                constructor =  globals()[params['type']] # create reference to component class
                #setattr(self, component, constructor(params)) # add component instance as attribute to the systems
                self.components[component] = constructor(params)
        except:
            pass


    def write_yaml(self, path):
        dict = {}
        for component_name, component_instance in self.components.items():
            dict[component_name] = component_instance.__dict__
        
        with open(path, 'w') as f:
            yaml.dump(dict, f)

    
    def calc_emissions(self, year, scenario, system_results):
        spec_co2_gas = scenario.eco2_path['spec_CO2_gas [g/kWh]'].at[year]
        spec_co2_el = scenario.eco2_path['spec_CO2_el [g/kWh]'].at[year]
        spec_co2 = {'gas' : spec_co2_gas, 'el' : spec_co2_el}

        res = {}
        sum = 0
        for component in self.components:
            res[self.components[component].emission] = self.components[component].calc_emissions(system_results[self.components[component].energy], spec_co2) # [t]
            sum += res[self.components[component].emission]
        
        # Grid household el
        P_el_grid_hh = system_results["Electricity grid household [Wh]"]
        co2_emissions_el_hh = P_el_grid_hh * spec_co2_el / 1e9   # [Wh]/1000 * [g/kWh]/1e6 = [tons]
        res["CO2 emissions el household [t]"] = co2_emissions_el_hh
        sum += co2_emissions_el_hh

        res['CO2 emissions total [t]'] = sum # total co2 emissions [tons]

        return res 

    def calc_energy_cost(self, year, scenario, system_results):
        spec_cost_gas = scenario.eco2_path['cost_gas [ct/kWh]'].at[year]
        spec_cost_el_hh = scenario.eco2_path['cost_el_hh [ct/kWh]'].at[year]
        spec_cost_el_hp = scenario.eco2_path['cost_el_hp [ct/kWh]'].at[year]

        # find PV system, note only the last component with type Photovoltaic will be used!
        for component, params in self.components.items():
            if params.type == 'Photovoltaic':
                pv_system = self.components[component]
                if pv_system.feedin_tariff_start + 20 < year: # tariff expired
                    pv_system.feedin_tariff_start = year
                    old_tariff = pv_system.feedin_tariff
                    pv_feedin_tariff = pv_system.calc_feedin_tariff() 
                    print(f"The feed-in tariff payment period of your PV system is expired: {old_tariff:.2f} ct/kWh -> {pv_feedin_tariff:.2f} ct/kWh\n")
                    input("    ENTER to continue")
                else:
                    pv_feedin_tariff = pv_system.feedin_tariff
            else:
                pv_feedin_tariff = 0


        
        
        spec_cost_energy = {'gas' : spec_cost_gas, 'el hh' : spec_cost_el_hh, 'el hp' : spec_cost_el_hp, 'pv feed-in' : pv_feedin_tariff}

        res = {}
        sum = 0
        for component in self.components:
            res[self.components[component].cost] = self.components[component].calc_energy_cost(system_results[self.components[component].energy], spec_cost_energy) # [Euro]
            sum += res[self.components[component].cost]
            #print(res[self.components[component].cost])

        # Grid household el
        P_el_grid_hh = system_results["Electricity grid household [Wh]"]

        energy_cost_grid_el_hh = P_el_grid_hh/1000 * spec_cost_el_hh/100 # [Wh]/1000 * [ct/kWh]/100 = [Euro]
        res["Household El. cost [Euro]"] = energy_cost_grid_el_hh
        sum += energy_cost_grid_el_hh

        res['Energy cost total [Euro]'] = sum # total energy costs [Euro]

        return res


class Component:
    def __init__(self, params, verbose = False):
        for key, value in params.items():
            if verbose == True:
                print(f"    - {key}, {value}")
            setattr(self, key, value)

class GasBoiler(Component):
    def __init__(self, params):
        Component.__init__(self, params)
        self.heat = "GasBoiler Heat Production [Wh]"
        self.energy = "GasBoiler Gas Consumption [Wh]"
        self.emission = "GasBoiler CO2 emissions [t]"
        self.cost = "GasBoiler Gas cost [Euro]"
        self.invest = "GasBoiler Invest [Euro]"

    def configure(self, year):
        print("Please specify the parameters of your GasBoiler:")
        # for system generation
        if year < c.START_YEAR:
            self.construction_year = int(input('Construction year: '))
        self.power_nom = float(input("Nominal power in kW : "))
        self.efficiency = float(input("Efficiency (0.95 for condensing, 0.9 for non condensing): "))

    def calc_energy(self, Qdot_heat_actual):
        used_gas = Qdot_heat_actual / self.efficiency # [W] assuming hourly time steps
        return used_gas

    def calc_emissions(self, energy, spec_co2):
        co2_emissions = energy * spec_co2['gas'] / 1e9   # [Wh]/1000 * [g/kWh]/1e6 = [tons]
        return co2_emissions

    def calc_energy_cost(self, energy, spec_cost):
        energy_cost = energy/1000 * spec_cost['gas']/100 # [Wh]/1000 * [ct/kWh]/100 = [Euro]
        return energy_cost

    def calc_investment_cost(self):
        cost = self.power_nom * self.cost_value_a * math.pow(self.power_nom, self.cost_value_b)
        return cost
    

class Photovoltaic(Component): 
    def __init__(self, params):
        Component.__init__(self, params)
        self.energy = "PV El. Production [Wh]"
        self.emission = "PV CO2 emissions [t]"
        self.cost = "PV feed-in revenue [Euro]"
        self.invest = "PV Invest [Euro]"

    def configure(self, year):
        print("Please specify the parameters of your PV system:")

        # for system generation
        if year < c.START_YEAR:
            self.construction_year = int(input('Construction year: '))
            self.feedin_tariff = float(input('Feed-in tariff in ct/kWh: '))
        else:
            # system added in main loop
            self.construction_year = year
            self.feedin_tariff = self.calc_feedin_tariff()

        self.power_nom = float(input("Nominal power in kW : "))
        self.tilt_angle = float(input("Tilt angle (0 : horizontal, 90 : vertical) in deg : "))
        orientation_input = input("Orientation (S,SW,W,NW,N,NE,E,SE) : ")
        azimuth_angles = {'S':0, 'SW':45, 'W':90, 'NW':135, 'N':180, 'NE':-135, 'E':-90, 'SE':-45 }
        self.azimuth_angle = azimuth_angles[orientation_input]

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
        
        n_months = (self.feedin_tariff_start - ref_year) * 12 # number of months passed since reference year Jan 2022
        feedin_tariff = feedin_tariff_ref * math.pow(1 - degression_rate/100, n_months) # [ct/kWh]
        
        return feedin_tariff



    def calc_energy(self, weather):
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
            #eta = a0 + a1*irradiance_tilted + a2* irradiance_tilted.pow(2) + a3* irradiance_tilted.pow(3) # efficiency curve
            eta = a0 + a1*irradiance_tilted + a2* np.power(irradiance_tilted, 2) + a3* np.power(irradiance_tilted, 3) # efficiency curve
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
        self.heat = "HeatPumpAir Heat Production [Wh]"
        self.energy = "HeatPumpAir El. Consumption [Wh]"
        self.emission = "HeatPumpAir CO2 emissions [t]"
        self.cost = "HeatPumpAir El. cost [Euro]"
        self.invest = "HeatPumpAir Invest [Euro]"

    def configure(self, year):
        # for system generation
        if year < c.START_YEAR:
            self.construction_year = int(input('Construction year: '))
        print("Please specify the parameters of your HeatPumpAir:")
        self.power_nom = float(input("Nominal power in kW : "))

    def calc_energy(self, heat_demand, weather):
        # calculate sink temperature with heating curve
        temp_sink = self.hc_const + self.hc_lin * weather['T_amb [degC]'] + self.hc_quad * np.power(weather['T_amb [degC]'],2)
        
        #calculate temperature difference between source and sink
        delta_temp = temp_sink - weather['T_amb [degC]']
        if isinstance(delta_temp, pd.Series):
            delta_temp.clip(lower = 0, inplace=True)
        else:
            if delta_temp < 0: #if source temperature is higher than sink temperature
                delta_temp = 0 #set temperature difference to zero

        ''' this should done by the controller
        #calculate thermal power of the heat pump
        if isinstance(heat_demand, pd.Series):
            power_th = heat_demand.clip(upper = self.power_nom * 1000)
            if heat_demand.max()/1000 > self.power_nom:
                uncovered_heat = heat_demand - power_th # W
                input(f'Heating load can not be covered by the Heat Pump! Uncovered heat: {uncovered_heat.sum()/1000:.2f} kWh/a')
            
        else:
            if heat_demand/1000 < self.power_nom: #if the heating load can be covered by the heat pump
                power_th = heat_demand #heat delivered by the heat pump equals the heating load
            else: #if the heating load is bigger than the max heat pump power
                power_th = self.power_nom * 1000 #heat delivered by the heat pump is max heat pump power
                uncovered_heat = heat_demand - power_th # W
                input(f'Heating load can not be covered by the Heat Pump! Uncovered heat : {uncovered_heat/1000:.2f} kW')
        '''
        #calculate COP
        cop = self.c_eff_const + self.c_eff_lin * delta_temp + self.c_eff_quad * np.power(delta_temp,2)
        
        #calculate electrical power of the heat pump
        power_el = heat_demand / cop
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