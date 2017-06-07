import os
import socket

import requests

def get_worker_id():
    worker_components = []

    ## AWS
    response = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
    if response.status_code == 200:
        worker_components.append(response.text)

    ## ECS (AWS Batch uses ECS as well)
    response = requests.get('http://172.17.0.1:51678/v1/tasks')
    if response.status_code == 200:
        tasks = response.json()['Tasks']
        short_docker_id = os.getenv('HOSTNAME', None) ## ECS marks the short docker id as the HOSTNAME
        if short_docker_id != None:
            matched = list(filter(
                lambda ecs_task: ecs_task['Containers'][0]['DockerId'][0:12] == short_docker_id,
                tasks))
            if len(matched) > 0:
                worker_components.append(matched[0]['Containers'][0]['Arn'])

    ## fallback to IP
    if len(worker_components) == 0:
        return socket.gethostbyname(socket.gethostname())
    else:
        return worker_components.join('-')
