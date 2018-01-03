from taskflow import Workflow

from phila_taskflow.tasks.abstract.the_el import TheEl
from phila_taskflow.tasks.abstract.extract_knack import ExtractKnackObject

schemas_base_path = 'https://raw.githubusercontent.com/CityOfPhiladelphia/myppr-data-pipeline/master/schemas/'

ppr_knack_tables = [
    {
        'carto_table': 'ppr_activity_categories',
        'knack_object_id': 32,
        'schema': 'ppr_activity_categories.json'
    },
    {
        'carto_table': 'ppr_activity_types',
        'knack_object_id': 6,
        'schema': 'ppr_activity_types.json'
    },
    {
        'carto_table': 'ppr_amenities',
        'knack_object_id': 7,
        'schema': 'ppr_amenities.json'
    },
    {
        'carto_table': 'ppr_amenity_types',
        'knack_object_id': 4,
        'schema': 'ppr_amenity_types.json'
    },
    {
        'carto_table': 'ppr_days',
        'knack_object_id': 25,
        'schema': 'ppr_days.json'
    },
    {
        'carto_table': 'ppr_facilities',
        'knack_object_id': 2,
        'schema': 'ppr_facilities.json'
    },
    {
        'carto_table': 'ppr_location_types',
        'knack_object_id': 33,
        'schema': 'ppr_location_types.json'
    },
    {
        'carto_table': 'ppr_program_schedules',
        'knack_object_id': 22,
        'schema': 'ppr_program_schedules.json'
    },
    {
        'carto_table': 'ppr_facility_schedules',
        'knack_object_id': 31,
        'schema': 'ppr_facility_schedules.json'
    },
    {
        'carto_table': 'ppr_programs',
        'knack_object_id': 5,
        'schema': 'ppr_programs.json'
    }
]

ppr_knack_workflow = Workflow(
    name='ppr_finder',
    active=True,
    schedule='0 8 * * 2-6')

for table in ppr_knack_tables:
    data_file = 's3://"$S3_STAGING_BUCKET"/ppr_finder/"$TASKFLOW_WORKFLOW_INSTANCE_ID"/{}.csv'.format(
        table['carto_table'])
    temp_table_name = table['carto_table'] + '_"$TASKFLOW_WORKFLOW_INSTANCE_ID"'

    extract_from_knack = ExtractKnackObject(
        workflow=ppr_knack_workflow,
        retries=2,
        name='{}_extract_{}'.format(ppr_knack_workflow.name, table['carto_table']),
        params={
            'knack_object_id': table['knack_object_id'],
            'output_file': data_file
        })

    create_temp_carto_table = TheEl(
        workflow=ppr_knack_workflow,
        name='{}_{}_create_temp_table'.format(ppr_knack_workflow.name, table['carto_table']),
        timeout=1200,
        retries=2,
        params={
            'el_command': 'create_table',
            'db_schema': 'phl',
            'table_name': temp_table_name,
            'table_schema_path': schemas_base_path + table['schema'],
            'if_not_exists': True,
            'connection_string': '"$CARTO_CONN_STRING"'
        })

    load_to_temp_carto_table = TheEl(
        workflow=ppr_knack_workflow,
        name='{}_{}_load_temp_table'.format(ppr_knack_workflow.name, table['carto_table']),
        timeout=3600,
        retries=2,
        params={
            'el_command': 'write',
            'db_schema': 'phl',
            'table_name': temp_table_name,
            'skip_headers': True,
            'table_schema_path': schemas_base_path + table['schema'],
            'connection_string': '"$CARTO_CONN_STRING"',
            'el_input_file': data_file
        })

    swap_carto_tables = TheEl(
        workflow=ppr_knack_workflow,
        name='{}_{}_swap_tables'.format(ppr_knack_workflow.name, table['carto_table']),
        timeout=600,
        retries=2,
        params={
            'el_command': 'swap_table',
            'db_schema': 'phl',
            'new_table_name': temp_table_name,
            'old_table_name': table['carto_table'],
            'select_users': ['tileuser', 'publicuser'],
            'connection_string': '"$CARTO_CONN_STRING"'
        })

    create_temp_carto_table.depends_on(extract_from_knack)
    load_to_temp_carto_table.depends_on(create_temp_carto_table)
    swap_carto_tables.depends_on(load_to_temp_carto_table)
