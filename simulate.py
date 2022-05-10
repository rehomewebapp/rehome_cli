
def calculate(year, user, building, system, scenario, annual_results_last_year):

    # Building
    annual_building_results, hourly_heat_demand = building.calc(user)

    # User
    hourly_el_demand = user.profile['el_hh [W]']    # Wh
    annual_el_hh  = hourly_el_demand.sum()    # Wh 
    
    # System
    annual_system_results, hourly_used_gas, hourly_el_feedin, hourly_el_supply = system.calc(hourly_heat_demand, hourly_el_demand, building.weather) # kWh, Wh

    # Eco2 analysis
    ecology_results, economy_results = eco2(year, user, scenario, annual_system_results)

    return annual_building_results, annual_system_results, ecology_results, economy_results

# {'Building':annual_building_results, 'System':0, 'Eco2': 0 } 


''' !toDo simplify simulate .. outsource calculations, so that we only have to call a few functions

def simulate(init, user, building, system, scenario):
    
    annual_building_results, hourly_heatdemand = building.calc(user) # Series/reihe ['RH', 'TRANS_TOTAL', 'VENT', 'TRANS_ROOF', 'TRANS_WINDOW', 'SOLAR_GAINS', 'INTERAL_GAINS_APP',...]
    annual_system_results, annual_grid_interactions = system.calc(hourly_heatdemand, user) #Series/reihe ['GasBoiler': ['GasConsumption', 'FullLoadHours', 'Q_th'..], 'PV': ['Autarky', 'ElectricityProduction', 'Feedin', ], 'HeatPump': ['Q_th', 'E_el', 'FullLoadHours', 'El_from_PV', 'El_from_Storage', 'COP'] ]
    eco2_results = eco2.calc(annual_grid_interactions)
    results = [annual_building_results, annual_system_results, eco2_results]

    return results   
'''

def eco2(year, user, scenario, annual_system_results):
    # ECOLOGY
    # CO2 emissions
    spec_co2_gas = scenario.eco2_path['spec_CO2_gas [g/kWh]'].at[year]
    spec_co2_el = scenario.eco2_path['spec_CO2_el [g/kWh]'].at[year]

    co2_gas     = annual_system_results['Gas consumption [kwh/a]'] * spec_co2_gas / 1e6   # [tons]
    co2_el      = annual_system_results['Electricity grid supply [kWh/a]'] * spec_co2_el   / 1e6   # [tons]
    
    co2_emissions = co2_gas + co2_el # total co2 emissions [tons]
    ecology_results = {"CO2 emissions [t]": co2_emissions, "CO2 emissions gas [t]": co2_gas, "CO2 emissions el [t]": co2_el}

    # ECONOMY
    # annual revenues and expenses
    revenues, expenses = user.calc() # [euro]

    # energy costs
    cost_gas = annual_system_results['Gas consumption [kwh/a]'] * scenario.eco2_path['cost_gas [ct/kWh]'].at[year]/100 # [euro]
    cost_el = annual_system_results['Electricity grid supply [kWh/a]'] * scenario.eco2_path['cost_el_hh [ct/kWh]'].at[year]/100 # [euro]
    energy_costs   = cost_gas + cost_el # total energy costs [euro]

    economy_results = {"User revenues [euro/a]": revenues, "User expenses [euro/a]": expenses, "Gas cost [euro/a]": cost_gas, "Electricity cost [euro/a]": cost_el, "Energy cost [euro/a]": energy_costs}

    return ecology_results, economy_results

