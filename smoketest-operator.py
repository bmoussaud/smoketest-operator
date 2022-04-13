
import copy
import kopf
import pprint
import yaml
import stringcase
import os
import kubernetes.config as k8s_config
import kubernetes.client as k8s_client

IN_CLUSTER = os.getenv("IN_CLUSTER", False)


class SmokeTest:
    group = "katapult.org"
    version = "v1alpha1"
    plural = "smoketests"
    kind = "SmokeTest"

    def __init__(self, logger):
        self.logger = logger

    def get_by_name(self, namespace, name):
        self.logger.error(f"SmokeTest:get_by_name {namespace}:{name}")
        try:
            with k8s_client.ApiClient() as api_client:
                api_instance = k8s_client.CustomObjectsApi(api_client)
                api_response = api_instance.get_namespaced_custom_object(
                    self.group, self.version, namespace, self.plural, name)
                return api_response
        except k8s_client.rest.ApiException as e:
            if e.status == 404:
                return None
            else:
                raise

    def update_status(self, namespace, name, body):
        self.logger.error(
            f"SmokeTest:update_status {namespace}:{name} with {body}")

        with k8s_client.ApiClient() as api_client:
            api_instance = k8s_client.CustomObjectsApi(api_client)
            api_response = api_instance.patch_namespaced_custom_object(
                group=self.group, version=self.version, namespace=namespace, plural=self.plural, name=name, body=body)
            return api_response


class Jobs:
    def create_job(self, namespace, doc):
        with k8s_client.ApiClient() as api_client:
            api_instance = k8s_client.BatchV1Api(api_client)
            api_response = api_instance.create_namespaced_job(namespace, doc)
            return api_response

    def delete_job(self, namespace, job_name):
        with k8s_client.ApiClient() as api_client:
            api_instance = k8s_client.BatchV1Api(api_client)
            api_response = api_instance.delete_namespaced_job(
                name=job_name,
                namespace=namespace,
                body=k8s_client.V1DeleteOptions(
                    propagation_policy='Background',
                    grace_period_seconds=0))
            return api_response


class K8SApi:
    def __init__(self):
        if 'KUBERNETES_PORT' in os.environ:
        #if IN_CLUSTER:
            print("----------------- LOAD  K8S_API IN CLUSTER----------------------")
            k8s_config.load_incluster_config()
        else:
            print("----------------- LOAD  K8S_API OUT CLUSTER----------------------")
            k8s_config.load_kube_config()


class Pods:
    def read_pod_logs(self, namespace, pod_name):
        with k8s_client.ApiClient() as api_client:
            api_instance = k8s_client.CoreV1Api(api_client)
            api_response = api_instance.read_namespaced_pod_log(
                name=pod_name, namespace=namespace)
            return api_response


K8S_API = K8SApi()


@kopf.on.login()
def login_fn(**kwargs):
    # return kopf.login_via_client(**kwargs)
    return kopf.login_with_service_account(**kwargs) or kopf.login_with_kubeconfig(**kwargs)


@kopf.on.create('smoketests')
def create(body, name, meta, spec, namespace, status, logger, **kwargs):
    logger.error(f"create smoke test {name}")
    template_job = "templates/job_complete.yaml"

    job_name = get_job_name(name)
    logger.error(f"{job_name}")

    with open(template_job) as f:
        doc = yaml.safe_load(f)

    env = spec_to_env(spec)
    containers = doc['spec']['template']['spec']['containers']
    container = containers[0]
    container['env'] = env
    doc['metadata']['name'] = job_name

    kopf.adopt(doc)
    kopf.label(doc, {'parent-name': name}, nested=['spec.template'])

    logger.error(pprint.pformat(doc))

    api_response = Jobs().create_job(namespace=namespace, doc=doc)
    print("Job created. status='%s'" % str(api_response))

    job_description = f"Check if '{spec['url']}' is available"
    kopf.info(body, reason='Created',
              message=f"Start '{job_name}' job: {job_description}'")

    # TODO: manage the status section properly, done by the return line below
    # but if you remove it, you'll get None line #75 status = parent.obj['status']
    return {'job-name': job_name, 'job-description': job_description}


