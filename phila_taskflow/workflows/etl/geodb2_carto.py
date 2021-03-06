from taskflow import Workflow

from phila_taskflow.tasks.abstract.the_el import TheEl

def carto_geodb2_workflow_factory(
        geodb2_schema,
        table_name,
        schema_file,
        geometry_support=None,
        geodb2_table_name=None, # defaults to same as table_name
        final_carto_table_name=None, # overides final carto table - useful for testing like test_table
        schedule='0 7 * * *', # defaults to 7am UTC (2am EST)
        retries=0,
        to_srid=None,
        from_srid=None,
        select_users='publicuser,tileuser',
        geodb2_connection_string='"$GEODB2_PUBLIC_CONN_STRING"',
        indexes_fields_on_create=None,
        indexes_fields_on_load=None,
        extract_timeout=7200,
        load_timeout=7200):

    workflow_name = 'etl_carto_geodb2_{}'.format(table_name)

    data_file = 's3://"$S3_STAGING_BUCKET"/' + workflow_name + '/"$TASKFLOW_WORKFLOW_INSTANCE_ID"/' + workflow_name + '.csv'

    workflow = Workflow(
        name=workflow_name,
        active=True,
        schedule=schedule)

    extract_from_geodb2 = TheEl(
        workflow=workflow,
        name=workflow_name + '_extract_from_geodb2',
        timeout=extract_timeout,
        retries=2,
        params={
            'el_command': 'read',
            'db_schema': geodb2_schema,
            'table_name': geodb2_table_name or table_name,
            'geometry_support':  geometry_support,
            'connection_string': geodb2_connection_string,
            'el_output_file': data_file,
            'to_srid': to_srid,
            'from_srid': from_srid
        })

    postgis_geometry_support = None
    if geometry_support != None:
        postgis_geometry_support = 'postgis'

    create_temp_carto_table = TheEl(
        workflow=workflow,
        name=workflow_name + '_create_temp_carto_table',
        timeout=1200,
        retries=2,
        params={
            'el_command': 'create_table',
            'db_schema': 'phl',
            'table_name': table_name + '_"$TASKFLOW_WORKFLOW_INSTANCE_ID"',
            'table_schema_path': schema_file,
            'geometry_support': postgis_geometry_support,
            'if_not_exists': True,
            'connection_string': '"$CARTO_CONN_STRING"',
            'indexes_fields': indexes_fields_on_create
        })

    load_to_temp_carto_table = TheEl(
        workflow=workflow,
        name=workflow_name + '_load_to_temp_carto_table',
        timeout=load_timeout,
        retries=2,
        params={
            'el_command': 'write',
            'db_schema': 'phl',
            'table_name': table_name + '_"$TASKFLOW_WORKFLOW_INSTANCE_ID"',
            'skip_headers': True,
            'table_schema_path': schema_file,
            'geometry_support': postgis_geometry_support,
            'connection_string': '"$CARTO_CONN_STRING"',
            'el_input_file': data_file,
            'indexes_fields': indexes_fields_on_load,
            'truncate': True
        })

    swap_carto_tables = TheEl(
        workflow=workflow,
        name=workflow_name + '_swap_carto_tables',
        timeout=600,
        retries=2,
        params={
            'el_command': 'swap_table',
            'db_schema': 'phl',
            'new_table_name': table_name + '_"$TASKFLOW_WORKFLOW_INSTANCE_ID"',
            'old_table_name': final_carto_table_name or table_name,
            'select_users': select_users,
            'connection_string': '"$CARTO_CONN_STRING"'
        })

    create_temp_carto_table.depends_on(extract_from_geodb2)
    load_to_temp_carto_table.depends_on(create_temp_carto_table)
    swap_carto_tables.depends_on(load_to_temp_carto_table)

    return workflow

etl_carto_geodb2_assessments = carto_geodb2_workflow_factory(
        'GIS_OPA',
        'assessments',
        's3://"$S3_SCHEMA_BUCKET"/opa_assessments.json',
        schedule='0 6 * * *')

