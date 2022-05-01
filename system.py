import yaml

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

        return used_gas, el_feedin, el_supply

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
        power = 0.1 * weather['G(h) [W/m^2]']

        return power
