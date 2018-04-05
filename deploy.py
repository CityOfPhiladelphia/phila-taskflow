import sys
from base64 import b64decode

import boto3
import click
import docker
import yaml
from git import Repo
from eastern_state.yaml_utils import Loader, Dumper

AWS_TAG_ROOT = '676612114792.dkr.ecr.us-east-1.amazonaws.com/'

SERVICES = [
    {
        'dockerfile': 'Dockerfile.api_server',
        'aws_repo_name': 'taskflow-api-server',
        'name': 'oddt-data-engineering-taskflow-api-server',
        'cluster': 'oddt-data-engineering-ecs-cluster',
        'service_task': {
            'name': 'oddt-data-engineering-taskflow-api-server',
            'task_def_name': 'oddt-data-engineering-taskflow-api-server',
            'task_def': {
                'family': 'oddt-data-engineering-taskflow-api-server',
                'taskRoleArn': 'arn:aws:iam::676612114792:role/oddt-data-engineering-taskflow-role',
                'containerDefinitions': [
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
        'cluster': 'oddt-data-engineering-ecs-cluster',
        'service_task': {
            'name': 'oddt-data-engineering-taskflow-scheduler',
            'task_def_name': 'oddt-data-engineering-taskflow-scheduler',
            'task_def': {
                'family': 'oddt-data-engineering-taskflow-scheduler',
                'taskRoleArn': 'arn:aws:iam::676612114792:role/oddt-data-engineering-taskflow-role',
                'containerDefinitions': [
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

def get_ecr_auth():
    ecr_client = boto3.client('ecr')
    response = ecr_client.get_authorization_token()
    auth_data = response['authorizationData'][0]
    userpass = (
        b64decode(auth_data['authorizationToken'])
        .decode('utf-8')
        .split(':')
    )
    auth_config_payload = {'username': userpass[0], 'password': userpass[1]}
    return auth_config_payload

@main.command('deploy-taskflow')
@click.option('--no-repo-check', is_flag=True, default=False, help='Overrides checking for uncommitted changes')
@click.option('--no-deploy', is_flag=True, default=False, help='Skips deploying to production, just build and push images')
def deploy_taskflow(no_repo_check, no_deploy):
    repo = Repo()

    if not no_repo_check and repo.is_dirty():
        click.echo('Repo is dirty, commit changes')
        sys.exit(1)

    hexsha = repo.head.commit.hexsha
    click.echo('Deploying from commit: {}'.format(hexsha))

    client = docker.from_env()
    auth_config_payload = get_ecr_auth()

    for service in SERVICES:
        click.echo('{} - Building Image'.format(service['name']))
        image, build_log = client.images.build(path='.',
                                               dockerfile=service['dockerfile'],
                                               tag=get_image_tag(service, hexsha),
                                               rm=True)
        for line in build_log:
            if 'stream' in line:
                sys.stdout.write(line['stream'])

        click.echo('{} - Pushing Image'.format(service['name']))
        push_log = client.images.push(get_image_repo(service),
                                      tag=hexsha,
                                      auth_config=auth_config_payload,
                                      stream=True,
                                      decode=True)
        for line in push_log:
            click.echo(line.get('status', '') + '\t' +
                       line.get('progress', '') + '\t' +
                       line.get('id', ''))

    if not no_deploy:
        ecs_client = boto3.client('ecs')
        for service in SERVICES:
            service_task = service['service_task']
            service_task['task_def']['containerDefinitions'][0]['image'] = get_image_tag(service, hexsha)

            click.echo('{} - Registering new ECS task'.format(service['name']))
            response = ecs_client.register_task_definition(**service_task['task_def'])
            new_task_def_arn = response['taskDefinition']['taskDefinitionArn']

            click.echo('{} - Updating service'.format(service['name']))
            ecs_client.update_service(cluster=service['cluster'],
                                      service=service['name'],
                                      taskDefinition=new_task_def_arn)

            response = ecs_client.list_task_definitions(familyPrefix=service_task['task_def']['family'],
                                                        status='ACTIVE')
            for task_def_arn in response['taskDefinitionArns']:
                if task_def_arn != new_task_def_arn:
                    click.echo('{} - Deregistering old task - {}'.format(service['name'], task_def_arn))
                    ecs_client.deregister_task_definition(taskDefinition=task_def_arn)

def normalize_task_name(task_name):
    return 'taskflow-' + task_name.replace('_', '-')

def get_task_image_repo(task_name):
    return AWS_TAG_ROOT + normalize_task_name(task_name)

def get_task_image_tag(task_name, hexsha):
    return get_task_image_repo(task_name) + ':' + hexsha

@main.command('deploy-task-image')
@click.argument('task-name')
@click.argument('docker-file')
@click.option('--build-path', default='.', help='Folder for docker to build from, usually git repo with task code')
@click.option('--no-repo-check', is_flag=True, default=False, help='Overrides checking for uncommitted changes')
@click.option('--no-deploy', is_flag=True, default=False, help='Skips deploying to production, just build and push images')
@click.option('--job-role', default='arn:aws:iam::676612114792:role/oddt-data-engineering-taskflow-role')
@click.option('--env', default='prod')
def deploy_task_image(task_name, docker_file, build_path, no_repo_check, no_deploy, job_role, env):
    repo = Repo()

    if not no_repo_check and repo.is_dirty():
        click.echo('Repo is dirty, commit changes')
        sys.exit(1)

    hexsha = repo.head.commit.hexsha
    click.echo('Deploying from commit: {}'.format(hexsha))

    client = docker.from_env()
    auth_config_payload = get_ecr_auth()

    click.echo('{} - Building Image'.format(task_name))
    image, build_log = client.images.build(path=build_path,
                                           dockerfile=docker_file,
                                           tag=get_task_image_tag(task_name, hexsha),
                                           rm=True)
    for line in build_log:
        if 'stream' in line:
            sys.stdout.write(line['stream'])

    click.echo('{} - Pushing Image'.format(task_name))
    push_log = client.images.push(get_task_image_repo(task_name),
                                  tag=hexsha,
                                  auth_config=auth_config_payload,
                                  stream=True,
                                  decode=True)
    for line in push_log:
        click.echo(line.get('status', '') + '\t' +
                   line.get('progress', '') + '\t' +
                   line.get('id', ''))

    if not no_deploy:
        click.echo('{} - Registering AWS Batch Job Definition'.format(task_name))

        batch_client = boto3.client('batch')
        job_definition = {
            'jobDefinitionName': normalize_task_name(task_name),
            'type': 'container',
            'containerProperties': {
                'image': get_task_image_tag(task_name, hexsha),
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

        click.echo('{} - Updating env.yml'.format(task_name))
        with open('env.yml') as file:
            env_file = yaml.load(file, Loader)
        task_env_var = task_name.replace('-', '_').upper() + '_JOB_DEFINITION'
        task_env_var_value = response['jobDefinitionName'] + ':' + str(response['revision'])
        env_file['environments'][env]['variables'][task_env_var] = task_env_var_value
 
        click.echo('{} - Updating local env.yml'.format(task_name))
        output = yaml.dump(env_file, Dumper=Dumper)
        with open('env.yml', 'w') as file:
            file.write(output)

        click.echo('{} - Uploading S3 env.yml'.format(task_name))
        client = boto3.client('s3')
        client.put_object(
            Bucket=env_file['bucket'],
            Key=env_file['name'],
            Body=output)

        ## TODO: add, commit, and push env.yml?

        click.echo('{} - Restarting scheduler'.format(task_name))

        ecs_client = boto3.client('ecs')

        scheduler_tasks = ecs_client.list_tasks(cluster='oddt-data-engineering-ecs-cluster',
                                                serviceName='oddt-data-engineering-taskflow-scheduler')
        if len(scheduler_tasks['taskArns']) > 1:
            raise Exception('There should never be more than one scheduler running')
        scheduler_task = scheduler_tasks['taskArns'][0]

        ecs_client.stop_task(cluster='oddt-data-engineering-ecs-cluster',
                             task=scheduler_task)

if __name__ == '__main__':
    main()
