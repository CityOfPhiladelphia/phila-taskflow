
## TODO: this is becoming a painpoint. Maybe just do an isinstance of Workflow on global?

from .etl.geodb2_carto import (
    etl_carto_geodb2_assessments,
    etl_carto_geodb2_public_cases_fc,
    etl_carto_geodb2_salesforce_cases,
    etl_carto_geodb2_employee_salaries,
    etl_carto_geodb2_streets_code_violation_notices,
    etl_carto_geodb2_wastebaskets_big_belly,
    etl_carto_geodb2_car_ped_stops,
    etl_carto_geodb2_incidents_part1_part2,
    etl_carto_geodb2_shootings,
    etl_carto_geodb2_opa_properties_public,
    etl_carto_geodb2_ais_vw_zoning_documents,
    etl_carto_geodb2_li_appeals,
    etl_carto_geodb2_li_appeals_type,
    etl_carto_geodb2_li_board_decisions,
    etl_carto_geodb2_li_business_licenses,
    etl_carto_geodb2_li_case_inspections,
    etl_carto_geodb2_li_com_act_licenses,
    etl_carto_geodb2_li_court_appeals,
    etl_carto_geodb2_li_demolitions,
    etl_carto_geodb2_li_imm_dang,
    etl_carto_geodb2_li_permits,
    etl_carto_geodb2_li_serv_req,
    etl_carto_geodb2_li_trade_licenses,
    etl_carto_geodb2_li_unsafe,
    etl_carto_geodb2_li_violations,
    etl_carto_geodb2_stormwater_grants,
    etl_carto_geodb2_land_use,
    etl_carto_geodb2_vw_rtt_summary,
    etl_carto_geodb2_ppr_website_locatorpoints,
    etl_carto_geodb2_dor_parcel,
    etl_carto_geodb2_pwd_parcels,
    etl_carto_geodb2_rtt_summary,
    etl_carto_geodb2_gis_water_inlets,
    etl_carto_geodb2_gis_planning_zoning_overlays,
    etl_carto_geodb2_gis_planning_zoning_basedistricts,
    etl_carto_geodb2_tax_delinquency,
    etl_carto_geodb2_gis_elections_elected_officials,
    etl_carto_geodb2_gis_elections_splits
)
from .etl.ppr import ppr_knack_workflow

workflows = [
    etl_carto_geodb2_assessments,
    etl_carto_geodb2_public_cases_fc,
    etl_carto_geodb2_salesforce_cases,
    etl_carto_geodb2_employee_salaries,
    etl_carto_geodb2_streets_code_violation_notices,
    etl_carto_geodb2_wastebaskets_big_belly,
    etl_carto_geodb2_car_ped_stops,
    etl_carto_geodb2_incidents_part1_part2,
    etl_carto_geodb2_shootings,
    etl_carto_geodb2_opa_properties_public,
    etl_carto_geodb2_ais_vw_zoning_documents,
    etl_carto_geodb2_li_appeals,
    etl_carto_geodb2_li_appeals_type,
    etl_carto_geodb2_li_board_decisions,
    etl_carto_geodb2_li_business_licenses,
    etl_carto_geodb2_li_case_inspections,
    etl_carto_geodb2_li_com_act_licenses,
    etl_carto_geodb2_li_court_appeals,
    etl_carto_geodb2_li_demolitions,
    etl_carto_geodb2_li_imm_dang,
    etl_carto_geodb2_li_permits,
    etl_carto_geodb2_li_serv_req,
    etl_carto_geodb2_li_trade_licenses,
    etl_carto_geodb2_li_unsafe,
    etl_carto_geodb2_li_violations,
    etl_carto_geodb2_stormwater_grants,
    etl_carto_geodb2_land_use,
    etl_carto_geodb2_vw_rtt_summary,
    etl_carto_geodb2_ppr_website_locatorpoints,
    ppr_knack_workflow,
    etl_carto_geodb2_dor_parcel,
    etl_carto_geodb2_pwd_parcels,
    etl_carto_geodb2_rtt_summary,
    etl_carto_geodb2_gis_water_inlets,
    etl_carto_geodb2_gis_planning_zoning_overlays,
    etl_carto_geodb2_gis_planning_zoning_basedistricts,
    etl_carto_geodb2_tax_delinquency,
    etl_carto_geodb2_gis_elections_elected_officials,
    etl_carto_geodb2_gis_elections_splits
]
