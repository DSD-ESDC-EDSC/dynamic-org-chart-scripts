from sqlalchemy import create_engine
from sqlalchemy.types import Integer, Text

from schedule.config import SQLAlchemyConfig
from schedule.main.utils.db_utils import assemble_sqlalchemy_url


def create_employee_table(df):
    '''
    Creates the employees table in the database.
    '''
    engine = create_engine(assemble_sqlalchemy_url(SQLAlchemyConfig))
    # Keep only a subset of the employee dataframe
    df = df[["employee_id", "last_name", "first_name", "job_title_en", "job_title_fr",
        "phone_number", "email", "address_en", "address_fr", "province_en", "province_fr",
        "city_en", "city_fr", "postal_code", "org_id", "dept_id"]]
    # Create employees table (english)
    df.to_sql(
        "employees",
        engine,
        if_exists="replace",
        index=False,
        chunksize=1000,
        dtype={
            "employee_id": Integer,
            "last_name": Text,
            "first_name": Text,
            "job_title_en": Text,
            "job_title_fr": Text,
            "phone_number": Text,
            "email": Text,
            "address_en": Text,
            "address_fr": Text,
            "province_en": Text,
            "province_fr": Text,
            "city_en": Text,
            "city_fr": Text,
            "postal_code": Text,
            "org_id": Integer,
            "dept_id": Integer,
        })