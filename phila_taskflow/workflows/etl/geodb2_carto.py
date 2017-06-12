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
        geodb2_connection_string='"$GEODB2_PUBLIC_CONN_STRING"'):

    workflow_name = 'etl_carto_geodb2_{}'.format(table_name)

    data_file = 's3://"$S3_STAGING_BUCKET"/' + workflow_name + '/"$TASKFLOW_WORKFLOW"/' + workflow_name + '.csv'

    workflow = Workflow(
        name=workflow_name,
        active=True,
        schedule=schedule)

    extract_from_geodb2 = TheEl(
        workflow=workflow,
        name=workflow_name + '_extract_from_geodb2',
        timeout=3600,
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
        timeout=600,
        params={
            'el_command': 'create_table',
            'db_schema': 'phl',
            'table_name': table_name + '_"$TASKFLOW_WORKFLOW_INSTANCE_ID"',
            'table_schema_path': schema_file,
            'geometry_support': postgis_geometry_support,
            'connection_string': '"$CARTO_CONN_STRING"'
        })

    load_to_temp_carto_table = TheEl(
        workflow=workflow,
        name=workflow_name + '_load_to_temp_carto_table',
        timeout=3600,
        params={
            'el_command': 'write',
            'db_schema': 'phl',
            'table_name': table_name + '_"$TASKFLOW_WORKFLOW_INSTANCE_ID"',
            'skip_headers': True,
            'table_schema_path': schema_file,
            'geometry_support': postgis_geometry_support,
            'connection_string': '"$CARTO_CONN_STRING"',
            'el_input_file': data_file
        })

    swap_carto_tables = TheEl(
        workflow=workflow,
        name=workflow_name + '_swap_carto_tables',
        timeout=600,
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
       schedule='0 6 * * *',
       final_carto_table_name='taskflow_assessments')

etl_carto_geodb2_public_cases_fc = carto_geodb2_workflow_factory(
       'GIS_311',
       'public_cases_fc',
       's3://"$S3_SCHEMA_BUCKET"/public_cases_fc.json',
       geometry_support='sde-char',
       schedule='0 6 * * *',
       final_carto_table_name='taskflow_public_cases_fc')

etl_carto_geodb2_salesforce_cases = carto_geodb2_workflow_factory(
       'GIS_311',
       'salesforce_cases',
       's3://"$S3_SCHEMA_BUCKET"/salesforce_cases.json',
       geometry_support='sde-char',
       schedule='0 6 * * *',
       select_users='tileuser',
       geodb2_connection_string='"$GEODB2_ODDT_CONN_STRING"',
       final_carto_table_name='taskflow_salesforce_cases')

etl_carto_geodb2_employee_salaries = carto_geodb2_workflow_factory(
       'GIS_ODDT',
       'employee_salaries',
       's3://"$S3_SCHEMA_BUCKET"/employee_salaries.json',
       schedule='0 6 * * *',
       final_carto_table_name='taskflow_employee_salaries')

etl_carto_geodb2_wastebaskets_big_belly = carto_geodb2_workflow_factory(
       'GIS_STREETS',
       'wastebaskets_big_belly',
       's3://"$S3_SCHEMA_BUCKET"/wastebaskets_big_belly.json',
       geometry_support='sde-char',
       schedule='0 6 * * *',
       final_carto_table_name='taskflow_wastebaskets_big_belly')

etl_carto_geodb2_incidents_part1_part2 = carto_geodb2_workflow_factory(
       'GIS_POLICE',
       'incidents_part1_part2',
       's3://"$S3_SCHEMA_BUCKET"/incidents_part1_part2.json',
       geometry_support='sde-char',
       schedule='0 6 * * *',
       final_carto_table_name='taskflow_incidents_part1_part2')
