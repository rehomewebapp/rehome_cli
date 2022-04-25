
def calculate(year, user, building, system, scenario):
    # ECOLOGY
    # gas consumption
    hourly_heat_demand = building.calc(user.comfort_temperature) # Wh
    hourly_el_demand = user.profile['el_hh [W]']    # Wh 
    annual_el_hh  = hourly_el_demand.sum()    # Wh 
    
    hourly_used_gas, hourly_el_feedin, hourly_el_supply = system.calc(hourly_heat_demand, hourly_el_demand, building.weather) # Wh
    annual_used_gas = hourly_used_gas.sum()
    annual_el_feedin = hourly_el_feedin.sum()
    annual_el_supply = hourly_el_supply.sum()

    print(f"Annual heat demand: {hourly_heat_demand.sum()/1000:.2f} kWh/a", end = ", ")
    print(f"Electricity PV feed-in: {annual_el_feedin/1000:.2f} kWh/a", end = ", ")
    print(f"Electricity grid supply: {annual_el_supply/1000:.2f} kWh/a")

    # CO2 emissions
    spec_co2_gas = scenario['spec_CO2_gas [g/kWh]'].at[year]
    spec_co2_el = scenario['spec_CO2_el [g/kWh]'].at[year]

    #print(spec_co2_gas)
    co2_gas     = annual_used_gas/1000 * spec_co2_gas / 1e6   # [tons]
    co2_el      = annual_el_supply/1000 * spec_co2_el   / 1e6   # [tons]
    #print(f'{co2_gas=} {co2_el=}')
    co2_emissions = co2_gas + co2_el # total co2 emissions [tons]

    # balance
    user.co2_budget = user.co2_budget - co2_emissions
    print(f"CO2 emissions: {co2_emissions:.2f} t/a", end = ", ")

    # ECONOMY
    # annual revenues and expenses
    revenues, expenses = user.calc() # [euro]

    # energy costs
    cost_gas = annual_used_gas/1000 * scenario['cost_gas [ct/kWh]'].at[year]/100 # [euro]
    cost_el = annual_el_supply/1000 * scenario['cost_el_hh [ct/kWh]'].at[year]/100 # [euro]
    energy_costs   = cost_gas + cost_el # total energy costs [euro]

    # balance
    balance = revenues - expenses - energy_costs
    user.bank_deposit = user.bank_deposit + balance # [euro]
    print(f"Bank balance: {balance:.2f} euro/a")

    # COMFORT
    comfort_deviation = '=)'    # comfort deviation [-]

    return comfort_deviation