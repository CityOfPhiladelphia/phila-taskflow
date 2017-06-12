
## TODO: this is becoming a painpoint. Maybe just do an isinstance of Workflow on global?

from .etl.geodb2_carto import (
    etl_carto_geodb2_assessments,
    etl_carto_geodb2_public_cases_fc,
    etl_carto_geodb2_salesforce_cases,
    etl_carto_geodb2_employee_salaries,
    etl_carto_geodb2_wastebaskets_big_belly,
    etl_carto_geodb2_incidents_part1_part2,
    etl_carto_geodb2_opa_properties_public
)

workflows = [
    etl_carto_geodb2_assessments,
    etl_carto_geodb2_public_cases_fc,
    etl_carto_geodb2_salesforce_cases,
    etl_carto_geodb2_employee_salaries,
    etl_carto_geodb2_wastebaskets_big_belly,
    etl_carto_geodb2_incidents_part1_part2,
    etl_carto_geodb2_opa_properties_public
]
