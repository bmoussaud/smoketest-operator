# SMOKETEST OPERATOR

## Running the app

### Repository install with Internet connectivity

First, let's add a new repository:

```shell
tanzu package repository add smoketest-operator-repo --url ghcr.io/bmoussaud/smoketest-operator-repo:latest -n tanzu-package-repo-global 
```

Wait a few minutes until the repository gets reconciled.
Use this command to get reconciliation status:

```shell
tanzu package repository list -n tanzu-package-repo-global
tanzu package repository get smoketest-operator-repo -n tanzu-package-repo-global
```

### Package install

Check that this app is available as a package:

```shell
tanzu package available list smoketest-operator.bmoussaud.github.com -n tanzu-package-repo-global
- Retrieving package versions for smoketest-operator.bmoussaud.github.com...
  NAME                                     VERSION    RELEASED-AT
  smoketest-operator.bmoussaud.github.com  0.1.0-dev  2022-04-20 19:37:19 +0200 CEST
```

Keep the package version handy - you'll need it when it comes to package deployment.

Create file `my-values.yaml`:

```yaml
#! Set target namespace.
NAMESPACE: smoketest-operator
```

Edit this file accordingly.

Deploy the package, using the version you have installed:

```shell
tanzu package install kpack-viz --package-name smoketest-operator.bmoussaud.github.com --version 0.1.0-dev  -n tanzu-package-repo-global -f my-values.yaml
```

Check the status of the deployed package
```shell
tanzu package installed get kpack-viz -n tanzu-package-repo-global
```
When the package install is done, note there's a new namespace accordingly to the `my-values.yaml` file

## Uninstall

```shell
tanzu package installed delete kpack-viz -n tanzu-package-repo-global
tanzu package repository delete smoketest-operator-repo -n tanzu-package-repo-global
```


## Setup

https://github.com/gbaeke/kopf-example
https://blog.baeke.info/2020/01/26/writing-a-kubernetes-operator-with-kopf/
https://kopf.readthedocs.io/
https://github.com/nolar/kopf

https://pykube.readthedocs.io/en/latest/index.html

# VIDEO
https://www.youtube.com/watch?v=vkhTdaAtcRE

About CRD format:
https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.0.md
https://github.com/vmware-tanzu/carvel-kapp/blob/develop/pkg/kapp/resourcesmisc/api_extensions_vx_crd.go
https://docs.okd.io/latest/rest_api/extension_apis/customresourcedefinition-apiextensions-k8s-io-v1.html

## ERRORS

if

```python

aiohttp.client_exceptions.ClientResponseError: 503, message='Service Unavailable', url=URL('https://127.0.0.1:6443/apis/metrics.k8s.io/v1beta1')

```

then

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
