import os
import time
from datetime import datetime

import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from taskflow import Scheduler, Taskflow, Worker, TaskInstance

from phila_taskflow.workflows import workflows
from phila_taskflow.tasks import tasks

def get_taskflow(session):
    taskflow = Taskflow()

    taskflow.add_workflows(workflows)
    taskflow.add_tasks(tasks)

    taskflow.sync_db(session)

    return taskflow

@click.group()
def main():
    pass

@main.command()
def apiserver():
    pass

@main.command()
@click.option('--sql-alchemy-connection')
@click.option('-n','--num-runs', type=int, default=10)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--now-override')
@click.option('--sleep', type=int, default=5)
def scheduler(sql_alchemy_connection, num_runs, dry_run, now_override, sleep):
    connection_string = sql_alchemy_connection or os.getenv('SQL_ALCHEMY_CONNECTION')
    engine = create_engine(connection_string)
    Session = sessionmaker(bind=engine)

    session = Session()
    taskflow = get_taskflow(session)
    session.close()

    if now_override != None:
        now_override = datetime.strptime(now_override, '%Y-%m-%dT%H:%M:%S')

    scheduler = Scheduler(taskflow, dry_run=dry_run, now_override=now_override)

    for n in range(0, num_runs):
        session = Session()
        taskflow.sync_db(session)
        scheduler.run(session)
        session.close()
        time.sleep(sleep)

@main.command()
@click.option('--sql-alchemy-connection')
@click.option('-n','--num-runs', type=int, default=10)
@click.option('--dry-run', is_flag=True, default=False)
@click.option('--now-override')
@click.option('--sleep', type=int, default=5)
@click.option('--task-names')
@click.option('--worker-id')
def pull_worker(sql_alchemy_connection, num_runs, dry_run, now_override, sleep, task_names, worker_id):
    connection_string = sql_alchemy_connection or os.getenv('SQL_ALCHEMY_CONNECTION')
    engine = create_engine(connection_string)
    Session = sessionmaker(bind=engine)

    session = Session()
    taskflow = get_taskflow(session)
    session.close()

    worker = Worker(taskflow)

    if now_override != None:
        now_override = datetime.strptime(now_override, '%Y-%m-%dT%H:%M:%S')

    if task_names != None:
        task_names = task_names.split(',')

    worker_id = worker_id or 'pull_worker' ## TODO: get AWS instance ID

    for n in range(0, num_runs):
        session = Session()
        
        task_instances = taskflow.pull(session, worker_id, task_names=task_names, now=now_override)

        print(task_instances)
        
        if len(task_instances) > 0:
            worker.execute(session, task_instances[0])

        session.close()

        if sleep > 0:
            time.sleep(sleep)

@main.command()
@click.argument('task_instance_id', type=int)
@click.option('--sql-alchemy-connection')
@click.option('--worker-id')
def run_task(task_instance_id, sql_alchemy_connection, worker_id):
    connection_string = sql_alchemy_connection or os.getenv('SQL_ALCHEMY_CONNECTION')
    engine = create_engine(connection_string)
    Session = sessionmaker(bind=engine)

    worker_id = worker_id or 'pull_worker' ## TODO: get AWS instance ID

    session = Session()
    taskflow = get_taskflow(session)

    task_instance = session.query(TaskInstance).get(task_instance_id)

    worker = Worker(taskflow)
    worker.execute(session, task_instance)

    session.close()

if __name__ == '__main__':
    main()
