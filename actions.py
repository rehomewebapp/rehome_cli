import subprocess

import user
import building
import system

def renovate(building_path):
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
