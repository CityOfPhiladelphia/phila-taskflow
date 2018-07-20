# Phila Taskflow

Local instance of [Taskflow](https://github.com/CityOfPhiladelphia/taskflow)

This instance of Taskflow uses AWS Elastic Container Service (ECS) and AWS Batch to process workflows and tasks using Docker containers.

There are Dockerfiles for the scheduler and API server, as well as various Dockerfiles for each type of task.

Read the [Taskflow](https://github.com/CityOfPhiladelphia/taskflow) to learn how to create a workflow or task.

Once you have a workflow or task, look at some of the existing Dockerfiles, Dockerfile.s3_sftp_sync.worker being the simplist and Dockerfile.the_el.worker being a more complex example.

### Deploy Taskflow Service

Deploys the Taskflow API and Scheduler. This should be performed everytime workflow defination code is changed (schedule, dependency, etc).

```sh
python deploy.py deploy-taskflow
```

### Deploy Taskflow task

Deploy a unique task container, such as the container that powers TheEL abstract task in this repo.

```sh
python deploy.py deploy-task-image the-el Dockerfile.the_el.worker
```

If you are deploying a transformation from another repo, make sure to keep the virtualenv enironment used for phila-taskflow active and change to the transformation scripts repo, then run `python deploy.py deploy-task-image ...`.

### Manually Deploy a task container

*** Outdated! - Kept in case pieces are useful ***

You will need to [create a repository in AWS](http://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-create.html) for the docker image. You only need to this each time your create a new image (new Dockerfile). The follow instructions can be used for each deploy after setting up a container repository.

In this example, we are deploying the `taskflow-the-el` using the `Dockerfile.the_el.worker` Dockerfile.

 1) Commit your code changes and get the latest commit hash using `git rev-parse HEAD`
 
 2) Build the Dockerfile using the git hash and your AWS Batch job definition name.
 
 `docker build -t 676612114792.dkr.ecr.us-east-1.amazonaws.com/taskflow-the-el:b2a7a76b98f87d5b914b7c55fdc8ea7b2c6a1b9a -f Dockerfile.the_el.worker .`
 
 Using follow the tag pattern `{container repo}:{HEAD get hash}`.
 
 3) Make sure Docker is logged into AWS by running `aws ecr get-login --no-include-email --region us-east-1` and copy-pasting the command it gives you into the terminal.
 
 4) Push the newly built image to the container repo `docker push 676612114792.dkr.ecr.us-east-1.amazonaws.com/taskflow-the-el:b2a7a76b98f87d5b914b7c55fdc8ea7b2c6a1b9a`
 
 5) Run `python deploy.py register_job_definition 76612114792.dkr.ecr.us-east-1.amazonaws.com/taskflow-the-el:b2a7a76b98f87d5b914b7c55fdc8ea7b2c6a1b9a taskflow-the-el --env prod` and note the 'revision' number that is returned.
 
 6) Update the task job definition environment variable, such as `THE_EL_JOB_DEFINITION` with the new revision number in env.yml. `THE_EL_JOB_DEFINITION: taskflow-the-el:44`
 
 7) Upload the edited env.yml to S3 `cat env.yml | eastern_state upload`
 
 8) Restart the scheduler or wait 20 minutes TODO: Give guidance on this?
