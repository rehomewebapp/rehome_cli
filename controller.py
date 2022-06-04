

class Ctrl_GasBoiler():
    
    def control(self, Qdot_heat_load, P_el_hh, system):
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
