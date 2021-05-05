
import time
import kubernetes.config
import logging
from os import path
from kubernetes.client.rest import ApiException
import yaml
import json
from pprint import pprint

class SmokManager:

    def __init__(self, namespace, name):
        self.name = name
        self.namespace = namespace
        self.logger = logging.getLogger('smoke_manager')
        self.logger.setLevel(logging.DEBUG)

    def get_smoke(self):       
        kubernetes.config.load_kube_config()          
        api_instance = kubernetes.client.CustomObjectsApi()
        group = 'katapult.org'
        version = 'v1alpha1'
        plural = 'smoketests'
    
        try:
            api_response = api_instance.get_namespaced_custom_object(group, version, self.namespace, plural, self.name)
            pprint(api_response)            
        except ApiException as e:
            print(
                "Exception when calling CustomObjectsApi->get_cluster_custom_object: %s\n" % e)
            
if __name__ == "__main__":
    sm = SmokManager("smok","main-test")
    sm.get_smoke()