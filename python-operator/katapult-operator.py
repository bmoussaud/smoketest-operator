import kopf
import pprint
import yaml
from jobrunner.trigger_job import JobRunner
from jobrunner.pod_manager import PodManager
import pykube
import stringcase


@kopf.on.login()
def login_fn(**kwargs):
    return kopf.login_via_client(**kwargs)


class SmokeTest(pykube.objects.NamespacedAPIObject):
    version = "katapult.org/v1alpha1"
    endpoint = "smoketests"
    kind = "SmokeTest"


def k8s_api():
    # api = pykube.HTTPClient(pykube.KubeConfig.from_file())
    # config = pykube.KubeConfig.from_env()
    # api = pykube.HTTPClient(config)

    config_file = "/Users/benoitmoussaud/.kube/config-files/kubeconfig-aws-poc.yml"
    api = pykube.HTTPClient(pykube.KubeConfig.from_file(config_file))
    return api


@kopf.on.create('smoketests')
def create(body, name, meta, spec, namespace, status, logger, **kwargs):
    logger.info(f"create smoke test")
    template_job = "templates/job_complete.yaml"

    job_name = f"job-smoke-test-{name}"
    print(f"{job_name}")

    with open(template_job) as f:
        doc = yaml.safe_load(f)

    env = spec_to_env(spec)
    containers = doc['spec']['template']['spec']['containers']
    container = containers[0]
    container['env'] = env
    logger.info(pprint.pformat(doc))

    doc['metadata']['name'] = job_name
    kopf.adopt(doc)
    kopf.label(doc, {'parent-name': name}, nested=['spec.template'])
    child = pykube.Job(k8s_api(), doc)
    child.create()

    job_description = f"Check if '{spec['url']}' is available"
    kopf.info(body, reason='Created',
              message=f"Start '{job_name}' job: {job_description}'")
    return {'job-name': job_name, 'job-description': job_description}


@kopf.on.event('', 'v1', 'pods', labels={'parent-name': kopf.PRESENT})
def event_in_a_pod(labels, status, namespace, logger, **kwargs):
    logger.debug(f"event_in_a_pod {status}")
    phase = status.get('phase')
    logger.info(f"event_in_a_pod {phase}")
    query = SmokeTest.objects(k8s_api(), namespace=namespace)
    try:
        parent = query.get_by_name(labels['parent-name'])
        logger.debug(f"event_in_a_pod {parent}")
        parent.patch({'status': {'state': phase}})
    except pykube.ObjectDoesNotExist:
        logger.info(
            f"associated smokeTest name='{labels['parent-name']}' does not exist anymore in '{namespace}' namespace")


@ kopf.on.delete('smoketests')
def delete_smoketest(body, meta, name, spec, namespace, status, logger, **kwargs):
    logger.info(f"delete smoke test")
    job_name = f"job-smoke-test-{name}"
    logger.info(f"job name is {job_name}")
    query = pykube.Job.objects(k8s_api(), namespace=namespace)
    parent = query.get_by_name(job_name)
    parent.delete(propagation_policy="Background")


def spec_to_env(spec):
    env = []

    # pprint.pprint(spec)
    # logger.info(pprint.pformat(spec))

    for key in spec:
        name = stringcase.constcase(key)
        if spec[key] is True:
            value = "TRUE"
        elif spec[key] is False:
            value = "FALSE"
        else:
            value = str(spec[key])

        env.append({'name': name, 'value': value})
    env.append({'name': 'SKIP', 'value': '0'})
    return env

# @ kopf.index('jobs.batch')


def index_jobs(namespace, name, status,  **_):
    print(f"index_jobs jobs.batch {namespace} / {name} / {status}")
    for k in status:
        print(f"key {k}")
    print('----')
    if 'conditions' in status:
        condition = status['conditions'][0]
        print(condition)
        return {(namespace, name): {'status': 'success', 'attempt': status['succeeded'], 'completionTime': status['startTime']}}

    if 'failed' in status:
        print("failed")
        return {(namespace, name): {'status': 'failed', 'attempt': status['failed'], 'when': status['startTime']}}


# @ kopf.on.probe()  # type: ignore
def job_count(index_jobs: kopf.Index, **_):
    print(" --> index_jobs %d" % len(index_jobs))
    return len(index_jobs)


# @ kopf.timer('jobs.batch', interval=5)
def intervalled2(index_jobs: kopf.Index, **_):
    print("---- intervalled2 --------")
    pprint.pprint(dict(index_jobs))
    print("---- /intervalled2 --------")

# @kopf.index('pods', field='status.phase', value='Failed')


def index_failed_pod(namespace, name, status,  **_):
    print(f"** index_failed_pod {namespace} / {name}")
    logs = PodManager(namespace, name).read_log()
    print(logs)
    return {(namespace, name): 'pods'}


# @kopf.on.event('', 'v1', 'pods')
async def pod_event(spec, name, namespace, status, logger, **kwargs):
    print(f"### on pod event {namespace}/{name}:{status}")


# @kopf.on.event('jobs')
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


# @ kopf.index('XXXXpods')
def is_running(namespace, name, status, **_):
    print("---- is_running --------")
    return {(namespace, name): status.get('phase') == 'Running'}
    # {('kube-system', 'traefik-...-...'): True,
    #  ('kube-system', 'helm-install-traefik-...'): False,
    #    ...}


# @ kopf.index('XXXXpods')
def by_label(labels, name, **_):
    print("---- by_label --------")
    return {(label, value): name for label, value in labels.items()}
    # {('app', 'traefik'): ['traefik-...-...'],
    #  ('job-name', 'helm-install-traefik'): ['helm-install-traefik-...'],
    #  ('helmcharts.helm.cattle.io/chart', 'traefik'): ['helm-install-traefik-...'],
    #    ...}


# @ kopf.timer('XXXXpods', interval=5)  # type: ignore
def intervalled(is_running: kopf.Index, by_label: kopf.Index, patch: kopf.Patch, **_):
    print("---- intervalled --------")
    pprint.pprint(dict(by_label))
    patch.status['running-pods'] = [
        f"{ns}::{name}"
        for (ns, name), is_running in is_running.items()
        if ns in ['kube-system', 'default']
        if is_running
    ]
    print(patch)
    print("---- /intervalled --------")


# @kopf.timer('smoketests', idle=5, interval=2)
def every_few_seconds_sync(spec, logger, **_):
    # logger.info(f"BENOIT Ping from a sync timer: field={spec['field']!r}")
    # print(f"BENOIT Ping from a sync timer: field={spec['field']!r}")
    logger.info(f"BENOIT Ping from a sync timer: field={spec}")


if __name__ == "__main__":
    with open("crd/500-maintest.yaml") as f:
        smdoc = yaml.safe_load(f)
    env = spec_to_env(smdoc['spec'])

    print(env)
    with open("python-operator/templates/job_complete.yaml") as f:
        doc = yaml.safe_load(f)
    containers = doc['spec']['template']['spec']['containers']
    container = containers[0]
    container['env'] = env
    pprint.pprint(doc)
