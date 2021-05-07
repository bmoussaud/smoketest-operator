import kopf
import operator
import pykube
import pprint
import yaml
import stringcase


@kopf.on.login()
def login_fn(**kwargs):
    return kopf.login_via_client(**kwargs)


class SmokeTest(pykube.objects.NamespacedAPIObject):
    version = "katapult.org/v1alpha1"
    endpoint = "smoketests"
    kind = "SmokeTest"


class K8SApi:
    def __init__(self):
        print("----------------- LOAD  K8S_API----------------------")
        config_file = "/Users/benoitmoussaud/.kube/config-files/kubeconfig-aws-poc.yml"
        self._api = pykube.HTTPClient(
            pykube.KubeConfig.from_file(config_file))

    def k8s_api(self):
        return self._api


K8S_API = K8SApi()


@kopf.on.create('smoketests')
def create(body, name, meta, spec, namespace, status, logger, **kwargs):
    logger.info(f"create smoke test {name}")
    template_job = "templates/job_complete.yaml"

    job_name = get_job_name(name)
    logger.debug(f"{job_name}")

    with open(template_job) as f:
        doc = yaml.safe_load(f)

    env = spec_to_env(spec)
    containers = doc['spec']['template']['spec']['containers']
    container = containers[0]
    container['env'] = env
    logger.debug(pprint.pformat(doc))

    doc['metadata']['name'] = job_name
    kopf.adopt(doc)
    kopf.label(doc, {'parent-name': name}, nested=['spec.template'])
    child = pykube.Job(K8S_API.k8s_api(), doc)
    child.create()

    job_description = f"Check if '{spec['url']}' is available"
    kopf.info(body, reason='Created',
              message=f"Start '{job_name}' job: {job_description}'")

    return {'job-name': job_name, 'job-description': job_description}


@kopf.on.event('', 'v1', 'pods', labels={'parent-name': kopf.PRESENT})
def event_in_a_pod(labels, status, name, namespace, started, logger, **kwargs):
    if 0 == 1:
        logger.info("------")
        logger.info(f"----- Started {started} {type(started)}")
        logger.info(type(kwargs))
        logger.info(dir(kwargs))
        for k in kwargs:
            logger.info(k)
            logger.info(kwargs[k])
        logger.info("------")
    logger.info(f"event_in_a_pod {labels['parent-name']}:{status}")
    phase = status.get('phase')
    startTime = status.get('startTime')
    logger.info(f"smoke test '{labels['parent-name']}'='{phase}'")
    query = SmokeTest.objects(K8S_API.k8s_api(), namespace=namespace)
    try:
        parent = query.get_by_name(labels['parent-name'])        
        status = parent.obj['status']
        conditions = []
        if not 'conditions' in status:
            status['conditions'] = conditions
        conditions = status['conditions']

        if not 'startTime' in status:
            status['startTime'] = startTime

        if phase == 'Succeeded':
            status['completionTime'] = started.strftime("%Y-%m-%dT%H:%M:%SZ")

        if phase == 'Pending':
            if not 'attempts' in status:
                status['attempts'] = 0
            status['attempts'] = status['attempts'] + 1

        message = ""
        if phase == 'Failed':
            logger.info(f"query log {namespace}/{name}")
            message = pykube.Pod.objects(K8S_API.k8s_api()).filter(
                namespace=namespace).get(name=name).logs()            
            logger.info(f"query message {message}")

        conditions.append({'status': phase,
                           'type': phase,
                           'message': message,
                           'lastTransitionTime': started.strftime("%Y-%m-%dT%H:%M:%SZ")})
        status['conditions'] = conditions

        logger.info(f"event_in_a_pod update status with {status}")
        parent.update()
        # parent.patch(
        #    {'status': {'startTime': startTime, 'conditions': [{'status': phase}, {'status': 'benoit'}]}})

    except pykube.ObjectDoesNotExist:
        logger.info(
            f"associated smokeTest name='{labels['parent-name']}' does not exist anymore in '{namespace}' namespace")


@ kopf.on.update('smoketests')
def update(body, name, meta, spec, namespace, status, logger, **kwargs):
    logger.info(f"update smoke test {name}")
    delete_smoketest(name, namespace, logger)
    create(body, name, meta, spec, namespace, status, logger)


@ kopf.on.delete('smoketests')
def delete_smoketest(name, namespace, logger, **kwargs):
    logger.info(f"delete smoke test {name}")
    job_name = get_job_name(name)
    logger.info(f"job name is {job_name}")
    query = pykube.Job.objects(K8S_API.k8s_api(), namespace=namespace)
    parent = query.get_by_name(job_name)
    parent.delete(propagation_policy="Background")


def get_job_name(name):
    return f"job-smoke-test-{name}"


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
