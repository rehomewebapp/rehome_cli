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

        self.profile = self.generate_profiles()
        self.event_economic_balance = 0
        self.bank_deposit = self.initial_bank_deposit

    def generate_profiles(self):
        # read hourly factors of normalized profile
        user_profile_norm = pd.read_csv("data/profiles/user_profile_norm.csv", index_col = "hour")

        df = pd.DataFrame(index = user_profile_norm.index)
        df['el_hh [W]'] = user_profile_norm['el_hh_norm'] * self.annual_el_demand * 1000 # [W]
        return df



    def calc_economy(self):
        annual_sallary = 13 * self.monthly_sallary # [Euro] including christmas bonus
        annual_costs = 12 * (self.monthly_living_cost + self.monthly_entertainment + self.monthly_loan_payoff) # [Euro]

        return annual_sallary, annual_costs
