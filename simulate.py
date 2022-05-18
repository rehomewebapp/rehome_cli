
def calculate(year, user, building, system, scenario, annual_results_last_year):

    # Building
    annual_building_results, hourly_heat_demand = building.calc(user)

    # User
    hourly_el_demand = user.profile['el_hh [W]']    # Wh
    annual_el_hh  = hourly_el_demand.sum()    # Wh
    
    # System
    annual_system_results, hourly_used_gas, hourly_el_feedin, hourly_el_supply = system.calc(hourly_heat_demand, hourly_el_demand, building.weather) # kWh, Wh

    # Calculate economic, ecologic and comfort balances
    ecology_results, economy_results, comfort_deviation = balance(year, user, scenario, annual_system_results)

    return annual_building_results, annual_system_results, ecology_results, economy_results, comfort_deviation


def balance(year, user, scenario, annual_system_results):
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
    revenues, expenses = user.calc() # [Euro]

    # energy costs
    cost_gas = annual_system_results['Gas consumption [kwh/a]'] * scenario.eco2_path['cost_gas [ct/kWh]'].at[year]/100 # [Euro]
    cost_el = annual_system_results['Electricity grid supply [kWh/a]'] * scenario.eco2_path['cost_el_hh [ct/kWh]'].at[year]/100 # [Euro]
    energy_costs   = cost_gas + cost_el # total energy costs [Euro]

    balance = revenues - expenses - energy_costs + user.event_economic_balance
    

    economy_results = {"Balance [Euro/a]"      : balance,
                       "Event balance [Euro/a]": user.event_economic_balance,
                       "User revenues [Euro/a]": revenues, 
                       "User expenses [Euro/a]": expenses, 
                       "Gas cost [Euro/a]": cost_gas, 
                       "Electricity cost [Euro/a]": cost_el, 
                       "Energy cost [Euro/a]": energy_costs}

    user.event_economic_balance = 0

    # COMFORT
    comfort_deviation = {"Comfort deviation [degC]" : user.comfort_temperature - user.set_point_temperature}    # [degC]

    return ecology_results, economy_results, comfort_deviation