etl_carto_geodb2_opa_properties_public = carto_geodb2_workflow_factory(
        'GIS_ODDT',
        'opa_properties_public',
        's3://"$S3_SCHEMA_BUCKET"/opa_properties_public.json',
        geometry_support='sde-char',
        schedule='0 6 * * *',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_public_cases_fc = carto_geodb2_workflow_factory(
        'GIS_311',
        'public_cases_fc',
        's3://"$S3_SCHEMA_BUCKET"/public_cases_fc.json',
        geometry_support='sde-char',
        schedule='15 6 * * *')

etl_carto_geodb2_salesforce_cases = carto_geodb2_workflow_factory(
        'GIS_311',
        'salesforce_cases',
        's3://"$S3_SCHEMA_BUCKET"/salesforce_cases.json',
        geometry_support='sde-char',
        schedule='15 6 * * *',
        select_users='tileuser,cartodb_user_5219a680-1104-4b8d-bf75-f02f304849e1',
        geodb2_connection_string='"$GEODB2_ODDT_CONN_STRING"',
        indexes_fields_on_load=['service_name', 'agency_responsible', 'requested_datetime', 'status'])

etl_carto_geodb2_employee_salaries = carto_geodb2_workflow_factory(
        'GIS_ODDT',
        'employee_salaries',
        's3://"$S3_SCHEMA_BUCKET"/employee_salaries.json',
        schedule=None) # manually triggered

etl_carto_geodb2_streets_code_violation_notices = carto_geodb2_workflow_factory(
        'GIS_STREETS',
        'streets_code_violation_notices',
        's3://"$S3_SCHEMA_BUCKET"/gis_streets_streets_code_violation_notices.json',
        geometry_support='sde-char',
        schedule='30 6 * * *',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_wastebaskets_big_belly = carto_geodb2_workflow_factory(
        'GIS_STREETS',
        'wastebaskets_big_belly',
        's3://"$S3_SCHEMA_BUCKET"/wastebaskets_big_belly.json',
        geometry_support='sde-char',
        schedule='30 6 * * *',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_car_ped_stops = carto_geodb2_workflow_factory(
        'GIS_POLICE',
        'car_ped_stops',
        's3://"$S3_SCHEMA_BUCKET"/gis_police_car_ped_stops.json',
        geometry_support='sde-char',
        schedule='0 7 * * *')

etl_carto_geodb2_incidents_part1_part2 = carto_geodb2_workflow_factory(
        'GIS_POLICE',
        'incidents_part1_part2',
        's3://"$S3_SCHEMA_BUCKET"/incidents_part1_part2.json',
        geometry_support='sde-char',
        schedule='0 7 * * *')

etl_carto_geodb2_shootings = carto_geodb2_workflow_factory(
        'GIS_POLICE',
        'shootings',
        's3://"$S3_SCHEMA_BUCKET"/gis_police_shootings.json',
        geometry_support='sde-char',
        schedule='0 7 * * *')

etl_carto_geodb2_ais_vw_zoning_documents = carto_geodb2_workflow_factory(
        'GIS_AIS_SOURCES',
        'vw_zoning_documents',
        's3://"$S3_SCHEMA_BUCKET"/gis_ais_sources_vw_zoning_documents.json',
        schedule='0 8 * * *',
        final_carto_table_name='ais_zoning_documents')

etl_carto_geodb2_li_appeals = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_appeals',
        's3://"$S3_SCHEMA_BUCKET"/li_appeals.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_appeals_type = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_appeals_type',
        's3://"$S3_SCHEMA_BUCKET"/li_appeals_type.json',
        schedule='0 8 * * 2-6')

etl_carto_geodb2_li_board_decisions = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_board_decisions',
        's3://"$S3_SCHEMA_BUCKET"/li_board_decisions.json',
        schedule='0 8 * * 2-6')

etl_carto_geodb2_li_business_licenses = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_business_licenses',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_business_licenses.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_case_inspections = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_case_inspections',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_case_inspections.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_com_act_licenses = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_com_act_licenses',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_com_act_licenses.json',
        schedule='0 8 * * 2-6')

etl_carto_geodb2_li_demolitions = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_demolitions',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_demolitions.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_court_appeals = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_court_appeals',
        's3://"$S3_SCHEMA_BUCKET"/li_court_appeals.json',
        schedule='0 8 * * 2-6')

etl_carto_geodb2_li_imm_dang = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_imm_dang',
        's3://"$S3_SCHEMA_BUCKET"/li_imm_dang.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_permits = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_permits',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_permits.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_serv_req = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_serv_req',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_serv_req.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_trade_licenses = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_trade_licenses',
        's3://"$S3_SCHEMA_BUCKET"/li_trade_licenses.json',
        schedule='0 8 * * 2-6')

