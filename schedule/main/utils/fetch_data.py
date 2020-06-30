import csv
from io import BytesIO

import pandas as pd
from urllib.request import urlopen
from zipfile import ZipFile

def fetch_geds(url, subset=None):
    '''
    Fetches the geds dataset from Canada's Open Data Portal

    Args:
        url:
            A string containing the url to the Canada Open Data Portal web page
            that downloads a zipped csv containing the geds dataset.
        subset:
            A string containing the acronym found in the "Department Acronym"
            field in the geds dataframe (e.g. "ESDC-EDSC") - used to build the
            org chart tool for only a subset of geds.
    
    Returns:
        df:
            A pandas dataframe containing the original contents of the zipped
            csv file.
    '''
    # Fetch the response from the geds url
    resp = urlopen(url)
    # Extract the file from the bytes object returned by urlopen
    zipped_file = ZipFile(BytesIO(resp.read()))
    # Extract the csv contents line-by-line
    lines = []
    # Note that zipped_file.namelist() returns ['gedsOpenData.csv'], so
    # zipped_file.namelist()[0] returns the file name
    for idx, line in enumerate(zipped_file.open(zipped_file.namelist()[0]).readlines()):
        # Need to use the csv module to read the string returned by line.decode()
        # Reason is csv module contains the logic to parse commas that are
        # contained within double quotes.
        decoded = [str(line.decode('ISO-8859-1'))]
        line = [item for item in csv.reader(decoded)][0]
        # There are a few observations (~90) that are not parsed correctly - this
        # needs to be investigated further.
        if len(line) == 44:
            lines.append(line)
    # Convert to pandas dataframe
    df = pd.DataFrame(lines[1:], columns=lines[0])
    # Select a subset of the dataframe (if any)
    if subset is not None:
        df = df[df["Department Acronym"] == subset]
    return df