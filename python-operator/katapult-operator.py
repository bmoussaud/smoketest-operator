import kopf

from jobrunner.trigger_job import JobRunner


@kopf.on.login()
def login_fn(**kwargs):
    return kopf.login_via_client(**kwargs)


@kopf.on.create('smoketests')
def create_smoketests(body, meta, spec, namespace, status, **kwargs):
    print(f"CREATE create_smoketests")
    ns = meta['namespace']
    name = meta['name']
    url = spec['url']
    #runner = JobRunner()
    # runner.store_as_cm(body)
    ##job_name = runner.katapult(name,ns)
    job_name = f"{ns}/{name}"
    job_description = f"Check if '{url}' is available"
    kopf.info(body, reason='Created',
              message=f"Start '{job_name}' job: {job_description}'")
    return {'job-name': job_name, 'job-description': job_description}
