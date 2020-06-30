from elasticsearch import Elasticsearch, helpers

from schedule.config import ElasticConfig

def elastic_bulk_upload(df, org_df, dept_df):
    '''
    Performs a bulk upload to an elasticsearch instance.
    '''
    # Include merged data in the employees and organization dataframes
    df, org_df = merge_dataframes(df, org_df, dept_df)
    # Create an instance of the ES client
    es = Elasticsearch([ElasticConfig.ELASTIC_URL],
                        timeout=ElasticConfig.ELASTIC_TIMEOUT)
    # Upload the employee data to elastic search in bulk
    bulk_upload_employees(df, es)
    # Upload organization data to elastic search in bulk
    bulk_upload_organizations(org_df, es)

def merge_dataframes(df, org_df, dept_df):
    '''
    Merges dataframes such that employees are indexed into elasticsearch with
    their organization/department names, as well as the traversal path from root
    to their organization unit.
    '''
    # Keep only the subsets that will be used.
    df = df[["employee_id", "last_name", "first_name", "full_name", "job_title_en", "job_title_fr",
             "phone_number", "email", "address_en", "address_fr", "province_en",
             "province_fr", "city_en", "city_fr", "postal_code", "org_id", "dept_id"]]
    org_df = org_df[["org_id", "org_name_en", "org_name_fr", "dept_id", "org_chart_path"]]
    dept_df = dept_df[["dept_id", "department_en", "department_fr"]]
    # Attach organization and department info to the employees dataframe
    df = df.merge(dept_df, left_on='dept_id', right_on='dept_id')
    # Note: the reason for subsetting org_df here is to avoid pandas convention of
    # applying _x and _y to two columns with the same name in different dataframes.
    df = df.merge(org_df[["org_id", "org_name_en", "org_name_fr", "org_chart_path"]],
                         left_on='org_id',
                         right_on='org_id')
    # Construct org df also
    org_df = org_df.merge(dept_df, left_on='dept_id', right_on='dept_id')
    return df, org_df

def bulk_upload_employees(df, es):
    ''' Uploads employees to elasticsearch. '''
    def employee_data_generator(df):
        ''' Generator for employee data. '''
        for idx, row in df.iterrows():
            yield {
                "_index": "employee",
                "_type": "employee",
                "_id": int(row["employee_id"]),
                "_source": {
                    "employee_id": int(row["employee_id"]),
                    "last_name": str(row["last_name"]),
                    "first_name": str(row["first_name"]),
                    "full_name": str(row["full_name"]),
                    "job_title_en": str(row["job_title_en"]),
                    "job_title_fr": str(row["job_title_fr"]),
                    "phone_number": str(row["phone_number"]),
                    "email": str(row["email"]),
                    "address_en": str(row["address_en"]),
                    "address_fr": str(row["address_fr"]),
                    "province_en": str(row["province_en"]),
                    "province_fr": str(row["province_fr"]),
                    "city_en": str(row["city_en"]),
                    "city_fr": str(row["city_fr"]),
                    "postal_code": str(row["postal_code"]),
                    "org_name_en": str(row["org_name_en"]),
                    "org_name_fr": str(row["org_name_fr"]),
                    "org_chart_path": str(row["org_chart_path"]),
                    "department_en": str(row["department_en"]),
                    "department_fr": str(row["department_fr"]),
                    "org_id": str(row["org_id"]),
                    "dept_id": str(row["dept_id"])}
                }
    try:
        res = helpers.bulk(es, employee_data_generator(df))
        print("SUCCESS: RESULT\n", res)
    except Exception as e:
        print("EXCEPTION:\n", e)

def bulk_upload_organizations(df, es):
    ''' Uploads employees to elasticsearch. '''
    def organization_data_generator(df):
        ''' Generator for employee data. '''
        for idx, row in df.iterrows():
            yield {
                "_index": "organization",
                "_type": "organization",
                "_id": int(row["org_id"]),
                "_source": {
                    "org_id": int(row["org_id"]),
                    "org_name_en": str(row["org_name_en"]),
                    "org_name_fr": str(row["org_name_fr"]),
                    "org_chart_path": str(row["org_chart_path"]),
                    "department_en": str(row["department_en"]),
                    "department_fr": str(row["department_fr"])},}
    try:
        res = helpers.bulk(es, organization_data_generator(df))
        print("SUCCESS: RESULT\n", res)
    except Exception as e:
        print("EXCEPTION:\n", e)
