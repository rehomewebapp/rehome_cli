import subprocess
import glob       # used to find available parameter files
import pandas as pd
import yaml

import user
import utilities as util
import constants as c
from system import *

def add_system_component(user, building, system, year):
    ''' This function adds a component to the given system'''
    # which component to add?
    print("Please choose the component you want to add: ")
    available_components = glob.glob('data/systems/components/*.yaml')
    # print all available options
    for cnt, component_path in enumerate(available_components):
        # only print the filename, not the path
        component_filename = util.path_leaf(component_path)
        component_name = component_filename.split(sep='.')[0]
        print(f'   - {component_name} ({cnt+1})')
    selection = int(input(''))

    component_path = available_components[selection - 1]

    # create component
    with open(component_path, "r") as stream:
        component_file = yaml.safe_load(stream)

    params = list(component_file.items())[0][1] # extract single value from dict
    constructor =  globals()[params['type']] # create reference to component class
    my_component = constructor(params)

    # configure component (not yet implemented)
    my_component.configure(year)

    # dont calc invest for system generation
    if year >= c.START_YEAR:
        # calc cost of new component
        investment_cost = my_component.calc_investment_cost()

        # check if the user has enough money
        if user.check_solvency(investment_cost):
            # ask user if he wants to purchase
            user_input = input(f"ENTER to purchase {my_component.name} system for {investment_cost:.2f} Euro, (0) to reject: ")
            if user_input == '0':
                return system
        else:
            print(f"You don't have enough money! \n    {my_component.name} : {investment_cost:.2f} Euro < {user.bank_deposit:.2f} Euro : Bank deposit")
            return system

    # Give name to new component
    usr_input = input('Give your new component a name: ')
    my_component.name = usr_input

    # add component to system obj
    system.components[my_component.name] = my_component

    # dont calc invest for system generation
    if year >= c.START_YEAR:
        # add investment cost to economic balance
        user.action_economic_balance += investment_cost

    # write system configuration to yaml
    system_path = f'data/systems/{building.name}'
    for component_name in system.components.keys():
        system_path += ('_' + component_name)
    system.write_yaml(system_path + '.yaml')
    
    return system

def delete_system_component(building, system):
    # list available components
    print("Please choose the component you want to delete: ")
    print('   - None (0)')
    existing_components = []
    for cnt, component in enumerate(system.components.items()):
        # print all available options
        print(f'   - {component[0]} ({cnt+1})')
        existing_components.append(component[0])

    # select component to delete
    selection = int(input(''))
    if selection == 0:
        return system

    # remove component from system object
    system.components.pop(existing_components[selection-1], None)

    print(f'Removed {existing_components[selection-1]} from system.')

    # write system configuration to yaml
    system_path = f'data/systems/{building.name}'
    for component_name in system.components.keys():
        system_path += ('_' + component_name)
    system.write_yaml(system_path + '.yaml')
    return system

def insulate(building, component, thickness):
    components = {'1' : 'facade', '2' : 'roof', '3' : 'upper_ceiling', '4' : 'groundplate'}
    old_u_value = getattr(building, f'u_value_{components[component]}')
    new_u_value = 1 / (1 / old_u_value + thickness/100 /0.04) # [W/(m^2K)]
    print(f"{components[component]} renovated: u-value {old_u_value:.2f} -> {new_u_value:.2f} W/(m^2K)")
    setattr(building, f"u_value_{components[component]}", new_u_value)
    #print(f"u_value_{components[component]} = {getattr(building, f'u_value_{components[component]}')}")
    
def change_windows(building, type):
    # wood double-glazed (1), plastic insulating glass (2), alu/steel insulating glass (3)
    types = {'1' : 'window_wood_double-glazed', '2' : 'window_plastic_iso', '3' : 'window_metal_iso'}
    u_values = pd.read_csv("data/components/u_values.csv", index_col = "bac").iloc[-1] # use u-values of latest building age class
    new_u_value = u_values[types[type]]
    print(f"Windows exchanged: u-value {building.u_value_window:.2} -> {new_u_value} W/(m^2K)")
    building.u_value_window = new_u_value

def generate_system(user, building):
    '''
    Parameters
    ---------
    user: instance of User object
        not used but required for add_system_component fct
    building: instance of Building object
        used to give recommendation for system dimensioning
    Returns
    -------
    instance of System object
        new System
    '''
    util.clear_console()
    inital_year = c.START_YEAR - 1

    # initalize empty system
    system = System('')
    # add component
    usr_input = ''
    while usr_input != '0':
        system = add_system_component(user, building, system, inital_year)
        usr_input = input('ENTER to add another component, (0) to finish: ')
    return system

def adopt(user_path):
    # change user behaviour
    subprocess.call(['nano', user_path])
    print('Behaviour adopted!')
    new_user = user.User(user_path)
    return new_user

if __name__ == "__main__":
    pass
