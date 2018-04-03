import sys
from base64 import b64decode

import boto3
import click
import docker
from git import Repo

AWS_TAG_ROOT = '676612114792.dkr.ecr.us-east-1.amazonaws.com/'

SERVICES = [
    {
        'dockerfile': 'Dockerfile.api_server',
        'aws_repo_name': 'taskflow-api-server',
        'name': 'oddt-data-engineering-taskflow-api-server',
        'service_task': {
            'name': 'oddt-data-engineering-taskflow-api-server',
            'task_def_name': 'oddt-data-engineering-taskflow-api-server',
            'task_def': {
                'family': 'oddt-data-engineering-taskflow-api-server',
                'task_role_arn': 'arn:aws:iam::676612114792:role/oddt-data-engineering-taskflow-role',
                'container_definitions': [
                    {
                        'cpu': 256,
                        'image': 'SCRIPT SHOULD UPDATE THIS!!!',
                        'memory': 512,
                        'name': 'taskflow_api_server',
                        'command': ['python3',
                                    'phila_taskflow/main.py',
                                    'api_server',
                                    '--worker-class',
                                    'eventlet',
                                    '--prod'],
                        'essential': True,
                        'portMappings': [
                            {
                              'hostPort': 5000,
                              'containerPort': 5000,
                              'protocol': 'tcp'
                            }
                        ],
                        'environment': [
                            {
                                'name': 'AWS_DEFAULT_REGION',
                                'value': 'us-east-1'
                            },
                            {
                                'name': 'EASTERN_STATE_BUCKET',
                                'value': 'eastern-state'
                            },
                            {
                                'name': 'EASTERN_STATE_NAME',
                                'value': 'taskflow'
                            },
                            {
                                'name': 'EASTERN_STATE_ENV',
                                'value': 'prod'
                            }
                        ],
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': 'oddt-data-engineering/taskflow-api-server',
                                'awslogs-region': 'us-east-1'
                            }
                        }
                    }
                ]
            }
        }
    },
    {
        'dockerfile': 'Dockerfile.scheduler',
        'aws_repo_name': 'taskflow-scheduler',
        'name': 'oddt-data-engineering-taskflow-scheduler',
        'service_task': {
            'name': 'oddt-data-engineering-taskflow-scheduler',
            'task_def_name': 'oddt-data-engineering-taskflow-scheduler',
            'task_def': {
                'family': 'oddt-data-engineering-taskflow-scheduler',
                'task_role_arn': 'arn:aws:iam::676612114792:role/oddt-data-engineering-taskflow-role',
                'container_definitions': [
                    {
                        "cpu": 512,
                        "image": 'SCRIPT SHOULD UPDATE THIS!!!',
                        "memory": 512,
                        "name": "taskflow_scheduler",
                        "command": ["python3",
                                    "phila_taskflow/main.py",
                                    "scheduler",
                                    "--num-runs",
                                    "200"],
                        "essential": True,
                        "environment": [
                            {
                                "name": "AWS_DEFAULT_REGION",
                                "value": "us-east-1"
                            },
                            {
                                "name": "EASTERN_STATE_BUCKET",
                                "value": "eastern-state"
                            },
                            {
                                "name": "EASTERN_STATE_NAME",
                                "value": "taskflow"
                            },
                            {
                                "name": "EASTERN_STATE_ENV",
                                "value": "prod"
                            }
                        ],
                        "logConfiguration": {
                            "logDriver": "awslogs",
                            "options": {
                                'awslogs-group': 'oddt-data-engineering/taskflow-scheduler',
                                'awslogs-region': 'us-east-1'
                            }
                        }
                    }
                ]
            }
        }
    }
]

@click.group()
def main():
    pass

def get_image_repo(service):
    return AWS_TAG_ROOT + service['aws_repo_name']

def get_image_tag(service, hexsha):
    return get_image_repo(service) + ':' + hexsha

@main.command('deploy-taskflow')
@click.option('--no-repo-check', is_flag=True, default=False)
def deploy_taskflow(no_repo_check):
    repo = Repo()

    if not no_repo_check and repo.is_dirty():
        click.echo('Repo is dirty, commit changes')
        sys.exit(1)

    hexsha = repo.head.commit.hexsha
    click.echo('Deploying from commit: {}'.format(hexsha))

    client = docker.from_env()

    ecr_client = boto3.client('ecr')
    response = ecr_client.get_authorization_token()
    auth_data = response['authorizationData'][0]
    userpass = (
        b64decode(auth_data['authorizationToken'])
        .decode('utf-8')
        .split(':')
    )
    auth_config_payload = {'username': userpass[0], 'password': userpass[1]}

    for service in SERVICES:
        image, build_log = client.images.build(path='.',
                                               dockerfile=service['dockerfile'],
                                               tag=get_image_tag(service, hexsha),
                                               rm=True)
        for line in build_log:
            if 'stream' in line:
                sys.stdout.write(line['stream'])

        push_log = client.images.push(get_image_repo(service),
                                      tag=hexsha,
                                      auth_config=auth_config_payload,
                                      stream=True,
                                      decode=True)
        for line in push_log:
            click.echo(line.get('status', '') + '\t' +
                       line.get('progress', '') + '\t' +
                       line.get('id', ''))

    ecs_client = boto3.client('ecs')

    for service in SERVICES:
        service_task = service['service_task']
        service_task['task_def']['container_definitions'][0]['image'] = get_image_tag(service, hexsha)

        response = ecs_client.register_task_definition(**service_task)

        ecs_client.update_service(service=service['name'],
                                  taskDefinition=response['taskDefinition']['taskDefinitionArn'])

        ## TODO: deregister old task def


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
