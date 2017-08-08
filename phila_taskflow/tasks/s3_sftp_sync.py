import os

from taskflow.tasks.bash_task import BashTask

class S3SFTPSync(BashTask):
    def get_command(self):
        return 'source <(eastern_state load_environment "$EASTERN_STATE_BUCKET" "$EASTERN_STATE_NAME" "$EASTERN_STATE_ENV") && s3_sftp_sync'

s3_sftp_sync = S3SFTPSync(
    name='s3_sftp_sync',
    active=True,
    schedule='0 * * * *',
    push_destination='aws_batch',
    timeout=7200,
    retries=1,
    params={
        'job_definition': os.getenv('S3_SFTP_SYNC_JOB_DEFINITION')
    })
