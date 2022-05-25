from os import system
import pandas as pd

def calculate(year, user, building, system, scenario):

    # Building
    annual_building_results, hourly_heat_demand = building.calc(user)

    # User
    hourly_el_demand = user.profile['el_hh [W]']    # Wh
    annual_el_hh  = hourly_el_demand.sum()    # Wh
    
    # System
    system_results = system.calc_energy(hourly_heat_demand, hourly_el_demand, building.weather) 

    # Calculate CO2 emissions
    ecology_results = system.calc_emissions(year, scenario, system_results) # [tons]
    
    # Calculate energy costs
    energy_costs = system.calc_energy_cost(year, scenario, system_results) # [Euro]

    annual_economy_results = energy_costs.sum() # [Euro]
    annual_economy_results["Event balance [Euro/a]"] = user.event_economic_balance
    annual_economy_results["Investment cost [Euro/a]"] = user.action_economic_balance

    # annual revenues and expenses
    annual_economy_results['Revenues [Euro/a]'], annual_economy_results['Expenses [Euro/a]'] = user.calc_economy() # [Euro]

    # calculate economic balance
    annual_economy_results["Balance [Euro/a]"] = annual_economy_results['Revenues [Euro/a]'] - annual_economy_results['Expenses [Euro/a]'] - energy_costs.sum().sum() + user.event_economic_balance - user.action_economic_balance
    user.event_economic_balance, user.action_economic_balance = 0, 0

    # COMFORT
    comfort_deviation = {"Comfort deviation [degC]" : user.comfort_temperature - user.set_point_temperature}    # [degC]

    return annual_building_results, system_results, ecology_results, annual_economy_results, comfort_deviation

   

