import os
import time
import logging
from datetime import datetime
import json

from taskflow import cli, Taskflow

from phila_taskflow.workflows import workflows
from phila_taskflow.tasks import tasks

def get_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def get_taskflow():
    taskflow = Taskflow()

    taskflow.add_workflows(workflows)
    taskflow.add_tasks(tasks)

    return taskflow

if __name__ == '__main__':
    get_logging()
    taskflow = get_taskflow()
    cli(taskflow)
