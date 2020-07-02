See [parent repository](https://github.com/DSD-ESDC-EDSC/dynamic-org-chart) for more information on the dynamic-org-chart project

# dynamic-org-chart-scripts
Some preprocessing scripts to prepare data for the Dynamic Org Chat project

> This repository runs a scheduled job that fetches the [Government of Canada Employee Contact Information (GEDS)](https://open.canada.ca/data/en/dataset/8ec4a9df-b76b-4a67-8f93-cdbc2e040098) dataset that is made available under the [Open Government License - Canada](https://open.canada.ca/en/open-government-licence-canada). The data produced by the scripts in this repository are used in a REST API which can be found [here](ADD LINK), and an instance of Elastic Search. These services then provide data to a front-end that shows a searchable interactive organizational chart, which can be found [here](ADD LINK).

> TODO:
> 1. Make org chart write "children" keys instead of "_children" keys by default, so that the front end does not need to unhide and rehide during d3 indexing.
> 2. Create separate indices in elastic search for french/english fields (will likely want to search them differently).
> 3. Check how the organization name column is being compared with the organization path column. Some typos/casing/spacing errors cause a failure to identify a search path.

## Start up instructions
1. Pull the elasticsearch docker image and run elasticsearch as a docker container.
```
docker pull docker.elastic.co/elasticsearch/elasticsearch:6.5.1
```
```
docker run -p 9200:9200 -p 9300:9300 -e "http.cors.enabled=true" -e "http.cors.allow-origin=*" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.5.1
```

2. Clone the ```dynamic-org-chart-scripts``` repository to a folder on your computer.
```
git clone https://github.com/DSD-ESDC-EDSC/dynamic-org-chart-scripts
```
3. In a new terminal, create and activate the virtual environment in the root of the ```dynamic-org-chart-scripts``` folder.
```
conda env create -f environment.yml
```
```
conda activate ./venv
```
4. Start the main script in the ```process-geds-data``` repository by running the following command from within the virtual environment in the project root:
```
python start.py
```

## Data
The data produced by the scripts in this repository can be broken into two types: flat and hierarchical. Flat data are written into the SQL tables described below.

### SQL Tables

__employees__
|    | column name | type | description |
|----|-------------|------|-----|
| PK | employee_id | INTEGER |  |
|    | last_name | TEXT |     |
|    | first_name | TEXT |     |
|    | job_title_en | TEXT |     |
|    | job_title_fr | TEXT |     |
|    | phone_number | TEXT |     |
|    | email | TEXT |     |
|    | address_en | TEXT |     |
|    | address_fr | TEXT |     |
|    | province_en | TEXT |     |
|    | province_fr | TEXT |     |
|    | city_en | TEXT |     |
|    | city_fr | TEXT |     |
|    | postal_code | TEXT |     |
| FK | org_id | INTEGER |     |
| FK | dept_id | INTEGER |     |

__organizations__

|    |  column name | type | description |
|----|----------|---------|----|
| PK |	org_id |INTEGER | |
|    |	org_name_en |TEXT | |
|    |	org_name_fr |TEXT | |
| FK |	dept_id |INTEGER | |
|    |	org_chart_path | TEXT | An array (serialized to string) describing the tree traversal required to arrive at the organization in the org chart.|

__departments__
|    |  column name | type | description |
|----|--------|---------|-----|
| PK |	dept_id |INTEGER |  |
|    |	department_en| TEXT |  |
|    |	department_fr |TEXT |  |
|    |	org_chart_en |TEXT | A JSON (serialized to string) describing the english org chart for the department. |
|    |	org_chart_fr |TEXT | A JSON (serialized to string) describing the french org chart for the department. |

### Hierarchical Data
Using a column from the csv extracted from [GEDS](https://open.canada.ca/data/en/dataset/8ec4a9df-b76b-4a67-8f93-cdbc2e040098) ("Organization Structure (EN/FR)"), it is possible to extract a hierarchical structure, which yields an organizational structure for the Government of Canada, as described in GEDS. The format of the data is as follows:

```json
{
  "name": "Employment and Social Development Canada",
  "_children": [
    {
      "name": "Deputy Minister of Employment and Social Development Canada",
      "_children": [
        {
          "name": "Strategic and Service Policy Branch",
          "_children": [
            {
              ...
            }
          ]
        }
      ]
    }
  ]
}
```

Each node has associated with it a ```name``` and ```_children``` property. ```name```, of course, is the name of the organizational unit being described, and ```_children``` is an array of nodes that are direct descendents of the current node. Due to the recursive nature of this structure, it is possible to search for specific business units. Since this linear search through the tree is slow, the path to each organization (starting at the root of its tree) is identified offline during the creation of the database tables (stored in the __org_chart_path__ column of the __organizations__ table). This way, as soon as an organization name or person is searched for (e.g. using [ElasticSearch](https://www.elastic.co)), the path to arrive at that organization or person is instantly available, without requiring a linear search through the tree at the time the request is made.

## Folder Organization

### data
For illustrative purposes, a small csv with fake data is included to simulate what raw data on employees of an organization might look like.

### schedule

#### config
Configurations are stored here using ```*.cfg``` files, and parsed with Python's ```configparser``` library.

#### main
The code below runs a scheduled job using Python's ```apscheduler``` library. In practice, this job will likely be run every 24 hours to pick up the latest posting of GEDS data.

Every function is called from ```main```. The call graph below outlines which functions are called and in which order in development vs. production. The main difference between the two is that the production graph will not fetch the GEDS data from the url every time it is ran; instead, it will store a local copy as a csv file and use that instead to avoid unnecessarily downloading the same file many times while testing during development.

__Dev Module Dependency Graph__
![call graph](https://g.gravizo.com/svg?digraph%20G%20%7B%0A%20%20main%20-%3E%20prepare_data%20%5Blabel%3D%221%22%5D%3B%0A%20%20prepare_data%20-%3E%20%22csv%20on%20disk%3F%22%20%5Bcolor%3D%22blue%22%5D%3B%0A%20%20%22csv%20on%20disk%3F%22%20-%3E%20load_df_from_csv%20%5Blabel%3D%22yes%22%5D%3B%0A%20%20%22csv%20on%20disk%3F%22%20-%3E%20fetch_geds%20%5Blabel%3D%22no%22%5D%3B%0A%20%20%22csv%20on%20disk%3F%22%20-%3E%20prepare_data%20%5Bcolor%3D%22red%22%20label%3D%22df%22%5D%3B%0A%20%20prepare_data%20-%3E%20%7Bpreprocess_columns%3B%20create_table_keys%7D%3B%0A%20%20prepare_data%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22df%22%5D%3B%0A%20%20main%20-%3E%20create_employees_table%20%5Blabel%3D%222%22%5D%3B%0A%20%20main%20-%3E%20prepare_org_chart%20%5Blabel%3D%223%22%5D%3B%0A%20%20prepare_org_chart%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22org%20chart%22%5D%3B%0A%20%20prepare_org_chart%20-%3E%20get_org_chart%3B%0A%20%20get_org_chart%20-%3E%20flat_to_hierarchical%3B%0A%20%20flat_to_hierarchical%20-%3E%20%7Bbuild_leaf%3B%20ctree%7D%3B%0A%20%20main%20-%3E%20create_department_table%20%5Blabel%3D%224%22%5D%3B%0A%20%20create_department_table%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22dept_df%22%5D%3B%0A%20%20create_department_table%20-%3E%20%7Bget_department_org_chart%7D%3B%0A%20%20main%20-%3E%20create_organization_table%20%5Blabel%3D%225%22%5D%3B%0A%20%20create_organization_table%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22org_df%22%5D%3B%0A%20%20create_organization_table%20-%3E%20generate_org_paths%3B%0A%20%20main%20-%3E%20elastic_bulk_upload%20%5Blabel%3D%226%22%5D%3B%0A%20%20elastic_bulk_upload%20-%3E%20%7Bmerge_dataframes%3B%20bulk_upload_employees%3B%20bulk_upload_organizations%7D%3B%0A%7D)
<!-- This is the original graph -->
<!-- <img src='https://g.gravizo.com/svg?
digraph G {
  main -> prepare_data [label="1"];
  prepare_data -> "csv on disk?" [color="blue"];
  "csv on disk?" -> load_df_from_csv [label="yes"];
  "csv on disk?" -> fetch_geds [label="no"];
  "csv on disk?" -> prepare_data [color="red" label="df"];
  prepare_data -> {preprocess_columns; create_table_keys};
  prepare_data -> main [color="red" label="df"];
  main -> create_employees_table [label="2"];
  main -> prepare_org_chart [label="3"];
  prepare_org_chart -> main [color="red" label="org chart"];
  prepare_org_chart -> get_org_chart;
  get_org_chart -> flat_to_hierarchical;
  flat_to_hierarchical -> {build_leaf; ctree};
  main -> create_department_table [label="4"];
  create_department_table -> main [color="red" label="dept_df"];
  create_department_table -> {get_department_org_chart};
  main -> create_organization_table [label="5"];
  create_organization_table -> main [color="red" label="org_df"];
  create_organization_table -> generate_org_paths;
  main -> elastic_bulk_upload [label="6"];
  elastic_bulk_upload -> {merge_dataframes; bulk_upload_employees; bulk_upload_organizations};
}'/> -->

<!-- Github's flavour of markdown doesn't support url encoding. A temporary workaround to this is given below.
In a python terminal (tested with python 3.8), do
raw='''digraph G {
  main -> prepare_data [label="1"];
  prepare_data -> {load_as_dataframe; preprocess_columns; create_table_keys};
  prepare_data -> main [color="red" label="df"];
  main -> create_contacts_table [label="2"];
  main -> create_organizations_table [label="3"];
  main -> create_departments_table [label="4"];
}'''
import urllib.parse
urllib.parse.quote(raw)
Then copy + paste the encoded url into the image tag
-->

__Production Module Dependency Graph__
![call graph](https://g.gravizo.com/svg?digraph%20G%20%7B%0A%20%20main%20-%3E%20prepare_data%20%5Blabel%3D%221%22%5D%3B%0A%20%20prepare_data%20-%3E%20%22csv%20on%20disk%3F%22%20%5Bcolor%3D%22blue%22%5D%3B%0A%20%20%22csv%20on%20disk%3F%22%20-%3E%20load_df_from_csv%20%5Blabel%3D%22yes%22%5D%3B%0A%20%20%22csv%20on%20disk%3F%22%20-%3E%20fetch_geds%20%5Blabel%3D%22no%22%5D%3B%0A%20%20%22csv%20on%20disk%3F%22%20-%3E%20prepare_data%20%5Bcolor%3D%22red%22%20label%3D%22df%22%5D%3B%0A%20%20prepare_data%20-%3E%20%7Bpreprocess_columns%3B%20create_table_keys%7D%3B%0A%20%20prepare_data%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22df%22%5D%3B%0A%20%20main%20-%3E%20create_employees_table%20%5Blabel%3D%222%22%5D%3B%0A%20%20main%20-%3E%20prepare_org_chart%20%5Blabel%3D%223%22%5D%3B%0A%20%20prepare_org_chart%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22org%20chart%22%5D%3B%0A%20%20prepare_org_chart%20-%3E%20get_org_chart%3B%0A%20%20get_org_chart%20-%3E%20flat_to_hierarchical%3B%0A%20%20flat_to_hierarchical%20-%3E%20%7Bbuild_leaf%3B%20ctree%7D%3B%0A%20%20main%20-%3E%20create_department_table%20%5Blabel%3D%224%22%5D%3B%0A%20%20create_department_table%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22dept_df%22%5D%3B%0A%20%20create_department_table%20-%3E%20%7Bget_department_org_chart%7D%3B%0A%20%20main%20-%3E%20create_organization_table%20%5Blabel%3D%225%22%5D%3B%0A%20%20create_organization_table%20-%3E%20main%20%5Bcolor%3D%22red%22%20label%3D%22org_df%22%5D%3B%0A%20%20create_organization_table%20-%3E%20generate_org_paths%3B%0A%20%20main%20-%3E%20elastic_bulk_upload%20%5Blabel%3D%226%22%5D%3B%0A%20%20elastic_bulk_upload%20-%3E%20%7Bmerge_dataframes%3B%20bulk_upload_employees%3B%20bulk_upload_organizations%7D%3B%0A%7D)
<!-- This is the original graph
<img src='https://g.gravizo.com/svg?
digraph G {
  main -> prepare_data [label="1"];
  prepare_data -> "csv on disk?" [color="blue"];
  "csv on disk?" -> load_df_from_csv [label="yes"];
  "csv on disk?" -> fetch_geds [label="no"];
  "csv on disk?" -> prepare_data [color="red" label="df"];
  prepare_data -> {preprocess_columns; create_table_keys};
  prepare_data -> main [color="red" label="df"];
  main -> create_employees_table [label="2"];
  main -> prepare_org_chart [label="3"];
  prepare_org_chart -> main [color="red" label="org chart"];
  prepare_org_chart -> get_org_chart;
  get_org_chart -> flat_to_hierarchical;
  flat_to_hierarchical -> {build_leaf; ctree};
  main -> create_department_table [label="4"];
  create_department_table -> {get_department_org_chart};
  main -> create_organization_table [label="5"];
  create_organization_table -> generate_org_paths;
}'/>
-->

#### test

## Elasticsearch
>TODO: need to test that the org chart paths generated agree with the paths to nodes in the org chart tree structure.

This repository assumes there exists an instance of Elasticsearch that it can upload data to via Elasticsearch's [bulk api](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html). This repository makes use of the [Python client for Elasticsearch](https://elasticsearch-py.readthedocs.io/en/master/).

> Note: Elasticsearch 6.0.0+ [removed support for multiple mapping types](https://www.elastic.co/guide/en/elasticsearch/reference/6.0/removal-of-types.html). As an alternative to multiple mapping types, this repository uses a single index for each type of document. In this case, the two types are ```employee``` and ```organization```. As such, there are two Elasticsearch indices named ```employee``` and ```organization```.

### Set up Elasticsearch with Docker
If you have [Docker](https://www.docker.com/) installed on your system, you can get up-and-running with Elasticsearch in only a few steps. These steps are outlined briefly below, but see [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) for more information.

1. Pull the Elasticsearch image from the Elastic docker registry.
```bash
docker pull docker.elastic.co/elasticsearch/elasticsearch:6.5.1
```
2. Start a single node cluster of elasticsearch on your local machine (host defaults to ```localhost```). Note that the arguments ```-e "http.cors.enabled=true" -e "http.cors.allow-origin=*"``` should only be used in development.
```bash
docker run -p 9200:9200 -p 9300:9300 -e "http.cors.enabled=true" -e "http.cors.allow-origin=*" -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:6.5.1
```
__Note:__ there are ```xms``` and ```xmx``` flags that [control the minimum/maximum heap size for JVM](https://www.elastic.co/guide/en/elasticsearch/reference/6.8/heap-size.html).

### Postman Collection
> TODO: create this and document it

## Resources
1. [SQLalchemy guide ch 1](https://www.oreilly.com/library/view/essential-sqlalchemy-2nd/9781491916544/ch01.html)
2. [sqlalchemy schema](https://overiq.com/sqlalchemy-101/defining-schema-in-sqlalchemy-orm/)
3. [pandas with sqlalchemy](https://hackersandslackers.com/connecting-pandas-to-a-sql-database-with-sqlalchemy/)
4. [python es client tutorial](https://kb.objectrocket.com/elasticsearch/how-to-use-python-helpers-to-bulk-load-data-into-an-elasticsearch-index)
5. [python es client documentation](https://elasticsearch-py.readthedocs.io/en/master/)
6. [python es client bulk helpers](https://elasticsearch-py.readthedocs.io/en/master/helpers.html)
7. [SO post on using Elasticsearch with human names](https://stackoverflow.com/questions/20632042/elasticsearch-searching-for-human-names)

# License
Unless otherwise noted, program source code of this project is covered under Crown Copyright, Government of Canada, and is distributed under the [MIT License](https://github.com/DSD-ESDC-EDSC/dynamic-org-chart/blob/master/LICENSE.md).

The Canada wordmark and related graphics associated with this distribution are protected under trademark law and copyright law. No permission is granted to use them outside the parameters of the Government of Canada's corporate identity program. For more information, see [Federal identity requirements](https://www.canada.ca/en/treasury-board-secretariat/topics/government-communications/federal-identity-requirements.html).

# Attribution
This project would not be possible without the availability and use of open source software. Acknowledgement and attribution to the open source tools used, along with their corresponding open licenses (where one was found), can be found in the [ATTRIBUTION.md](https://github.com/DSD-ESDC-EDSC/dynamic-org-chart/blob/master/ATTRIBUTION.md) file in this repository. Users are advised to consult original sources for official information, especially if they plan on re-distributing all or parts of these code artifacts.

# How to Contribute
Instructions for how to contribute can be found in the CONTRIBUTING.md file.
