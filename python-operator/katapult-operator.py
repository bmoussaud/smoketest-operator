import kopf

from jobrunner.trigger_job import JobRunner


@kopf.on.login()
def login_fn(**kwargs):
    return kopf.login_via_client(**kwargs)


@kopf.on.create('smoketests')
def create_smoketest(body, meta, spec, namespace, status, **kwargs):
    print(f"CREATE create_smoketests")
    ns = meta['namespace']
    name = meta['name']
    url = spec['url']
    runner = JobRunner(meta['namespace'],meta['name'])
    runner.deploy_configuration(spec)

    ##job_name = runner.katapult(name,ns)
    job_name = f"{ns}/{name}"
    job_description = f"Check if '{url}' is available"
    kopf.info(body, reason='Created',
              message=f"Start '{job_name}' job: {job_description}'")
    return {'job-name': job_name, 'job-description': job_description}


@kopf.on.delete('smoketests')
def delete_smoketest(body, meta, spec, namespace, status, **kwargs):
    print(f"DELETE create_smoketests")
    runner = JobRunner(meta['namespace'],meta['name'])
    runner.undeploy_configuration()

