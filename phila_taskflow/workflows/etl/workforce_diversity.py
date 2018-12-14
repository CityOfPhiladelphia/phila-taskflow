from os import getenv

from taskflow import Workflow
from taskflow.tasks.bash_task import BashTask
from phila_taskflow.tasks.abstract.the_el import TheEl

redash_connection_string = '"$REDASH_CONN_STRING"'
cli_job_definition = getenv('WORKFORCE_DIVERSITY_JOB_DEFINITION')

source_file_dir = 's3://"$S3_SFTP_SYNC__S3_BUCKET"/sftp/OHR_Workforce_Diversity/'
source_files = {
    'hires': source_file_dir + 'COP_Exempt_Employees_Hires_and_Promotions.csv',
    'separations': source_file_dir + 'COP_Exempt_Employees_Separations.csv',
    'roster': source_file_dir + 'COP_HR_Diversity_Report.csv',
}

processed_file_dir = 's3://"$S3_STAGING_BUCKET"/workforce_diversity/"$TASKFLOW_WORKFLOW_INSTANCE_ID"/'
processed_file_destinations = {
    'hires': processed_file_dir + 'hires.csv',
    'separations': processed_file_dir + 'separations.csv',
    'roster': processed_file_dir + 'roster.csv',
}

schema_files_dir = 's3://"$S3_SCHEMA_BUCKET/'
schema_files = {
    'hires': schema_files_dir + 'workforce_diversity_hires.json',
    'separations': schema_files_dir + 'workforce_diversity_separations.json',
    'roster': schema_files_dir + 'workforce_diversity_roster.json',
}

workforce_diversity = Workflow(
    name='workforce_diversity',
    active=True,
    schedule=None # manually trigger
    # schedule='0 8 * * 1' # mondays at 8am
)

process_hires = BashTask(
    workflow=workforce_diversity,
    name='process_hires',
    push_destination='aws_batch',
    params={
        'job_definition': cli_job_definition,
        'command': 'cat {} | workforce_diversity process_hires > {}'.format(
            source_files['hires'], processed_file_destinations['hires'])
    },
)

process_separations = BashTask(
    workflow=workforce_diversity,
    name='process_separations',
    push_destination='aws_batch',
    params={
        'job_definition': cli_job_definition,
        'command': 'cat {} | workforce_diversity process_separations > {}'.format(
            source_files['separations'], processed_file_destinations['separations'])
    },
)

process_roster = BashTask(
    workflow=workforce_diversity,
    name='process_roster',
    push_destination='aws_batch',
    params={
        'job_definition': cli_job_definition,
        'command': 'cat {} | workforce_diversity process_exempt_roster > {}'.format(
            source_files['roster'], processed_file_destinations['roster'])
    },
)

upsert_hires = TheEl(
    workflow=workforce_diversity,
    name='upsert_hires',
    params={
        'el_command': 'write',
        'upsert': True,
        'db_schema': 'workforce_diversity',
        'table_name': 'hires',
        'table_schema_path': schema_files['hires'],
        'connection_string': redash_connection_string,
        'el_input_file': processed_file_destinations['hires'],
        'geometry_support': 'postgis',
        'skip_headers': True,
    }
)

upsert_separations = TheEl(
    workflow=workforce_diversity,
    name='upsert_separations',
    params={
        'el_command': 'write',
        'upsert': True,
        'db_schema': 'workforce_diversity',
        'table_name': 'separations',
        'table_schema_path': schema_files['separations'],
        'connection_string': redash_connection_string,
        'el_input_file': processed_file_destinations['separations'],
        'geometry_support': 'postgis',
        'skip_headers': True,
    }
)

upsert_roster = TheEl(
    workflow=workforce_diversity,
    name='upsert_roster',
    params={
        'el_command': 'write',
        'upsert': True,
        'db_schema': 'workforce_diversity',
        'table_name': 'roster',
        'table_schema_path': schema_files['roster'],
        'connection_string': redash_connection_string,
        'el_input_file': processed_file_destinations['roster'],
        'geometry_support': 'postgis',
        'skip_headers': True,
    }
)

upsert_hires.depends_on(process_hires)
upsert_separations.depends_on(process_separations)
upsert_roster.depends_on(process_roster)
# Note this dependency tree could result in some files being
# successfully updated but not all. Not sure that's ideal.
