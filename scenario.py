import pandas as pd

class Scenario:
    def __init__(self, eco2_paths_filepath):
        self.CO2_budget = 50 # [t]
        self.eco2_path = pd.read_csv(eco2_paths_filepath, index_col = "year") #"data/scenarios/Scenario.csv"