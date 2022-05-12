import yaml

from utilities import calc_irradiance_on_tilted_plane

class System:
    def __init__(self, system_path):
        # read system parameter file
        with open(system_path, "r") as stream:
            try:
                components = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        
        # Add component instances as attributes
        for component, params in components.items():
            constructor =  globals()[component] # create reference to component class
            setattr(self, component, constructor(params)) # add component instance as attribute to the systems

    def calc(self, heat_demand, el_demand, weather):
        ''' Calculate heat and electricity balances
        '''
        # heat balance
        used_gas = self.GasBoiler.calc(heat_demand)

        # electricity balance
        pv_production = self.Photovoltaic.calc(weather)
        balance = el_demand - pv_production
        el_feedin = balance.where(balance < 0, 0)
        el_supply = balance.where(balance > 0, 0)

        return {'Gas consumption [kwh/a]': used_gas.sum()/1000, 'Electricity PV feed-in [kWh/a]': el_feedin.sum()/1000, 'Electricity grid supply [kWh/a]': el_supply.sum()/1000}, used_gas, el_feedin, el_supply

class Component:
    def __init__(self, params, verbose = False):
        for key, value in params.items():
            if verbose == True:
                print(f"    - {key}, {value}")
            setattr(self, key, value)

class GasBoiler(Component):
    def __init__(self, params):
        Component.__init__(self, params)

    def calc(self, heatdemand):
        used_fuel = heatdemand * self.efficiency
        return used_fuel

class Photovoltaic(Component): 
    def __init__(self, params):
        Component.__init__(self, params)

    def calc(self, weather):
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
        
        return power
