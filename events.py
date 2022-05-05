import random
# These events can happen randomly during the obersvation period.

# add new event (the function name) to this list to register it.
events = ['nothing', 'inherit', 'nothing', 'sarscov', 'nothing', 'saharaSand', 'nothing', 'unemployed',
          'nothing', 'promotion', 'nothing', 'fridge'] 


def nothing(year, user, building, system, event_states):
    # The nothing happens event corresonds to a very boring year
    pass

def inherit(year, user, building, system, event_states):
    # This event adds money to your bank account
    heritage = random.randint(5,50) * user.monthly_sallary # [euro] 
    print(f"You inherit! Added {heritage} € to your bank account.")
    user.bank_deposit = user.bank_deposit + heritage

def sarscov(year, user, building, system, event_states):
    # This event increases the ventilation rate of your building

    # check if ventilation rate has to be reset
    if 'sarscov' in event_states:
        if year == event_states['sarscov']:
            building.ventilation_rate = building.ventilation_rate - 0.2
            print(f"Yeey, the pandemic is over. Resetting ventilation rate back to {building.ventilation_rate:.2} 1/h.")
            event_states.pop('sarscov', None) # remove event from event_states dictionary

        return

    print(f"Huugh yet another virus! Increasing the ventilation rate for two years: {building.ventilation_rate} 1/h -> {building.ventilation_rate + 0.2:.2} 1/h.")
    building.ventilation_rate = building.ventilation_rate + 0.2
    event_states['sarscov'] = year + 2

def saharaSand(year, user, building, system, event_states):
    # this event reduces the efficiency of the pv module

    # check if efficiency has to be reset
    if 'saharaSand' in event_states:
        if year == event_states['saharaSand']:
            system.Photovoltaic.efficiency_param = system.Photovoltaic.efficiency_param + 0.2
            print(f"Your PV modules are clean again. Resetting efficiency back to {system.Photovoltaic.efficiency_param}.")
            event_states.pop('saharaSand', None) # remove event from event_states dictionary
        return

    print(f"Wooow. Everything is covered by sand from Sahara desert - your PV modules operate with reduced efficiency for one year: {system.Photovoltaic.efficiency_param} -> {system.Photovoltaic.efficiency_param - 0.3:.2}")
    system.Photovoltaic.efficiency_param = system.Photovoltaic.efficiency_param - 0.2
    event_states['saharaSand'] = year + 1

def unemployed(year, user, building, system, event_states):
    # this event reduces the sallary

    # check if monthly sallary has to be reset
    if 'unemployed' in event_states:
        if year == event_states['unemployed']:
            user.monthly_sallary = user.monthly_sallary * 1.5
            print(f"Congratulations! You found a new job. Your monthly sallary is {user.monthly_sallary} euro.")
            event_states.pop('unemployed', None) # remove event from event_states dictionary
        return

    print(f"Unfortunately you've lost your job. You receive unemployment benefits in the amount of {0.5 * user.monthly_sallary} euro/month.")
    user.monthly_sallary = user.monthly_sallary * 0.5
    event_states['unemployed'] = year + random.randint(1,2)
    

def promotion(year, user, building, system, event_states):
    # this event increases the sallary

    # check if user is not unemployed in the simulated year
    if 'unemployed' not in event_states:
        promotion_factor = 1 + random.randint(5,25)/100
        print(f"Congratulations! You've been promoted. Your new monthly sallary increased from {user.monthly_sallary} euro to {user.monthly_sallary * promotion_factor} euro.")
        user.monthly_sallary = user.monthly_sallary * promotion_factor

def fridge(year, user, building, system, event_states):
    # This event reduces the electricity demand and uniquely removes money from the bank account
    cost = 500 # [euro] 
    print(f"Your refrigerator is broken. It is replaced by an energy-efficient one. You pay {cost} euro and your annual electricity demand is reduced from {user.annual_el_demand} kWh to {user.annual_el_demand - 100} kWh.")
    user.bank_deposit = user.bank_deposit - cost
    user.annual_el_demand = user.annual_el_demand - cost