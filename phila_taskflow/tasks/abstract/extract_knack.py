import os

from taskflow.tasks.bash_task import BashTask

class ExtractKnackObject(BashTask):
    def __init__(self, *args, **kwargs):
        kwargs['push_destination'] = 'aws_batch'
        kwargs['params']['job_definition'] = os.getenv('EXTRACT_KNACK_JOB_DEFINITION')
        super(ExtractKnackObject, self).__init__(*args, **kwargs)

    def get_command(self):
        return 'extract-knack extract-records "$KNACK_APP_ID" "$KNACK_APP_KEY" {}'.format(
            self.params['knack_object_id'])
