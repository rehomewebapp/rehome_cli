import pandas as pd

class Eco2:
    ''' Economic and ecological calculation, and parameters
    '''
    def __init__(self, eco2_paths_filepath):
        self.CO2_budget = 50 # [t]
        self.eco2_path = pd.read_csv(eco2_paths_filepath, index_col = "year") 