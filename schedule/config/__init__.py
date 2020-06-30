import ast

from configparser import ConfigParser

config = ConfigParser()
# Read in the default and local config files to populate our configuration
files_read = config.read(['./schedule/config/default.cfg', './schedule/config/local.cfg'])

class SQLAlchemyConfig:
    ''' Configuration to connect to SQLAlchemy. '''
    DB_HOST = config.get('database', 'host')
    DB_DIALECT = config.get('database', 'dialect')  # Used to construct a SQLAlchemy URL
    DB_PORT = int(config.get('database', 'port'))
    DB_NAME = config.get('database', 'name')
    DB_USER = config.get('database', 'user')
    DB_PASS = config.get('database', 'pass')
    EMPLOYEES_COLUMNS_EN = ast.literal_eval(config.get('database', 'employees_en_table'))
    EMPLOYEES_COLUMNS_FR = ast.literal_eval(config.get('database', 'employees_fr_table'))


class DataConfig:
    GEDS_DATA_URL = config.get('data', 'geds_data_url')
    ORIGINAL_DATA_PATH = config.get('data', 'original_data_path')
    COLUMNS_TO_KEEP = ast.literal_eval(config.get('data', 'columns_to_keep'))
    COLUMN_ALIASES = ast.literal_eval(config.get('data', 'column_name_aliases'))
    ORG_SPECIAL_CHARACTERS = ast.literal_eval(config.get('data', 'org_special_characters'))
    

class ElasticConfig:
    ELASTIC_URL = config.get('elasticsearch', 'elastic_url')
    ELASTIC_TIMEOUT = int(config.get('elasticsearch', 'timeout'))

class TestConfig:
    TEST_DATA_PATH = config.get('data', 'test_data_path')