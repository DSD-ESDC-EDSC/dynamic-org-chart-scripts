import json

from sqlalchemy import create_engine
from sqlalchemy.types import Integer, Text

from schedule.config import SQLAlchemyConfig
from schedule.main.utils.db_utils import assemble_sqlalchemy_url

def create_department_table(df, org_chart_en, org_chart_fr):
    '''
    Creates the department table in the database.
    '''
    # Create database connection
    engine = create_engine(assemble_sqlalchemy_url(SQLAlchemyConfig))
    # Keep unique departments as rows
    dept_df = df[["dept_id", "department_en", "department_fr"]].drop_duplicates()
    # Create column to hold serialized org chart
    dept_df["org_chart_en"] = dept_df["department_en"].apply(
        lambda x: get_department_org_chart(x, org_chart_en))
    dept_df["org_chart_fr"] = dept_df["department_fr"].apply(
        lambda x: get_department_org_chart(x, org_chart_fr))
    # Now write department's dataframe to another table in our database. In the
    # current use case, we only need to access each department's org chart from
    # the root.
    dept_df[["dept_id", "department_en", "department_fr", "org_chart_en", "org_chart_fr"]].to_sql(
        "departments",
        engine,
        if_exists="replace",
        index=False,
        dtype={
            "dept_id": Integer,
            "department_en": Text,
            "department_fr": Text,
            "org_chart_en": Text, 
            "org_chart_fr": Text,
        })
    return dept_df

def get_department_org_chart(department, org_chart):
    '''
    Gets the org chart assiciated with a department name.
    Args:
        department: a string containing the department name.
        org_chart: a python dict containing the org chart.
    Returns:
        dept_org_chart: the org chart for the department being searched.
    '''

    # Find the department matching the search; from context we know department will be
    # unique and at the first level of the tree.
    dept = [dept for dept in org_chart
                     if dept.get("name") == department]
    if dept:
        dept = dept[0]
        # Return serialized json 
        return json.dumps(dept)
    return json.dumps(org_chart)
    