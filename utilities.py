import ntpath
import json
from pathlib import Path

import requests
import pandas as pd

def path_leaf(path):
    # return the filename, given a filepath
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def get_tmy_data(latitude, longitude):
    """Load weather - typical meterological year(TMY) data from PVGIS
    Parameters
    ----------
    latitude : float
        Latitude [decimal degrees]
    longitude : float
        Longitude [decimal degrees]
    Returns
    -------
    content of the requests.response object containing weather data
    """
    url = 'https://re.jrc.ec.europa.eu/api/tmy?lat='+str(latitude)+'&lon='+str(longitude)+'&outputformat=json'
    response = requests.get(url)
    return response.content

def save_tmy_data(data, filepath):
    """Save the weather data in a json file.
    Parameters
    ----------
    data : content of the requests.response object
        content of the requests.response object containing weather data
    filepath : pathlib Path
        filepath where the json file should be saved
    """
    Path(filepath).write_bytes(data)


def read_tmy_data(filepath):
    """Read the weather data from a json file and write to pandas dataframe.
    Parameters
    ----------
    filepath : pathlib Path
        filepath where the json file is saved
    Returns
    -------
    pandas df containing
    - time (index, datetime): Date & time (UTC)
    - T2m (pandas column, float): Dry bulb (air) temperature [°C]
    - G(h) (pandas column, float): Global horizontal irradiance [W/m2]
    - Gb(n) (pandas column, float): Direct (beam) irradiance [W/m2]
    - Gd(h) (pandas column, float): Diffuse horizontal irradiance [W/m2]
    Notes
    -----
    A typical meteorological year (TMY) is a set of meteorological data with data values 
    for every hour in a year for a given geographical location. The data are selected from hourly 
    data in a longer time period (normally 10 years or more). 
    The TMY is generated in PVGIS following the procedure described in ISO 15927-4. [1]_
    References
    ----------
    .. [1] https://ec.europa.eu/jrc/en/PVGIS/tools/tmy
    """

    with open(filepath, 'r') as file:
        data = json.load(file)
    data_outputs_hourly = data['outputs']['tmy_hourly']
    df = pd.DataFrame.from_dict(data_outputs_hourly)
    df.set_index('time(UTC)', inplace = True)
    df.index = pd.to_datetime(df.index, format = '%Y%m%d:%H%M')
    return df[['T2m','G(h)','Gb(n)','Gd(h)']]