import random
import cowsay

import utilities as util
# These events can happen randomly during the obersvation period.

# add new event (the function name) to this list to register it.

events = ['nothing', 'inherit', 'nothing', 'sarscov', 'nothing', 'saharaSand', 'nothing', 'unemployed',
          'nothing', 'promotion', 'nothing', 'fridge', 'nothing', 'gasBoilerAging', 
          'nothing', 'coldYear', 'nothing', 'homeOffice', 'nothing', 'sealingTape'] 

#events = ['inherit']

def nothing(year, user, building, system, event_states):
    # The nothing happens event corresonds to a very boring year
    pass

def inherit(year, user, building, system, event_states):
    # This event adds money to your bank account
    heritage = random.randint(5,50) * user.monthly_sallary # [Euro] 
    user.event_economic_balance += heritage
    util.clear_console()
    cowsay.cow(f"You inherit! Added {heritage} € to your bank account.")

def sarscov(year, user, building, system, event_states):
    # This event increases the ventilation rate of your building
    delta_ventilation = 0.2
    duration = random.randint(1,3)

    # check if ventilation rate has to be reset
    if 'sarscov' in event_states:
        if year == event_states['sarscov']:
            building.ventilation_rate = building.ventilation_rate - delta_ventilation
            print(f"Yeey, the pandemic is over. Resetting ventilation rate back to {building.ventilation_rate:.2} 1/h.")
            input('ENTER to continue.')
            event_states.pop('sarscov', None) # remove event from event_states dictionary

        return

    print(f"Huugh yet another virus! Increasing the ventilation rate: {building.ventilation_rate:.2} 1/h -> {building.ventilation_rate + delta_ventilation:.2} 1/h.")
    building.ventilation_rate = building.ventilation_rate + delta_ventilation
    event_states['sarscov'] = year + duration

def saharaSand(year, user, building, system, event_states):
    if 'Photovoltaic' not in system.components:
        return -1
    # this event reduces the efficiency of the pv module
    delta_efficiency = 0.2

    # check if efficiency has to be reset
    if 'saharaSand' in event_states:
        if year == event_states['saharaSand']:
            system.components['Photovoltaic'].efficiency_param += delta_efficiency
            print(f"Your PV modules are clean again. Resetting efficiency back to {system.components['Photovoltaic'].efficiency_param}.")
            input('ENTER to continue.')
            event_states.pop('saharaSand', None) # remove event from event_states dictionary
        return

    print(f"Wooow. Everything is covered by sand from Sahara desert - your PV modules operate with reduced efficiency for one year: {system.components['Photovoltaic'].efficiency_param} -> {system.components['Photovoltaic'].efficiency_param - delta_efficiency:.2}")
    system.components['Photovoltaic'].efficiency_param = system.components['Photovoltaic'].efficiency_param - delta_efficiency
    event_states['saharaSand'] = year + 1

def unemployed(year, user, building, system, event_states):
    # this event reduces the sallary
    benefit_rate = 0.5

    # check if monthly sallary has to be reset
    if 'unemployed' in event_states:
        if year == event_states['unemployed']:
            user.monthly_sallary = user.monthly_sallary * (1 + benefit_rate)
            print(f"Congratulations! You found a new job. Your monthly sallary is {user.monthly_sallary} euro.")
            input('ENTER to continue.')
            event_states.pop('unemployed', None) # remove event from event_states dictionary
        return

    print(f"Unfortunately you've lost your job. You receive unemployment benefits in the amount of {benefit_rate * user.monthly_sallary} euro/month.")
    user.monthly_sallary = user.monthly_sallary * benefit_rate
    event_states['unemployed'] = year + random.randint(1,2)
    

def promotion(year, user, building, system, event_states):
    # this event increases the sallary

    # check if user is not unemployed in the simulated year
    if 'unemployed' not in event_states:
        promotion_factor = 1 + random.randint(5,25)/100
        print(f"Congratulations! You've been promoted. Your new monthly sallary increased from {user.monthly_sallary:.2f} euro to {user.monthly_sallary * promotion_factor:.2f} euro.")
        user.monthly_sallary = user.monthly_sallary * promotion_factor

def fridge(year, user, building, system, event_states):
    # This event reduces the electricity demand and uniquely removes money from the bank account
    cost = 500 # [Euro] 
    delta_el = 100 # [kWh/a]
    print(f"Your refrigerator is broken. It is replaced by an energy-efficient one. You pay {cost} euro and your annual electricity demand is reduced from {user.annual_el_demand} kWh to {user.annual_el_demand - delta_el} kWh.")
    user.event_economic_balance -= cost # [Euro]
    user.annual_el_demand = user.annual_el_demand - delta_el

