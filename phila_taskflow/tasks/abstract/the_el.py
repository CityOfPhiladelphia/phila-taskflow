import os

from taskflow.tasks.bash_task import BashTask

class TheEl(BashTask):
    def __init__(self, *args, **kwargs):
        kwargs['push_destination'] = 'aws_batch'
        kwargs['params']['job_definition'] = os.getenv('THE_EL_JOB_DEFINITION')
        super(TheEl, self).__init__(*args, **kwargs)

    def get_command(self):
        eastern_state_cmd = 'source <(eastern_state load_environment "$EASTERN_STATE_BUCKET" "$EASTERN_STATE_NAME" "$EASTERN_STATE_ENV") &&'

        if 'table_name' in self.params and self.params['table_name'] != None:
            table_name = self.params['table_name']
        elif 'new_table_name' in self.params and self.params['new_table_name'] != None:
            table_name = self.params['new_table_name']

        bash_command = '{} the_el {} {}'.format(
            eastern_state_cmd,
            self.params['el_command'],
            table_name)

        if 'table_schema_path' in self.params and self.params['table_schema_path'] != None:
            if self.params['el_command'] == 'create_table':
                bash_command += ' {}'.format(self.params['table_schema_path'])
            else:
                bash_command += ' --table-schema-path {}'.format(self.params['table_schema_path'])

        if self.params['el_command'] == 'swap_table':
            bash_command += ' ' + self.params['old_table_name']

        if 'connection_string' in self.params and self.params['connection_string'] != None:
            bash_command += ' --connection-string {}'.format(self.params['connection_string'])

        if 'db_schema' in self.params and self.params['db_schema']:
            bash_command += ' --db-schema {}'.format(self.params['db_schema'])

        if 'geometry_support' in self.params and self.params['geometry_support'] != None:
            bash_command += ' --geometry-support {}'.format(self.params['geometry_support'])

        if 'indexes_fields' in self.params and self.params['indexes_fields'] != None:
            if isinstance(self.params['indexes_fields'], list):
                _indexes_fields = ','.join(self.params['indexes_fields'])
            else:
                _indexes_fields = self.params['indexes_fields']

            bash_command += ' --indexes-fields {}'.format(_indexes_fields)

        if 'el_input_file' in self.params and self.params['el_input_file'] != None:
            bash_command += ' --input-file {}'.format(self.params['el_input_file'])

        if 'el_output_file' in self.params and self.params['el_output_file'] != None:
            bash_command += ' --output-file {}'.format(self.params['el_output_file'])

        if 'skip_headers' in self.params and self.params['skip_headers'] != None:
            bash_command += ' --skip-headers'

        if 'from_srid' in self.params and self.params['from_srid'] != None:
            bash_command += ' --from-srid {}'.format(self.params['from_srid'])

        if 'to_srid' in self.params and self.params['to_srid'] != None:
            bash_command += ' --to-srid {}'.format(self.params['to_srid'])

        if 'select_users' in self.params and self.params['select_users'] != None:
            if isinstance(self.params['select_users'], list):
                select_users = ','.join(self.params['select_users'])
            else:
                select_users = self.params['select_users']

            bash_command += ' --select-users {}'.format(select_users)

        if 'if_not_exists' in self.params and self.params['if_not_exists'] == True:
            bash_command += ' --if-not-exists'

        return bash_command
