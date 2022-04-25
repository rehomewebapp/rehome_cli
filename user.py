from datetime import datetime
import yaml
import pandas as pd
import numpy as np

class User:
    def __init__(self, user_path, verbose = False):
        # load user parameters from file
        with open(user_path, "r") as stream:
            try:
                user_params = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        for key, value in user_params.items():
            if verbose == True:
                print(f"    - {key}, {value}")
            setattr(self, key, value)

        self.co2_budget    = 50 # [tons] !ToDo move this to a file called scenarios.py

        self.profile = self.generate_profiles()

    def generate_profiles(self):
        # read hourly factors of normalized profile
        user_profile_norm = pd.read_csv("data/profiles/user_profile_norm.csv", index_col = "hour")

        df = pd.DataFrame(index = user_profile_norm.index)
        df['el_hh [W]'] = user_profile_norm['el_hh_norm'] * self.annual_el_demand * 1000 # [W]
        return df



    def calc(self):
        annual_sallary = 13 * self.monthly_sallary # [euro] including christmas bonus
        annual_costs = 12 * (self.monthly_living_cost + self.monthly_entertainment + self.monthly_loan_payoff) # [euro]

        return annual_sallary, annual_costs
