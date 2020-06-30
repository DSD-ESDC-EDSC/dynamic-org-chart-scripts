import os

import pandas as pd

from schedule.config import DataConfig

from schedule.main.utils.fetch_data import fetch_geds

def prepare_data():
    ''' Returns the prepared dataframe. '''
    # If geds data already exists, load it from csv; otherwise fetch it from url.
    if os.path.isfile(DataConfig.ORIGINAL_DATA_PATH):
        print("Geds data is already here, load from csv")
        df = load_from_csv()
    else:
        # Fetch the GEDS csv, then write it to disk
        df = fetch_geds(DataConfig.GEDS_DATA_URL)
        df.to_csv(DataConfig.ORIGINAL_DATA_PATH)
    df = preprocess_columns(df)
    return create_table_keys(df)

def load_from_csv():
    ''' Returns a pandas dataframe containing the employee data. '''
    return pd.read_csv(DataConfig.ORIGINAL_DATA_PATH)

def preprocess_columns(df):
    '''
    Applies preprocessing to certain columns; returns the modified
    dataframe.
    Args:
        df: a pandas dataframe
    Returns:
        df: a pandas dataframe
    '''
    # Keep only a subset of the dataframe
    df = df[DataConfig.COLUMNS_TO_KEEP]
    # Alias the column names to something sql friendly
    df.columns = DataConfig.COLUMN_ALIASES
    # Standardize the format of organization/department names because they will
    # be used downstream to specify the org chart tree.
    remove_pattern = "|".join(DataConfig.ORG_SPECIAL_CHARACTERS)
    cols_to_format = ["department_en", "department_fr", "org_name_en", "org_name_fr"]
    df[cols_to_format] = df[cols_to_format].replace(remove_pattern, ' ', regex=False)
    # Strip white spaces from end of strings
    df[cols_to_format] = df[cols_to_format].apply(lambda x: x.str.strip())
    # Create a compound name of "dept:org" in case two departments have
    # organizations with identical names.
    df["compound_name_en"] = df["department_en"] + ": " + df['org_name_en']
    df["compound_name_fr"] = df["department_fr"] + ": " + df['org_name_fr']
    # Create compound names for people as an additional field for elasticsearch
    df["full_name"] = df["first_name"] + " " + df["last_name"]
    return df

def create_table_keys(df):
    '''
    Creates unique integer keys for organizations and departments so tables can
    be linked later on.
    '''
    # Use the index as the individaul id
    df["employee_id"] = df.index
    # Create unique integers for organization names
    df = df.assign(org_id=(df["compound_name_en"]).astype('category').cat.codes)
    # Create unique integers for departments
    df = df.assign(dept_id=(df["department_en"]).astype('category').cat.codes)
    return df

def get_contacts_table():
    ''' Returns the contact info table of the database. '''
    df = load_as_dataframe()
    df = preprocess_columns(df)
    org_df, org_chart = prepare_org_chart(df)
    # Trying to find a node in the org chart
    org_df = generate_org_paths(org_df, org_chart)
    # print("temp is ", temp)

def prepare_org_chart(df, tree_depth=7):
    '''
    Creates hierarchical data of the organizational structure using the csv.
    Args:
        df: a pandas dataframe
        tree_depth: an int specifying how deep the org chart tree should go.
    Returns:
        org_chart: a python dict-like object containing the org chart.
    '''
    org_table = df[["org_name"]].drop_duplicates()
    # org_table["org_name"] = org_table["org_name"].drop_duplicates()
    org_struc = df["org_structure"].drop_duplicates()
    org_struc = org_struc.str.split(":", n=-1, expand=True)
    columns = [i for i in range(0, min(tree_depth + 1, len(org_struc.columns)), 1)]
    org_struc = org_struc[columns]
    return org_table, get_org_chart(org_struc)

def generate_org_paths(df, org_chart):
    '''
    Appends a dataframe with the path used to arrive at the particular node in
    the org chart.
    '''
    df["org_chart_path"] = df["org_name"].str.lower().apply(lambda x: get_path_to_node(x, org_chart))
    return df