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
