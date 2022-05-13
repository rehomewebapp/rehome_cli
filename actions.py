import subprocess
import pandas as pd

import user
import building
import system

def insulate(building, component, thickness):
    components = {'1' : 'facade', '2' : 'roof', '3' : 'upper_ceiling', '4' : 'groundplate'}
    old_u_value = getattr(building, f'u_value_{components[component]}')
    new_u_value = 1 / (1 / old_u_value + thickness/10 /0.04) # [W/(m^2K)]
    print(f"{components[component]} renovated: u-value {old_u_value:.2f} -> {new_u_value:.2f} W/(m^2K)")
    setattr(building, f"u_value_{components[component]}", new_u_value)
    #print(f"u_value_{components[component]} = {getattr(building, f'u_value_{components[component]}')}")
    
def change_windows(building, type):
    # wood double-glazed (1), plastic insulating glass (2), alu/steel insulating glass (3)
    types = {'1' : 'window wood double-glazed', '2' : 'window plastic iso', '3' : 'window metal iso'}
    u_values = pd.read_csv("data/components/u_values.csv", index_col = "bac").iloc[-1] # use u-values of latest building age class
    new_u_value = u_values[types[type]]
    print(f"Windows exchanged: u-value {building.u_value_window:.2} -> {new_u_value} W/(m^2K)")
    building.u_value_window = new_u_value

def edit_bldg_params(building_path):
    # edit building parameters
    subprocess.call(['nano', building_path])
    # create new building after editing is done ...
    # !ToDo we have to run some tests here to make sure the user did a valid renovation 
    #      (e.g no geometry changed..., physical parameters within bounds ...)
    # !ToDo calculate the costs for the renovation
    new_building = building.Building(building_path)
    print('Renovation done! - Please note that the expenses of your renovation are not yet considered. Everything for free :)')
    return new_building

def optimize(system_path):
    # add/delete new system or edit parameters
    subprocess.call(['nano', system_path])
    new_system = system.System(system_path)
    print('System improved! - Please not that the expenses of your system optimization are not yet considered. Everything for free :)')
    return new_system


def adopt(user_path):
    # change user behaviour
    subprocess.call(['nano', user_path])
    print('Behaviour adopted!')
    new_user = user.User(user_path)
    return new_user



if __name__ == "__main__":
    pass
