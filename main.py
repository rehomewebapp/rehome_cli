# modules from pythons std library
import random     # used to draw a random event
import glob       # used to find available parameter files
import shutil     # used to create copies of the default parameter files
import subprocess # used to run the nano texteditor to edit config files from the cmd prompt
from pathlib import Path
from unittest import result

# these modules have to be installed (e.g. with pip)
import numpy as np
import pandas as pd
from ruamel.yaml import YAML # this version of pyyaml support dumping without loosing the comments in the .yaml file
yaml = YAML()

# modules you find in this directory
import utilities
import user
import building
import system
import actions
import events
import simulate
import scenario
import gamelog

# intro
print("Welcome to REhome!")
print("Try to reach the climate goals without going bankrupt or violating your comfort zone!")

# choose scenario
print("Choose the cost and emission scenario:")
my_scenario = scenario.Eco2("data/eco2_paths/Scenario.csv")
print("    - Default scenario (moderate increase of CO2 pricing) ")
#print(my_scenario.eco2_path.head())

# initalize results dataframe
initial_year = 2021
annual_results = pd.DataFrame(index = my_scenario.eco2_path.index)

# choose user
print("Choose your character:")
existing_users = glob.glob('data/users/*.yaml')
for cnt, user_path in enumerate(existing_users):
    user_filename = utilities.path_leaf(user_path) # we only need the filename, not the filepath
    user_name = user_filename.split(sep='.')[0] # get rid of the extension
    print(f'    - {user_name} ({cnt})')
selection = int(input(f'Selected Character: '))
user_path = existing_users[selection]
# if the user wants to create a new character ...
if Path(user_path) == Path('data/users/NewUser.yaml'):
    user_name = input("Give your new character a name: ")
    new_user_path = Path(f'data/users/{user_name}.yaml')
    # create a copy of the default user
    shutil.copy(Path('data/users/NewUser.yaml'), new_user_path)
    # write user name to user config file
    with open(new_user_path, "r") as stream:
        try:
            user_file = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    user_file['name'] = user_name
    with open(new_user_path, 'w') as f:
        yaml.dump(user_file, f)
    # let the user edit it's config file
    subprocess.call(['nano', new_user_path])
    user_path = new_user_path
else:
    #print(f"Loading user from {user_path}")
    pass

# create the user from the selected config file path
me = user.User(user_path)
print(f"Hello {me.name} :).", end = ' ')

# initalize user columns in results df
annual_results[['CO2 Budget [t]','Bank Deposit [Euro]', 'Comfort']] = np.nan
annual_results.at[initial_year, 'CO2 Budget [t]'] = my_scenario.CO2_budget
annual_results.at[initial_year, 'Bank Deposit [Euro]'] = me.bank_deposit
annual_results.at[initial_year, 'Comfort'] = " =) =) =)"

# Let's choose a building config in a simmilar manner
print('Please choose one of the following buildings:')
existing_buildings = glob.glob('data/buildings/*.yaml')
# print all available options
for cnt, building_path in enumerate(existing_buildings):
    # only print the filename, not the path
    building_filename = utilities.path_leaf(building_path)
    building_name = building_filename.split(sep='.')[0]
    print(f'   - {building_name} ({cnt})')
selection = int(input(f'Selected Building: '))
building_path = existing_buildings[selection]
# if the user wants to create a new building ...
if Path(building_path) == Path('data/buildings/NewBuilding.yaml'):
    building_name = input("Give your new building a name: ")
    new_building_path = Path(f'data/buildings/{building_name}.yaml')
    # create a copy of the default building
    shutil.copy(Path('data/buildings/NewBuilding.yaml'), new_building_path)
    # write building name to user config file
    with open(new_building_path, "r") as stream:
        try:
            building_file = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    building_file['name'] = building_name
    with open(new_building_path, 'w') as f:
        yaml.dump(building_file, f)

    # let the user edit the default building config file
    subprocess.call(['nano', new_building_path])
    building_path = new_building_path
else:
    #print(f"Loading parameters from {building_path}")
    pass

# create a instance of your building
my_building = building.Building(building_path, verbose = False)


# choose system configuration
my_system, system_path = actions.choose_system()

annual_results.to_csv('annual_results.csv')

# start REhoming...
event_states = {} # initalize event states, to store event information for durations longer than one year