etl_carto_geodb2_li_unsafe = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_unsafe',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_unsafe.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_li_violations = carto_geodb2_workflow_factory(
        'GIS_LNI',
        'li_violations',
        's3://"$S3_SCHEMA_BUCKET"/gis_lni_li_violations.json',
        geometry_support='sde-char',
        schedule='0 8 * * 2-6',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_stormwater_grants = carto_geodb2_workflow_factory(
        'GIS_WATERSHEDS',
        'stormwater_grants',
        's3://"$S3_SCHEMA_BUCKET"/gis_watersheds_stormwater_grants.json',
        geometry_support='sde-char',
        schedule='0 7 * * *',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_land_use = carto_geodb2_workflow_factory(
        'GIS_PLANNING',
        'land_use',
        's3://"$S3_SCHEMA_BUCKET"/gis_planning_land_use.json',
        geometry_support='sde',
        schedule='0 7 1 * *',
        from_srid=2272,
        to_srid=4326,
        final_carto_table_name='taskflow_land_use')

etl_carto_geodb2_condominium = carto_geodb2_workflow_factory(
        'GIS_DOR',
        'condominium',
        's3://"$S3_SCHEMA_BUCKET"/gis_dor_condominium.json',
        schedule='0 15 * * 6')

etl_carto_geodb2_ppr_website_locatorpoints = carto_geodb2_workflow_factory(
        'GIS_PPR',
        'ppr_website_locatorpoints',
        's3://"$S3_SCHEMA_BUCKET"/gis_ppr_ppr_website_locatorpoints.json',
        geometry_support='sde-char',
        schedule='0 8 * * 1',
        from_srid=2272,
        to_srid=4326,
        geodb2_connection_string='"$GEODB2_ODDT_CONN_STRING"')

etl_carto_geodb2_dor_parcel = carto_geodb2_workflow_factory(
        'GIS_DOR',
        'dor_parcel',
        's3://"$S3_SCHEMA_BUCKET"/gis_dor_dor_parcel.json',
        geometry_support='sde',
        schedule='0 10 * * 0',
        extract_timeout=43200, # 12 hours
        load_timeout=43200, # 12 hours
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_pwd_parcels = carto_geodb2_workflow_factory(
        'GIS_WATER',
        'pwd_parcels',
        's3://"$S3_SCHEMA_BUCKET"/gis_water_pwd_parcels.json',
        geometry_support='sde',
        schedule='0 10 * * 0',
        extract_timeout=43200, # 12 hours
        load_timeout=43200, # 12 hours
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_rtt_summary = carto_geodb2_workflow_factory(
        'GIS_DOR',
        'rtt_summary',
        's3://"$S3_SCHEMA_BUCKET"/gis_dor_rtt_summary.json',
        geometry_support='sde-char',
        schedule=None, # manually trigger
        extract_timeout=10800, # 3 hours
        load_timeout=10800, # 3 hours
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_gis_water_inlets = carto_geodb2_workflow_factory(
        'GIS_WATER',
        'inlets',
        's3://"$S3_SCHEMA_BUCKET"/gis_water_inlets.json',
        geometry_support='sde-char',
        schedule='0 12 * * 0',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_gis_planning_zoning_overlays = carto_geodb2_workflow_factory(
        'GIS_PLANNING',
        'zoning_overlays',
        's3://"$S3_SCHEMA_BUCKET"/gis_planning_zoning_overlays.json',
        geometry_support='sde',
        schedule='0 5 * * *',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_gis_planning_zoning_basedistricts = carto_geodb2_workflow_factory(
        'GIS_PLANNING',
        'zoning_basedistricts',
        's3://"$S3_SCHEMA_BUCKET"/gis_planning_zoning_basedistricts.json',
        geometry_support='sde',
        schedule='0 5 * * *',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_tax_delinquency = carto_geodb2_workflow_factory(
        'GIS_REVENUE',
        'real_estate_tax_delinquencies',
        's3://"$S3_SCHEMA_BUCKET"/gis_revenue_real_estate_tax_delinquencies.json',
        schedule=None, # manually trigger
        geometry_support='sde-char',
        from_srid=2272,
        to_srid=4326)

etl_carto_geodb2_gis_elections_splits = carto_geodb2_workflow_factory(
        'GIS_ELECTIONS',
        'splits',
        's3://"$S3_SCHEMA_BUCKET"/gis_elections_splits.json',
        schedule=None) # manually trigger

etl_carto_geodb2_gis_elections_elected_officials = carto_geodb2_workflow_factory(
        'GIS_ELECTIONS',
        'elected_officials',
        's3://"$S3_SCHEMA_BUCKET"/gis_elections_elected_officials.json',
        schedule=None)  # manually trigger

etl_carto_geodb2_gis_elections_polling_places = carto_geodb2_workflow_factory(
        'GIS_ELECTIONS',
        'polling_places',
        's3://"$S3_SCHEMA_BUCKET"/gis_elections_polling_places.json',
        schedule='0 5 * * *',  # manually trigger
        geometry_support='sde-char',
        from_srid=2272,
        to_srid=4326
        )

etl_carto_geodb2_gis_streets_legal_cards = carto_geodb2_workflow_factory(
        'GIS_STREETS',
        'legal_cards',
        's3://"$S3_SCHEMA_BUCKET"/gis_streets_legal_cards.json',
        schedule='0 5 * * *',  # manually trigger
        geometry_support='sde-char',
        from_srid=2272,
        to_srid=4326
        )
