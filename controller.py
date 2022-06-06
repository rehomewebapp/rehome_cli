
def select_controller(system):
    available_components = []
    for component, params in system.components.items():
        # find gas boiler, note only the last component with type gasboiler will be used!
        if params.type == 'GasBoiler':
            available_components.append('GasBoiler')
        if params.type == 'Photovoltaic':
            available_components.append('Photovoltaic')

        if 'Photovoltaic' in available_components:
            controller = Ctrl_PV()
        if 'GasBoiler' in available_components:
            controller = Ctrl_GasBoiler()
        if 'Photovoltaic' in available_components and 'GasBoiler' in available_components:
            controller = Ctrl_GasBoiler_PV()
            break

    return controller


class Ctrl_GasBoiler():
    
    def control(self, Qdot_heat_load, P_el_hh, disturbances, system):
        # HEAT BALANCE
        # find gas boiler, note only the last component with type gasboiler will be used!
        for component, params in system.components.items():
            if params.type == 'GasBoiler':
                gasboiler = system.components[component]

        # find nominal power of gas boiler
        power_nom = gasboiler.power_nom * 1000 # [W]

        # check if heat load can be covered
        if power_nom < Qdot_heat_load:
            Qdot_heat_actual = power_nom
            Qdot_heat_uncovered = Qdot_heat_load - Qdot_heat_actual
        else:
            Qdot_heat_actual = Qdot_heat_load
            Qdot_heat_uncovered = 0

        # write results to dict
        res = {gasboiler.heat : Qdot_heat_actual, "Uncovered heat [Wh]" : Qdot_heat_uncovered}

        # !ToDo calc comfort deviation from uncovered heat
        # T_comfort_dev = bldg.calc_comfort_dev(Qdot_heat_actual)

        # ENERGY
        used_gas = gasboiler.calc_energy(Qdot_heat_actual) 
        res[gasboiler.energy] = used_gas

        # ELECTRICITY BALANCE
        P_el_grid_hh = P_el_hh
        res["Electricity grid household [Wh]"] = P_el_grid_hh

        return res

class Ctrl_PV():
    def control(self, Qdot_heat_load, P_el_hh, disturbances, system):
        # HEAT BALANCE
        Qdot_heat_uncovered = Qdot_heat_load
        # write results to dict
        res = {"Uncovered heat [Wh]" : Qdot_heat_uncovered}

        # !ToDo calc comfort deviation from uncovered heat
        # T_comfort_dev = bldg.calc_comfort_dev(Qdot_heat_actual)

        # ENERGY
        # find PV system, note only the last component with type Photovoltaic will be used!
        for component, params in system.components.items():
            if params.type == 'Photovoltaic':
                pv_system = system.components[component]

        P_el_pv_prod = pv_system.calc_energy(disturbances) 
        res[pv_system.energy] = P_el_pv_prod

        # ELECTRICITY BALANCE
        P_el_grid_hh = P_el_hh - P_el_pv_prod
        P_pv_feedin = 0
        if P_el_grid_hh < 0:
            P_el_pv_prod_excess = -P_el_grid_hh
            P_pv_feedin = P_el_pv_prod_excess
            P_el_grid_hh = 0
        res["Electricity PV feedin [Wh]"] = P_pv_feedin
        res["Electricity grid household [Wh]"] = P_el_grid_hh

        return res

class Ctrl_GasBoiler_PV():
    def control(self, Qdot_heat_load, P_el_hh, disturbances, system):
        # HEAT BALANCE
        # find gas boiler, note only the last component with type gasboiler will be used!
        for component, params in system.components.items():
            if params.type == 'GasBoiler':
                gasboiler = system.components[component]

        # find nominal power of gas boiler
        power_nom = gasboiler.power_nom * 1000 # [W]

        # check if heat load can be covered
        if power_nom < Qdot_heat_load:
            Qdot_heat_actual = power_nom
            Qdot_heat_uncovered = Qdot_heat_load - Qdot_heat_actual
        else:
            Qdot_heat_actual = Qdot_heat_load
            Qdot_heat_uncovered = 0

        # !ToDo calc comfort deviation from uncovered heat
        # T_comfort_dev = bldg.calc_comfort_dev(Qdot_heat_actual)

        # write results to dict
        res = {gasboiler.heat : Qdot_heat_actual, "Uncovered heat [Wh]" : Qdot_heat_uncovered}

        # ENERGY
        used_gas = gasboiler.calc_energy(Qdot_heat_actual) 
        res[gasboiler.energy] = used_gas

        # find PV system, note only the last component with type Photovoltaic will be used!
        for component, params in system.components.items():
            if params.type == 'Photovoltaic':
                pv_system = system.components[component]

        P_el_pv_prod = pv_system.calc_energy(disturbances) 
        res[pv_system.energy] = P_el_pv_prod

        # ELECTRICITY BALANCE
        P_el_grid_hh = P_el_hh - P_el_pv_prod
        P_pv_feedin = 0
        if P_el_grid_hh < 0:
            P_el_pv_prod_excess = -P_el_grid_hh
            P_pv_feedin = P_el_pv_prod_excess
            P_el_grid_hh = 0
        res["Electricity PV feedin [Wh]"] = P_pv_feedin
        res["Electricity grid household [Wh]"] = P_el_grid_hh

        return res