@kopf.on.event('', 'v1', 'pods', labels={'parent-name': kopf.PRESENT})
def event_in_a_pod(labels, status, name, namespace, started, logger, **kwargs):
    logger.error(f"event_in_a_pod {labels['parent-name']}:{status}")
    phase = status.get('phase')
    startTime = status.get('startTime')
    logger.error(f"smoke test '{labels['parent-name']}'='{phase}'")
    try:
        message = ""
        parent = SmokeTest(logger).get_by_name(
            namespace=namespace, name=labels['parent-name'])

        if parent == None:
            logger.error(
                f"SmokeTest isn't there anymore {namespace}/{labels['parent-name']}")
            return

        new_status = copy.deepcopy(parent)
        logger.error(pprint.pformat(new_status))
        status = new_status['status']

        if not 'startTime' in status:
            status['startTime'] = startTime

        if phase == 'Succeeded':
            status['completionTime'] = started.strftime("%Y-%m-%dT%H:%M:%SZ")
            message = f"'{parent['spec']['url']}' is available"

        if phase == 'Pending':
            if not 'attempts' in status:
                status['attempts'] = 0
            status['attempts'] = status['attempts'] + 1
        else:
            conditions = []
            if not 'conditions' in status:
                status['conditions'] = conditions
            conditions = status['conditions']

            if phase == 'Failed':
                logger.error(f"query log {namespace}/{name}")
                message = Pods().read_pod_logs(namespace, name)
                logger.error(f"query message {message}")

            conditions.append({'status': 'True',
                               'type': phase,
                               'message': message,
                               'lastTransitionTime': started.strftime("%Y-%m-%dT%H:%M:%SZ")})
            status['conditions'] = conditions

        logger.error(f"event_in_a_pod update status with {status}")
        logger.error("get_by_name")
        smoked = SmokeTest(logger).get_by_name(namespace=namespace,
                                               name=labels['parent-name'])

        logger.error(smoked)
        logger.error("update_status")
        SmokeTest(logger).update_status(namespace=namespace,
                                        name=labels['parent-name'], body=new_status)
    except Exception:
        logger.error(
            f"associated smokeTest name='{labels['parent-name']}' does not exist anymore in '{namespace}' namespace")
        logger.exception("Exception in event_in_a_pod ")


@kopf.on.update('smoketests')
def update(body, name, meta, spec, namespace, status, logger, **kwargs):
    logger.error(f"update smoke test {name}")
    delete_smoketest(name, namespace, logger)
    create(body, name, meta, spec, namespace, status, logger)


@kopf.on.delete('smoketests')
def delete_smoketest(name, namespace, logger, **kwargs):
    logger.error(f"delete smoke test {name}")
    job_name = get_job_name(name)
    logger.error(f"job name is {job_name}")

    api_response = Jobs().delete_job(namespace, job_name)
    print("Job deleted. status='%s'" % str(api_response.status))


@kopf.on.event('jobs',  labels={'parent-name': kopf.PRESENT})
def event_in_job(labels, status, name, namespace, started, logger, **kwargs):
    logger.error(f"event_in_job {labels['parent-name']}:{status}")
    if 'conditions' not in status:
        return

    for condition in status['conditions']:
        if condition['type'] == 'Failed':
            logger.error(
                f"smoke test failed job '{labels['parent-name']}'='{condition}'")
            try:
                parent = SmokeTest(logger).get_by_name(
                    namespace=namespace, name=labels['parent-name'])
                status = parent['status']
                conditions = []
                if not 'conditions' in status:
                    status['conditions'] = conditions
                conditions = status['conditions']
                status['completionTime'] = started.strftime(
                    "%Y-%m-%dT%H:%M:%SZ")
                conditions.append({'status': 'True',
                                   'type': 'Failed',
                                   'reason': condition['message'],
                                   'message': f"'{parent['spec']['url']}' is not available",
                                   'lastTransitionTime': started.strftime("%Y-%m-%dT%H:%M:%SZ")})
                status['conditions'] = conditions
                logger.error(f"event_in_a_pod update status with {status}")
                parent.update()
            except Exception:
                logger.error(
                    f"associated smokeTest name='{labels['parent-name']}' does not exist anymore in '{namespace}' namespace")


def get_job_name(name):
    return f"job-smoke-test-{name}"


def spec_to_env(spec):
    env = []
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
