import subprocess
import glob       # used to find available parameter files
import pandas as pd
import shutil     # used to create copies of the default parameter files
from pathlib import Path
from ruamel.yaml import YAML # this version of pyyaml support dumping without loosing the comments in the .yaml file
yaml = YAML()

import user
import utilities as util
import constants as c
import building
import system

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

def configure_system(year, user_name):
    '''
    Parameters
    ---------
    year: int
        current year - used to set construction year of PV system
    user_name: str
        used to name the configured file
    Returns
    -------
    str
        new file path for the configured system yaml-file
    '''
    util.clear_console()
    # chosse heat generation system
    heat_input = input("Please choose your heat generation system: GasBoiler (1), HeatPumpAir (2) : ")
    if heat_input == '1':
        heat_selection = 'GasBoiler'
    elif heat_input == '2':
        heat_selection = 'HeatPumpAir'
    # input nominal power of heating system
    power_heat = float(input(f"Please input the nominal power of the {heat_selection} in kW : "))
    heat_system_path = Path('data/systems/' + heat_selection + '.yaml')
    # ToDo add recommendation based on max bldg heating load * 1.1 safety factor
    system_name = user_name + "'s_" + heat_selection
    
    el_selection = "" # initialization
    el_input = input("Do you want to add a PV system? no (0), yes (1) : ")
    if el_input == '1':
        # ToDo generalize adding PV for all heat generation systems, not only for GasBoiler
        if heat_input == '2':
            print("The combination of HeatPump and PV is not yet implemented. =( ")
        else:
            el_selection = 'PV'
            print("Please specify the parameters of your PV system:")
            if year == c.START_YEAR-1: # during system initialization
                construction_year = int(input("Year of construction : "))
                feedin_tariff = float(input("Feed-in tariff in ct/kWh : "))
            else: # during game
                construction_year = year
            power_pv = float(input("Nominal power in kW : "))
            tilt_angle = float(input("Tilt angle (0 : horizontal, 90 : vertical) in deg : "))
            orientation_input = input("Orientation (S,SW,W,NW,N,NE,E,SE) : ")
            azimuth_angles = {'S':0, 'SW':45, 'W':90, 'NW':135, 'N':180, 'NE':-135, 'E':-90, 'SE':-45 }
            azimuth_angle = azimuth_angles[orientation_input]
            el_system_path = Path('data/systems/' + el_selection + '.yaml')
            system_name += '_' + el_selection

    new_system_path = Path('data/systems/configured/' + system_name + '.yaml')

    # create a copy of the heat system
    shutil.copy(heat_system_path, new_system_path)
    with open(new_system_path, "r") as stream:
        system_file = yaml.load(stream)
    # set name of system
    #system_file['name'] = system_name
    # set nominal power of heating system
    system_file[heat_selection]['power_nom'] = power_heat

    # if pv system is selected:
    if el_selection == 'PV':
        with open(el_system_path, "r") as stream:
            el_file = yaml.load(stream)
        system_file['Photovoltaic'] = el_file['Photovoltaic']
        system_file['Photovoltaic']['power_nom'] = power_pv
        system_file['Photovoltaic']['tilt_angle'] = tilt_angle
        system_file['Photovoltaic']['azimuth_angle'] = azimuth_angle
        system_file['Photovoltaic']['construction_year'] = construction_year
        if year == c.START_YEAR-1: # during system initialization
            system_file['Photovoltaic']['feedin_tariff'] = feedin_tariff
    with open(new_system_path, 'w') as f:
        yaml.dump(system_file, f)
    
    return new_system_path

def optimize(system_path):
    # edit parameters
    subprocess.call(['nano', system_path])
    new_system = system.System(system_path)
    return new_system


def adopt(user_path):
    # change user behaviour
    subprocess.call(['nano', user_path])
    print('Behaviour adopted!')
    new_user = user.User(user_path)
    return new_user



if __name__ == "__main__":
    pass
