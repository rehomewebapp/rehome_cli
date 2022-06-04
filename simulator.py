import pandas as pd

import controller

class Simulator():
    def __init__(self, user, building, system, scenario):
        self.user = user
        self.building = building
        self.system = system
        self.scenario = scenario
        self.controller = controller.Ctrl_GasBoiler()
        

    def one_step(self, year, Qdot_heat_load, P_el_hh):
        # calculate energy
        system_results = self.controller.control(Qdot_heat_load, P_el_hh, self.system)
        # calculate eco2
        ecologic_results = self.system.calc_emissions(year, self.scenario, system_results)
        economic_results = self.system.calc_energy_cost(year, self.scenario, system_results)

        results = {'system' : system_results, 'ecology' : ecologic_results, 'economy' : economic_results}
        return results

    def simulate_year(self, year):
        # Building heat demand
        hourly_heat_demand = self.building.calc(self.user)[1]
        # User el profile
        hourly_el_demand = self.user.profile['el_hh [W]']
        
        hours = hourly_heat_demand.index

        results = {}
        results['system'] = pd.DataFrame(index = hours)
        results['economy'] = pd.DataFrame(index = hours)
        results['ecology'] = pd.DataFrame(index = hours)
        for hour in hours:
            Qdot_heat_load = hourly_heat_demand.loc[hour]
            P_el_hh = hourly_el_demand.loc[hour]
            one_step_results = self.one_step(year, Qdot_heat_load, P_el_hh)
            for category, values in one_step_results.items(): # system, ecology, economy
                for key, value in values.items():
                    results[category].at[hour, key] = value

        # economic balance
        #annual_economy_results = energy_costs.sum() # [Euro]
        results["economy"].at[0, "Event balance [Euro/a]"] = self.user.event_economic_balance
        results["economy"].at[0, "Investment cost [Euro/a]"] = self.user.action_economic_balance

        # annual revenues and expenses
        results["economy"].at[0, 'Revenues [Euro/a]'], results["economy"].at[0, 'Expenses [Euro/a]'] = self.user.calc_economy() # [Euro]

        # calculate economic balance
        results["economy"].at[0, "Balance [Euro/a]"] = (results["economy"].at[0, 'Revenues [Euro/a]'] - results["economy"].at[0, 'Expenses [Euro/a]']\
             - results['economy']['Energy cost total [Euro]'].sum() + self.user.event_economic_balance - self.user.action_economic_balance)
        self.user.event_economic_balance, self.user.action_economic_balance = 0, 0

        # ToDo! calc building results with actual heating power
        results['building'] = self.building.calc(self.user)[0]
        # ToDo! calc comfort deviation with actual room temperature
        results['comfort'] = {"Comfort deviation [degC]" : self.user.comfort_temperature - self.user.set_point_temperature}    # [degC]
        return results