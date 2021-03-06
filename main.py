# modules from pythons std library
import random     # used to draw a random event
import glob       # used to find available parameter files
import shutil     # used to create copies of the default parameter files
import subprocess # used to run the nano texteditor to edit config files from the cmd prompt
from pathlib import Path

# these modules have to be installed (e.g. with pip)
import numpy as np
import pandas as pd
from ruamel.yaml import YAML # this version of pyyaml support dumping without loosing the comments in the .yaml file
yaml = YAML()

# modules you find in this directory
import utilities as util
import constants as c
import user
import building
import system
import actions
import events
import simulator
import scenario
import gamelog

util.clear_console()

# intro
print("Welcome to REhome!")
print("    Try to reach the climate goals without going bankrupt or violating your comfort zone!")

# choose scenario
#print("Choose the cost and emission scenario:")
my_scenario = scenario.Eco2("data/eco2_paths/Scenario.csv")
#print("    - Default scenario (moderate increase of CO2 pricing) ")
#print(my_scenario.eco2_path.head())
selection = input(f"\n    ENTER to continue: ")
util.clear_console()
# initalize results dataframe
initial_year = c.START_YEAR - 1 # initialization in year 2021
annual_results = pd.DataFrame(index = my_scenario.eco2_path.index)

# choose user
print("Choose a character or create a new one (0): ")
existing_users = glob.glob('data/users/*.yaml')
for cnt, user_path in enumerate(existing_users):
    user_filename = util.path_leaf(user_path) # we only need the filename, not the filepath
    user_name = user_filename.split(sep='.')[0] # get rid of the extension
    print(f"    - {user_name} '{cnt+1}'")
selection = int(input(f''))

# if the user wants to create a new character ...
if selection == 0:
    user_name = input("Give your new character a name: ")
    new_user_path = Path(f'data/users/{user_name}.yaml')
    # create a copy of the default user
    shutil.copy(Path('data/users/DefaultUser.yaml'), new_user_path)
    # write user name to user config file
    with open(new_user_path, "r") as stream:
        user_file = yaml.load(stream)
    user_file['name'] = user_name
    with open(new_user_path, 'w') as f:
        yaml.dump(user_file, f)
    # let the user edit it's config file
    subprocess.call(['nano', new_user_path])
    user_path = new_user_path
else:
    user_path = existing_users[selection-1]
    #print(f"Loading user from {user_path}")
    pass

# create the user from the selected config file path
me = user.User(user_path)
util.clear_console()
print(f"Hello {me.name} :).", end = ' ')

# initalize user columns in results df
annual_results[['CO2 Budget [t]','Bank Deposit [Euro]', 'Comfort']] = np.nan
annual_results.at[initial_year, 'CO2 Budget [t]'] = my_scenario.CO2_budget
annual_results.at[initial_year, 'Bank Deposit [Euro]'] = me.bank_deposit
annual_results.at[initial_year, 'Comfort'] = " =) =) =)"

# Let's choose a building config in a simmilar manner
util.clear_console()
print('Please choose one of the following buildings, or create your own (0):')
existing_buildings = glob.glob('data/buildings/*.yaml')
# print all available options
for cnt, building_path in enumerate(existing_buildings):
    # only print the filename, not the path
    building_filename = util.path_leaf(building_path)
    building_name = building_filename.split(sep='.')[0]
    print(f'   - {building_name} ({cnt+1})')
selection = int(input(''))
building_path = existing_buildings[selection-1]
# if the user wants to create a new building ...
if selection == 0:
    building_name = input("Give your new building a name: ")
    new_building_path = Path(f'data/buildings/{building_name}.yaml')
    # create a copy of the default building
    shutil.copy(Path('data/buildings/DefaultBuilding.yaml'), new_building_path)
    # write building name to user config file
    with open(new_building_path, "r") as stream:
        building_file = yaml.load(stream)
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

# calculate maximum heat load of the building
annual_building_results, hourly_heat_demand = my_building.calc(me)
heat_load_max = hourly_heat_demand.max()
my_building.heat_load_max = heat_load_max
print(f"Maximum heating load of your building: {my_building.heat_load_max/1000:.2f} kW")
input('    ENTER to continue:')

# choose system configuration
print("Please choose one of the following systems, or create your own (0):")
existing_systems = glob.glob('data/systems/*.yaml')
# print all available options
for cnt, system_path in enumerate(existing_systems):
    # only print the filename, not the path
    system_filename = util.path_leaf(system_path)
    system_name = system_filename.split(sep='.')[0]
    print(f'   - {system_name} ({cnt+1})')
selection = int(input(''))
#
system_path = existing_systems[selection-1]

if selection == 0:
    my_system = actions.generate_system(me, my_building)
else:
    my_system = system.System(system_path)

