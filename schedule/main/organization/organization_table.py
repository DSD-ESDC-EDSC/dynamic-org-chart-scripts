import json

from sqlalchemy import create_engine
from sqlalchemy.types import Integer, Text

from schedule.config import SQLAlchemyConfig
from schedule.main.utils.db_utils import assemble_sqlalchemy_url
from schedule.main.organization.search import get_path_to_node

def create_organization_table(df, org_chart_en, org_chart_fr, tree_depth=7):
    '''
    Creates the organization table in the database.
    '''
    engine = create_engine(assemble_sqlalchemy_url(SQLAlchemyConfig))
    # Get a dataframe with unique organizations
    org_df = df[["org_id", "org_name_en", "org_name_fr", "dept_id", "department_en", "department_fr", "org_structure_en", "org_structure_fr"]].drop_duplicates()
    # Get the paths to each org unit and store them in a table column
    # TODO: try normalizing text to avoid things like capital letters preventing
    # the search from being successful
    org_df = generate_org_paths(org_df, org_chart_en, "en")
    # # Write org_df to the database
    org_df[["org_id", "org_name_en", "org_name_fr", "dept_id", "org_chart_path"]].to_sql(
        "organizations",
        engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype={
            "org_id": Integer,
            "org_name_en": Text,
            "org_name_fr": Text,
            "dept_id": Integer,
            "org_chart_path": Text,
        })
    return org_df

def generate_org_paths(df, org_chart, lang):
    '''
    Generates the path to each business unit in the org chart.
    '''
    def get_org_path(row, org_chart):
        ''' Finds the relevant org chart to search, then returns the path
            to that org chart.'''
        dept = [dept for dept in org_chart
                     if dept.get("name") == row[f"department_{lang}"]]
        if dept:
            path_to_node = get_path_to_node(row[f"org_name_{lang}"], dept[0])
            return json.dumps(path_to_node)
        return None
    # Serialize the path to the node as a string
    df["org_chart_path"] = df.apply(get_org_path, axis=1, args=(org_chart,))
    return df