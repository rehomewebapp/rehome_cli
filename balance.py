def calculate(ecology_results, economy_results, annual_results_last_year):
    # ECOLOGY
    CO2_budget = annual_results_last_year['CO2 Budget [t]'] - ecology_results["CO2 emissions [t]"]
    #print(f"CO2 emissions: {co2_emissions:.2f} t/a", end = ", ")

    # ECONOMY
    balance = economy_results["User revenues [euro/a]"] - economy_results["User expenses [euro/a]"] - economy_results["Energy cost [euro/a]"]
    bank_deposit = annual_results_last_year['Bank Deposit [Euro]'] + balance # [euro]
    #print(f"Bank balance: {balance:.2f} euro/a")

    # COMFORT
    comfort_deviation = '=)'    # comfort deviation [-]

    return {"CO2 Budget [t]": CO2_budget, "Bank deposit [euro]": bank_deposit, "Comfort": comfort_deviation}