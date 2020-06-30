import pandas as pd

from schedule.main.department.flat_to_hierarchical import get_org_chart

def prepare_org_chart(df, tree_depth=7):
    '''
    Creates hierarchical data of the organizational structure using the csv.
    Args:
        df: a pandas dataframe
        tree_depth: an int specifying how deep the org chart tree should go.
    Returns:
        org_chart: a python dict-like object containing the org chart.
    '''
    # Start by getting a dataframe that contains unique organization structures
    # in both languages
    org_struc_en = df["org_structure_en"].str.replace('\(.*?\)', '').drop_duplicates()
    org_struc_fr = df["org_structure_fr"].str.replace('\(.*?\)', '').drop_duplicates()
    # Split org units into columns and keep a subset of them based on the
    # desired tree depth.
    org_struc_en = org_struc_en.str.split(" :", n=-1, expand=True)
    org_struc_fr = org_struc_fr.str.split(" :", n=-1, expand=True)
    # Column subset is the same in both languages
    columns = [i for i in range(0, min(tree_depth + 1, len(org_struc_en.columns)), 1)]
    org_struc_en = org_struc_en[columns]
    org_struc_fr = org_struc_fr[columns]
    # Remove duplicates to generate org chart
    org_struc_en = remove_duplicates(org_struc_en, columns)
    org_struc_fr = remove_duplicates(org_struc_fr, columns)
    # Get the org charts
    org_chart_en = get_org_chart(org_struc_en)
    org_chart_fr = get_org_chart(org_struc_fr)
    # Remove any instances of None from the list of org charts
    # TODO: check why one of the departments yields None
    org_chart_en = [dept for dept in org_chart_en if dept is not None]
    org_chart_fr = [dept for dept in org_chart_fr if dept is not None]
    # Attach an organization ID to every org chart node
    df["org_name_en_lower"] = df["org_name_en"].str.lower()
    # TODO: maybe just assign french org charts org_id's created from traversing
    # the english tree to avoid character encoding errors.
    # df["org_name_fr_lower"] = df["org_name_fr"].str.lower()
    org_chart_en = attach_org_id(df, org_chart_en, lang="en")
    # org_chart_fr = attach_org_id(df, org_chart_fr, lang="fr")
    return org_chart_en, org_chart_fr

def remove_duplicates(df, columns):
    ''' Removes duplicate organizations. '''
    # Need to restructure the dataframe to avoid duplicates when
    # it is parsed into a dict-like object.
    #==============================================================================
    # Algorithm: if the number of 'Nones' between two consecutive rows differ by 1,
    # keep the row with fewer 'Nones'. If they differ by more than one 'Nones', then 
    # keep both because these are two different paths
    #==============================================================================
    # Dataframe to store the unique rows
    unique_df = pd.DataFrame(columns=columns)
    # Declare initial values
    past_Nones = 0
    current_Nones = 0
    past_row = df.iloc[0]
    # Loop over all rows in org_struc
    for idx, row in df.iloc[1:].iterrows():
        # Calculate past nones and present nones
        for cid in range(1,len(row)):
            if past_row[cid] is None:
                past_Nones += 1
            if row[cid] is None:
                current_Nones += 1
        # Check the difference between past nones and current nones
        diff = past_Nones - current_Nones
        # If diff > 0, then move onto the next row to check - Note that diff will
        # always be 1 if diff > 0 because of the tree structure of the data
        if diff > 0:
            pass
        # If diff <= 0, then the past row must be unique - add it to unique_dfs
        else:
            unique_df = unique_df.append(past_row)
        # Update past row to be the current row
        past_row = row
        # Reset the None counts
        past_Nones = 0
        current_Nones = 0
    return unique_df

def attach_org_id(df, org_chart, lang="en"):
    '''
    For every node in the org chart, attaches a key that contains the
    organization id of each business unit.
    Args:
        df: a pandas dataframe containing the geds dataset.
        org_chart: a dict-like structure containing hierarchical org chart data.
    '''
    for idx, chart in enumerate(org_chart):
        recursive_add(chart, df, lang=lang)
        # if idx > 1: break
    return org_chart

def recursive_add(org_chart, df, lang="en"):
    '''
    Adds the org_id to each node of the org chart. This is used downstream to
    perform fast lookup on data related to the organization. For example, given
    the org_id, it is possible to look up information for all people on that
    team.
    '''
    if org_chart.get("_children") is None:
        org_chart["org_id"] = get_org_id(org_chart['name'], df, lang=lang)
#         print("org chart is ", org_chart)
    else:
        for idx, child in enumerate(org_chart["_children"]):
            recursive_add(child, df)

def get_org_id(org_name, df, lang="en"):
    '''
    Given a dataframe containing organization names and org_id's, returns the
    org id associated with a given name.
    '''
    try:
        return str(df[df[f"org_name_{lang}_lower"] == org_name.lower()].iloc[0]["org_id"])
    except:
        print("could not find match for ", org_name)