def gasBoilerAging(year, user, building, system, event_states):
    if 'GasBoiler' not in system.components:
        return -1
    # this event reduces the gas boiler efficiency for one year and creates cost after one year
    delta_efficiency = 0.1

    # check if efficiency has to be reset
    if 'gasBoilerAging' in event_states:
        if year == event_states['gasBoilerAging']:
            cost = 1000 # [Euro]
            system.components['GasBoiler'].efficiency += delta_efficiency
            user.event_economic_balance -=  cost # [Euro]
            print(f"A mechanic repairs your gas boiler for {cost} euro. Resetting efficiency back to {system.components['GasBoiler'].efficiency}.")
            input('ENTER to continue.')
            event_states.pop('gasBoilerAging', None) # remove event from event_states dictionary
        return

    print(f"Uh-oh! The efficiency of the gas boiler drops from {system.components['GasBoiler'].efficiency} to {system.components['GasBoiler'].efficiency-delta_efficiency:.2} due to aging effects.")
    system.components['GasBoiler'].efficiency -= delta_efficiency
    event_states['gasBoilerAging'] = year + random.randint(1,2)

'''
def balconyPV(year, user, building, system, event_states):
    # this event increases your installed PV power
    delta_power = 0.6

    print(f"Happy Birthday! Your friends surprise you with a balcony power plant. Your installed PV power increases: {system.components['Photovoltaic'].power_nom} kWp -> {system.components['Photovoltaic'].power_nom + delta_power:.2} kWp")
    system.components['Photovoltaic'].power_nom = system.components['Photovoltaic'].power_nom + delta_power
'''

def coldYear(year, user, building, system, event_states):
    # this event increases the set point and comfort temperature (instead of the ambient temperature) for one year
    temp_amb_drop = 3 # [degC]

    # check if temperature has to be reset
    if 'coldYear' in event_states:
        if year == event_states['coldYear']:
            user.comfort_temperature = user.comfort_temperature - temp_amb_drop
            user.set_point_temperature = user.set_point_temperature - temp_amb_drop
            print(f"Ambient temperature back at normal level.")
            input('ENTER to continue.')
            event_states.pop('coldYear', None) # remove event from event_states dictionary
        return

    print(f"Brrr. It's cold out there. This year the ambient temperature is in average {temp_amb_drop} degC cooler than usual.")
    user.comfort_temperature = user.comfort_temperature + temp_amb_drop
    user.set_point_temperature = user.set_point_temperature + temp_amb_drop
    event_states['coldYear'] = year + 1

def homeOffice(year, user, building, system, event_states):
    # this event increases the set point temperature and the electricity demand
    delta_temp = 2 #[degC]
    delta_el = 500 # [kWh/a]

    # check if temperatures and annual electricity demand has to be reset
    if 'homeOffice' in event_states:
        if year == event_states['homeOffice']:
            user.comfort_temperature = user.comfort_temperature - delta_temp
            user.set_point_temperature = user.set_point_temperature - delta_temp
            user.annual_el_demand = user.annual_el_demand - delta_el
            print(f"Back to office. Annual electricity demand and set point temperature back to {user.annual_el_demand} kWh and {user.comfort_temperature} degC.")
            input('ENTER to continue.')
            event_states.pop('homeOffice', None) # remove event from event_states dictionary
        return
    
    duration = random.randint(1,3)
    print(f"You work in homeoffice for {duration} years. Your annual electricity demand such as comfort and set point temperature of your heating system increase: {user.annual_el_demand} kWh -> {user.annual_el_demand + delta_el} kWh and {user.comfort_temperature} degC -> {user.comfort_temperature + delta_temp} degC")
    user.comfort_temperature = user.comfort_temperature + delta_temp
    user.set_point_temperature = user.set_point_temperature + delta_temp
    user.annual_el_demand = user.annual_el_demand + delta_el
    event_states['homeOffice'] = year + duration

def sealingTape(year, user, building, system, event_states):
    # this event reduces the infiltration rate
    delta_infiltration = 0.1
    print(f"A friend applies sealing tape at your windows. Your infiltration rate drops: {building.infiltration_rate} -> {building.infiltration_rate - delta_infiltration:.2}")
    building.infiltration_rate = building.infiltration_rate - delta_infiltration