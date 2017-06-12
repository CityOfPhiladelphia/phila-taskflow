from .etl.geodb2_carto import (
    etl_carto_geodb2_assessments,
    etl_carto_geodb2_public_cases_fc,
    etl_carto_geodb2_salesforce_cases,
    etl_carto_geodb2_employee_salaries,
    etl_carto_geodb2_wastebaskets_big_belly
)

workflows = [
    etl_carto_geodb2_assessments,
    etl_carto_geodb2_public_cases_fc,
    etl_carto_geodb2_salesforce_cases,
    etl_carto_geodb2_employee_salaries,
    etl_carto_geodb2_wastebaskets_big_belly
]
