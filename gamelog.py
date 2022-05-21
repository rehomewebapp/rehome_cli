def calculate(ecology_results, economy_results, comfort_deviation, annual_results_last_year):
    # ECOLOGY
    CO2_budget = annual_results_last_year['CO2 Budget [t]'] - ecology_results["CO2 emissions total [t]"]

    # ECONOMY
    bank_deposit = annual_results_last_year['Bank Deposit [Euro]'] + economy_results["Balance [Euro/a]"] # [Euro]

    # COMFORT
    comfort = annual_results_last_year["Comfort"]
    if abs(comfort_deviation["Comfort deviation [degC]"]) > 2:
        comfort = comfort[:-3]

    return {"CO2 Budget [t]": CO2_budget, "Bank Deposit [Euro]": bank_deposit, "Comfort": comfort}