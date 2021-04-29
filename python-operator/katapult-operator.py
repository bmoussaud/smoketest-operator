import kopf
import pprint

from jobrunner.trigger_job import JobRunner
from jobrunner.pod_manager import PodManager


@kopf.on.login()
def login_fn(**kwargs):
    return kopf.login_via_client(**kwargs)


@kopf.on.create('smoketests')
def create_smoketest(body, meta, spec, namespace, status, **kwargs):
    print(f"CREATE create_smoketests")
    runner = JobRunner(namespace, meta['name'])
    runner.deploy_configuration(spec)
    job_name = runner.trigger_job()

    job_description = f"Check if '{spec['url']}' is available"
    kopf.info(body, reason='Created',
              message=f"Start '{job_name}' job: {job_description}'")
    return {'job-name': job_name, 'job-description': job_description}


@kopf.on.delete('smoketests')
def delete_smoketest(body, meta, spec, namespace, status, **kwargs):
    print(f"DELETE create_smoketests")
    runner = JobRunner(namespace, meta['name'])
    runner.delete_job()
    runner.undeploy_configuration()


@kopf.index('jobs.batch')
def index_jobs(namespace, name, status,  **_):
    print(f"index_jobs jobs.batch {namespace} / {name} / {status}")
    return {(namespace, name): 'jobs.batch'}


@kopf.on.probe()  # type: ignore
def job_count(index_jobs: kopf.Index, **_):
    print(" --> index_jobs %d" % len(index_jobs))
    return len(index_jobs)


@kopf.timer('kex', interval=5)  # type: ignore
def intervalled2(index_jobs: kopf.Index, patch: kopf.Patch, **_):
    print("---- intervalled2 --------")
    pprint.pprint(dict(index_jobs))

# @kopf.index('pods', field='status.phase', value='Failed')


def index_failed_pod(namespace, name, status,  **_):
    print(f"** index_failed_pod {namespace} / {name}")
    logs = PodManager(namespace, name).read_log()
    print(logs)
    return {(namespace, name): 'pods'}


@kopf.on.event('', 'v1', 'pods')
async def pod_event(spec, name, namespace, status, logger, **kwargs):
    print(f"### on pod event {namespace}/{name}:{status}")


@kopf.on.event('jobs')
async def on_jobs_event(spec, name, namespace, body, status, logger, **kwargs):
    print(f"### on batch event {namespace}/{name}:{status}")
    for k in status:
        print(f"key {k}")
    print('----')
    if 'conditions' in status:
        for condition in status['conditions']:
            print(f"--> {condition}")
            message = f"Job '{name}' {condition['type']}:{condition['status']}"
            print(f"the message is {message}")
            kopf.info(body, reason='Created', message=message)
    print(f"### / on batch event {namespace}/{name}:{status}")


@kopf.index('pods')
def is_running(namespace, name, status, **_):
    print("---- is_running --------")
    return {(namespace, name): status.get('phase') == 'Running'}
    # {('kube-system', 'traefik-...-...'): True,
    #  ('kube-system', 'helm-install-traefik-...'): False,
    #    ...}


@kopf.index('pods')
def by_label(labels, name, **_):
    print("---- by_label --------")
    return {(label, value): name for label, value in labels.items()}
    # {('app', 'traefik'): ['traefik-...-...'],
    #  ('job-name', 'helm-install-traefik'): ['helm-install-traefik-...'],
    #  ('helmcharts.helm.cattle.io/chart', 'traefik'): ['helm-install-traefik-...'],
    #    ...}


@kopf.on.probe()  # type: ignore
def pod_count(is_running: kopf.Index, **_):
    print("---- pod_count --------")
    return len(is_running)


@kopf.on.probe()  # type: ignore
def pod_names(is_running: kopf.Index, **_):
    print("---- pod_names --------")
    return [name for _, name in is_running]


@kopf.timer('kex', interval=5)  # type: ignore
def intervalled(is_running: kopf.Index, by_label: kopf.Index, patch: kopf.Patch, **_):
    print("---- intervalled --------")
    pprint.pprint(dict(by_label))
    patch.status['running-pods'] = [
        f"{ns}::{name}"
        for (ns, name), is_running in is_running.items()
        if ns in ['kube-system', 'default']
        if is_running
    ]

@kopf.timer('smoketests', idle=5, interval=2)
def every_few_seconds_sync(spec, logger, **_):
    #logger.info(f"BENOIT Ping from a sync timer: field={spec['field']!r}")
    #print(f"BENOIT Ping from a sync timer: field={spec['field']!r}")
    logger.info(f"BENOIT Ping from a sync timer: field={spec}")
