import boto3
import click

## TODO: Deployment steps
# 1) Build image
# 2)
#    a) If ECS, create new task definition and update service
#    b) If Batch, create new job definition
# 3) If Batch update env.yml with new job def and upload

@click.group()
def main():
    pass

@main.command()
@click.argument('image')
@click.argument('job_definition_name')
@click.option('--job-role', default='arn:aws:iam::676612114792:role/oddt-data-engineering-taskflow-role')
@click.option('--env', default='dev')
def register_job_definition(image, job_definition_name, job_role, env):
    batch_client = boto3.client('batch')

    job_definition = {
        'jobDefinitionName': job_definition_name,
        'type': 'container',
        'containerProperties': {
            'image': image,
            'jobRoleArn': job_role,
            'vcpus': 1,
            'memory': 1024,
            'command': [
                'python3',
                'phila_taskflow/main.py',
                'run_task',
                'Ref::task_instance'
            ],
            'environment': [
                {
                    'name': 'EASTERN_STATE_NAME',
                    'value': 'taskflow'
                },
                {
                    'name': 'EASTERN_STATE_BUCKET',
                    'value': 'eastern-state'
                },
                {
                    'name': 'AWS_DEFAULT_REGION',
                    'value': 'us-east-1'
                },
                {
                    'name': 'EASTERN_STATE_ENV',
                    'value': env
                }
            ]
        }
    }

    response = batch_client.register_job_definition(**job_definition)

    print(response)

if __name__ == '__main__':
    main()