win = True
year = initial_year+1 # start year
while year <= 2045: # end year
    user_input = '0'
    while user_input != '':
        user_input = input('Enter to Simulate next year; Renovate building (1); Improve the System (2); Change User Behaviour (3): ')
        if user_input == '1': # renovate building
            component_input = input("Select component: none (0), facade (1), roof (2), upper ceiling (3), groundplate (4), window (5): ")
            if component_input == '0': # none
                pass
            elif int(component_input) < 5:
                thickness_insulation = int(input("Additional insulation thickness [cm]: "))
                actions.insulate(my_building, component_input, thickness_insulation)
                input("Press any key to continue")
            elif component_input == '5': # window
                window_type = input("Select new window type: wood double-glazed (1), plastic insulating glass (2), alu/steel insulating glass (3): ")
                actions.change_windows(my_building, window_type)
                input("Press any key to continue")
                
        elif user_input == '2': # change system parameters
            system_input = input("Return (0), Change system (1), Improve current system (2): ")
            if system_input == '0': # return
                pass
            elif system_input == '1': # change system
                my_system, system_path = actions.choose_system()
            elif system_input == '2': # edit system
                print("Let's improve the System Performance!")
                my_system = actions.optimize(system_path)
        elif user_input == '3': # change user behaviour
            print("Let's change the user behaviour!")
            me = actions.adopt(user_path)

    # check if we have to reset one of the events
    if event_states != {}:
        #print(event_states)
        for key, value in list(event_states.items()): # list enforces a copy of dict - required to avoid removing changing size of dict while iterating over it
            getattr(events, key)(year, me, my_building, my_system, event_states)

    event_status = -1
    while event_status == -1:
        # draw random event
        event = random.choice(events.events)
        #print(f'Event: {event}')
        # call the random event and pass user, building (system) objects (so they can be changed by the event).
        event_status = getattr(events, event)(year, me, my_building, my_system, event_states)

    if event != 'nothing':
        input('Press any key to continue.')

    # simulate
    print(f'Year: {year}/45')
    annual_building_results, system_results, ecology_results, annual_economy_results, comfort_deviation = simulate.calculate(year, me, my_building, my_system, my_scenario)

    annual_system_results = system_results.sum()
    annual_ecology_results = ecology_results.sum()

    # calculate game log
    game_log = gamelog.calculate(annual_ecology_results, annual_economy_results, comfort_deviation, annual_results.loc[year-1]) #ToDo add parameters

    # append game_log dict to annual_results df  
    for key, value in game_log.items():
            annual_results.at[year, key] = value
    
    # append annual building/sytem/ecologic/economic results dicts to annual_results df
    dicts = [annual_building_results, annual_system_results, annual_ecology_results, annual_economy_results, comfort_deviation]
    for dict in dicts:
        if year == initial_year:
            annual_results = annual_results.join(pd.DataFrame([dict], index=[year]))
        else:
            for key, value in dict.items():
                annual_results.at[year, key] = value

    # write annual results to csv-file
    annual_results.to_csv('annual_results.csv')

    # print rewards
    ''' Co2 emissions, Co2 budget; Annual costs, Bank deposite, '''
    print(f"    CO2 emissions [t/a]  : {annual_ecology_results['CO2 emissions total [t]']:4.2f}", end=' ')
    print(f"    Bank balance [Euro/a]: {annual_economy_results['Balance [Euro/a]']:9.2f}", end=' ')
    print(f"    Comfort deviation [degC]: {comfort_deviation['Comfort deviation [degC]']:9.2f}\n")
 
    # print gamelog
    print(f"    CO2 budget [t]       : {game_log['CO2 Budget [t]']:4.2f}", end=' ')
    print(f"    Bank deposit [Euro]  : {game_log['Bank Deposit [Euro]']:9.2f}", end=' ')
    print(f"    Comfort status : {game_log['Comfort']}\n")

    # print detailed results
    user_input = '0'
    while user_input != '':
        user_input = input('Enter to continue; Show building results (1); Show system results (2); Show ecologic results (3); Show economic results (4) : ')
        if user_input == '1':
            for key, value in annual_building_results.items():
                print(f"{key} : {value}")
        if user_input == '2':
            for key, value in annual_system_results.items():
                print(f"{key} : {value}")
        if user_input == '3':
            for key, value in annual_ecology_results.items():
                print(f"{key} : {value}")
        if user_input == '4':
            for key, value in annual_economy_results.items():
                print(f"{key} : {value}")

    # start next year
    year = year + 1

    # game over
    if game_log["CO2 Budget [t]"] < 0:
        print('CO2 budget exceeded!')
        win = False
        break
    elif game_log["Bank Deposit [Euro]"] < 0:
        print('Bank account empty!', end = ' ')
        win = False
        break
    elif game_log['Comfort'] == "":
        print('Comfort violated!', end = ' ')
        win = False
        break

if win == True:
    print('Yaayy!! You made it. ')
else:
    print('GAME OVER =(')
