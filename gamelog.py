def calculate(user, ecology_results, economy_results, annual_results_last_year):
    # ECOLOGY
    CO2_budget = annual_results_last_year['CO2 Budget [t]'] - ecology_results["CO2 emissions [t]"]

    # ECONOMY
    bank_deposit = annual_results_last_year['Bank Deposit [Euro]'] + economy_results["Balance [Euro/a]"] # [euro]

    # COMFORT
    comfort_deviation = user.comfort_temperature - user.set_point_temperature    # comfort deviation [degC]
    if abs(comfort_deviation) < 1:
        comfort = "=)"
    elif abs(comfort_deviation) < 3:
        comfort = "=/"
    else:
        comfort = "=("
    

    return {"CO2 Budget [t]": CO2_budget, "Bank Deposit [Euro]": bank_deposit, "Comfort": comfort}