annual_results.to_csv('annual_results.csv')

# initalize the simulator
my_simulator = simulator.Simulator(me, my_building, my_system, my_scenario)

# start REhoming...
event_states = {} # initalize event states, to store event information for durations longer than one year

win = True
year = c.START_YEAR # initialize with start year 2022
while year <= c.END_YEAR: # end year
    user_input = '0'
    while user_input != '':
        util.clear_console()
        user_input = input('ENTER to Simulate next year; Renovate building (1); Edit System (2); Change User Behaviour (3): ')
        if user_input == '1': # renovate building
            component_input = input("Select component: none (0), facade (1), roof (2), upper ceiling (3), groundplate (4), window (5): ")
            if component_input == '0': # none
                pass
            elif int(component_input) < 5:
                thickness_insulation = int(input("Additional insulation thickness [cm]: "))
                actions.insulate(my_building, component_input, thickness_insulation)
                input("    ENTER to continue")
            elif component_input == '5': # window
                window_type = input("Select new window type: wood double-glazed (1), plastic insulating glass (2), alu/steel insulating glass (3): ")
                actions.change_windows(my_building, window_type)
                input("    ENTER to continue")
                
        elif user_input == '2': # change system parameters
            # aks user if he wants to add or remove a component
            usr_input = -1
            while usr_input not in [0,1]:
                usr_input = int(input('Return (0), Add component (1), Remove component (2): '))
                if usr_input == 0:
                    break
                if usr_input == 1:
                    my_system = actions.add_system_component(me, my_building, my_system, year)
                elif usr_input == 2:
                    my_system = actions.delete_system_component(my_building, my_system)
                else:
                    print('Invalid input!')

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
        input("    ENTER to continue: ")

    # simulate
    results = my_simulator.simulate_year(year)
    annual_building_results = results['building']
    annual_system_results = results['system'].sum()
    annual_ecology_results = results['ecology'].sum()
    annual_economy_results = results['economy'].sum()
    comfort_deviation = results['comfort'] # !ToDo use actual room temperature for calculation of comfort deviation -> return hourly values


    # calculate game log
    game_log = gamelog.calculate(annual_ecology_results, annual_economy_results, comfort_deviation, annual_results.loc[year-1]) #ToDo add parameters

    # update user
    me.bank_deposit = game_log['Bank Deposit [Euro]']


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
    util.clear_console()
    print(f'Year: {year}/45')
    ''' Co2 emissions, Co2 budget; Annual costs, Bank deposite, '''
    print(f"    CO2 emissions [t/a]  : {annual_ecology_results['CO2 emissions total [t]']:5.2f}", end=' ')
    print(f"    Bank balance [Euro/a]: {annual_economy_results['Balance [Euro/a]']:9.2f}", end=' ')
    print(f"    Comfort deviation [degC]: {comfort_deviation['Comfort deviation [degC]']:9.2f}")
 
    # print gamelog
    print(f"    CO2 budget [t]       : {game_log['CO2 Budget [t]']:5.2f}", end=' ')
    print(f"    Bank deposit [Euro]  : {game_log['Bank Deposit [Euro]']:9.2f}", end=' ')
    print(f"    Comfort status : {game_log['Comfort']}\n")

    # print detailed results
    user_input = '0'
    while user_input != '':
        
        #print("Building results (1); System results (2); Ecologic results (3); Economic results (4) : ")
        if user_input == '1': 
            util.clear_console()
            print('Detailed Building Results:')
            for key, value in annual_building_results.items():
                print(f"    {key.split('[')[0]: <30} : {value:>15.2f} [{key.split('[')[1]: <6}") # seperate key into 'name' and 'unit', align output with <^>, edit precision with .2f
            #user_input = input('    ENTER to continue; Show building results (1); Show system results (2); Show ecologic results (3); Show economic results (4) : ')
        if user_input == '2':
            util.clear_console()
            print('Detailed System Results:')
            for key, value in annual_system_results.items():
                print(f"    {key.split('[')[0]: <30} : {value/1000:>15.2f} [k{key.split('[')[1]: <6}")
        if user_input == '3':
            util.clear_console()
            print('Detailed Ecology Results:')            
            for key, value in annual_ecology_results.items():
                print(f"    {key.split('[')[0]: <30} : {value:>15.2f} [{key.split('[')[1]: <6}")
        if user_input == '4':
            util.clear_console()      
            print('Detailed Economy Results:')
            for key, value in annual_economy_results.items():
                print(f"    {key.split('[')[0]: <30} : {value:>15.2f} [{key.split('[')[1]: <6}")
        print("\nBuilding results (1); System results (2); Ecologic results (3); Economic results (4) : ")  
        user_input = input('    ENTER to continue: ')

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
