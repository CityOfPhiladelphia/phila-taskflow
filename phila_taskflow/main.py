import os
import time
import logging
from datetime import datetime
import json

from taskflow import cli, Taskflow
from taskflow.push_workers.aws_batch import AWSBatchPushWorker
from taskflow.monitoring.base import Monitor
from taskflow.monitoring.aws import AWSMonitor
from taskflow.monitoring.slack import SlackMonitor

from phila_taskflow.workflows import workflows
from phila_taskflow.tasks import tasks

DEBUG = os.getenv('DEBUG', 'False') == 'True'

def get_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if DEBUG:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)

def get_taskflow():
    taskflow = Taskflow()

    aws_monitor = AWSMonitor(metric_namespace='taskflow')
    slack_monitor = SlackMonitor(taskflow)
    monitor = Monitor(destinations=[aws_monitor, slack_monitor])
    taskflow.set_monitoring(monitor)

    taskflow.add_workflows(workflows)
    taskflow.add_tasks(tasks)
    job_queue = os.getenv('TASKFLOW_JOB_QUEUE')
    taskflow.add_push_worker(AWSBatchPushWorker(taskflow, default_job_queue=job_queue))

    return taskflow

if __name__ == '__main__':
    get_logging()
    taskflow = get_taskflow()
    cli(taskflow)
