
import time
import kubernetes.config
import logging
from os import path
from kubernetes.client.rest import ApiException
import yaml
import json


class PodManager:

    def __init__(self, namespace, name):
        self.name = name
        self.namespace = namespace
        self.logger = logging.getLogger('pod_manager')
        self.logger.setLevel(logging.DEBUG)

    def read_log(self):
        api = kubernetes.client.CoreV1Api()
        return api.read_namespaced_pod_log(namespace=self.namespace, name=self.name, pretty=True)
