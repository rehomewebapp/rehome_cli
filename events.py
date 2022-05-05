import random
# These events can happen randomly during the obersvation period.

# add new event (the function name) to this list to register it.
events = ['nothing', 'inherit', 'nothing', 'sarscov', 'nothing', 'saharaSand'] 


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
            print(f"Yeey, the pandemic is over. Resetting ventilation rate back to {building.ventilation_rate} 1/h.")
            event_states.pop('sarscov', None) # remove event from event_states dictionary

        return

    print(f"Huugh yet another virus! Increasing the ventilation rate for two years: {building.ventilation_rate} 1/h -> {building.ventilation_rate + 0.2:.2} 1/h.")
    building.ventilation_rate = building.ventilation_rate + 0.2
    event_states['sarscov'] = year + 2

def saharaSand(year,user, building, system, event_states):
    # this event reduces the efficiency of the pv module
    if 'saharaSand' in event_states:
        if year == event_states['saharaSand']:
            system.Photovoltaic.efficiency_param = system.Photovoltaic.efficiency_param + 0.2
            print(f"Your PV modules are clean again. Resetting efficiency back to {system.Photovoltaic.efficiency_param}")
        return

    print(f"Wooow. Everything is covered by sand from Sahara desert - your PV modules operate with reduced efficiency for one year: {system.Photovoltaic.efficiency_param} -> {system.Photovoltaic.efficiency_param - 0.3:.2}")
    system.Photovoltaic.efficiency_param = system.Photovoltaic.efficiency_param - 0.2
    event_states['saharaSand'] = year + 1