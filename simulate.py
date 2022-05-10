
def calculate(year, user, building, system, scenario, annual_results_last_year):

    # Building
    annual_building_results, hourly_heat_demand = building.calc(user)
    hourly_el_demand = user.profile['el_hh [W]']    # Wh

    # ECOLOGY
    # gas consumption

    annual_el_hh  = hourly_el_demand.sum()    # Wh 
    
    annual_system_results, hourly_used_gas, hourly_el_feedin, hourly_el_supply = system.calc(hourly_heat_demand, hourly_el_demand, building.weather) # Wh
    #annual_used_gas = hourly_used_gas.sum()
    #annual_el_feedin = hourly_el_feedin.sum()
    #annual_el_supply = hourly_el_supply.sum()

    #print(f"Electricity PV feed-in: {-annual_el_feedin/1000:.2f} kWh/a", end = ", ")
    #print(f"Electricity grid supply: {annual_el_supply/1000:.2f} kWh/a")

    # CO2 emissions
    spec_co2_gas = scenario.eco2_path['spec_CO2_gas [g/kWh]'].at[year]
    spec_co2_el = scenario.eco2_path['spec_CO2_el [g/kWh]'].at[year]

    #print(spec_co2_gas)
    co2_gas     = annual_system_results['Gas consumption [kwh/a]'] * spec_co2_gas / 1e6   # [tons]
    co2_el      = annual_system_results['Electricity grid supply [kWh/a]'] * spec_co2_el   / 1e6   # [tons]
    #print(f'{co2_gas=} {co2_el=}')
    co2_emissions = co2_gas + co2_el # total co2 emissions [tons]

    # balance
    CO2_budget = annual_results_last_year['CO2 Budget [t]'] - co2_emissions
    print(f"CO2 emissions: {co2_emissions:.2f} t/a", end = ", ")

    # ECONOMY
    # annual revenues and expenses
    revenues, expenses = user.calc() # [euro]

    # energy costs
    cost_gas = annual_system_results['Gas consumption [kwh/a]'] * scenario.eco2_path['cost_gas [ct/kWh]'].at[year]/100 # [euro]
    cost_el = annual_system_results['Electricity grid supply [kWh/a]'] * scenario.eco2_path['cost_el_hh [ct/kWh]'].at[year]/100 # [euro]
    energy_costs   = cost_gas + cost_el # total energy costs [euro]

    # balance
    balance = revenues - expenses - energy_costs
    bank_deposit = annual_results_last_year['Bank Deposit [Euro]'] + balance # [euro]
    print(f"Bank balance: {balance:.2f} euro/a")

    # COMFORT
    comfort_deviation = '=)'    # comfort deviation [-]
    
    return  CO2_budget, bank_deposit, comfort_deviation, annual_building_results, annual_system_results

# {'Building':annual_building_results, 'System':0, 'Eco2': 0 } 


''' !toDo simplify simulate .. outsource calculations, so that we only have to call a few functions

def simulate(init, user, building, system, scenario):
    
    annual_building_results, hourly_heatdemand = building.calc(user) # Series/reihe ['RH', 'TRANS_TOTAL', 'VENT', 'TRANS_ROOF', 'TRANS_WINDOW', 'SOLAR_GAINS', 'INTERAL_GAINS_APP',...]
    annual_system_results, annual_grid_interactions = system.calc(hourly_heatdemand, user) #Series/reihe ['GasBoiler': ['GasConsumption', 'FullLoadHours', 'Q_th'..], 'PV': ['Autarky', 'ElectricityProduction', 'Feedin', ], 'HeatPump': ['Q_th', 'E_el', 'FullLoadHours', 'El_from_PV', 'El_from_Storage', 'COP'] ]
    eco2_results = eco2.calc(annual_grid_interactions)
    results = [annual_building_results, annual_system_results, eco2_results]

    return results   
'''