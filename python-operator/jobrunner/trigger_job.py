
import time
import kubernetes.config
import logging
from os import path
from kubernetes.client.rest import ApiException
import yaml
import json


class JobRunner:

    def __init__(self, namespace, name):
        self.name = name
        self.namespace = namespace
        self.logger = logging.getLogger('trigger_job')
        self.logger.setLevel(logging.DEBUG)
        self.template_job = "templates/job.yaml"
        self.template_cm = "templates/configuration.yaml"
        self.job_namespace = "smok"
        self.resource_prefix = "st"

    def config_map_name(self):
        return f"{self.resource_prefix}-cm-{self.namespace}-{self.name}"

    def job_name(self):
        return f"{self.resource_prefix}-cm-{self.namespace}-{self.name}"

    def deploy_configuration(self, spec):
        with open(self.template_cm) as f:
            cm_spec = yaml.safe_load(f)
            cm_spec['data']['URL'] = spec['url']
            cm_spec['data']['EXPECTED_RESPONSE_TEXT'] = spec['expectedResponseText']
            cm_spec['data']['RETRY_INTERVAL_SECS'] = str(
                spec['retryIntervalSeconds'])
            cm_spec['data']['START_DELAY_SECS'] = str(
                spec['startDelaySeconds'])
            cm_spec['data']['TIMEOUT'] = str(spec['timeout'])
            cm_spec['data']['SHOW_PAGE_CONTENT'] = str(spec['showPageContent'])
            cm_spec['metadata']['name'] = self.config_map_name()

            self.logger.debug(f"cm_spec {cm_spec}")
            api = kubernetes.client.CoreV1Api()
            api.create_namespaced_config_map(
                body=cm_spec, namespace=self.job_namespace)

    def undeploy_configuration(self):
        api = kubernetes.client.CoreV1Api()
        api.delete_namespaced_config_map(
            name=self.config_map_name(), namespace=self.job_namespace)

    def trigger_job(self):
        kubernetes.config.load_kube_config()  # developer's config files
        self.logger.debug("Client is configured via kubeconfig file.")
        self.logger.debug(self.template_job)
        with open(self.template_job) as f:
            content = f.read()
            new_content = content.replace(
                "CONFIG_REF_NAME", self.config_map_name())
            job_spec = yaml.safe_load(new_content)
            job_spec['metadata']['name'] = self.job_name()

            self.logger.debug(f"job_spec {job_spec}")

            # Make it our child: assign the namespace, name, labels, owner references, etc.
            # kopf.adopt(job_spec)

            try:
                batch_api = kubernetes.client.BatchV1Api()
                batch_api.create_namespaced_job(
                    body=job_spec, namespace=self.job_namespace)
                self.logger.debug(f"Job created. status='{self.job_name()}'")
                return self.job_name()
            except ApiException as e:
                self.logger.debug(
                    "Exception when calling AppsV1Api->create_namespaced_job: %s\n" % e)
            

    def delete_job(self):
        batch_api = kubernetes.client.BatchV1Api()
        jobs = batch_api.list_namespaced_job(namespace=self.job_namespace)
        job = next(
            (j for j in jobs.items if j.metadata.name == self.job_name()), None)
        if not job:
            self.logger.debug("{0} not found".format(job_name))
        else:
            self.logger.debug("{0} found, delete it".format(self.job_name()))
            self.logger.debug('delete job {0}'.format(self.job_name()))
            batch_api.delete_namespaced_job(
                name=self.job_name(), namespace=self.job_namespace)
            self.logger.debug("sleep 5 sec")
            time.sleep(5)

def standalone_new_logger():
    logger = logging.getLogger('trigger_job')
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger


if __name__ == "__main__":
    standalone_new_logger()
    #runner = JobRunner()
    # runner.katapult("katapulted-sample","katapulted-crd")
    # runner.unkatapult("katapulted-sample", "katapulted-crd")
