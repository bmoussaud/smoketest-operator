# README

## Setup

https://github.com/gbaeke/kopf-example
https://blog.baeke.info/2020/01/26/writing-a-kubernetes-operator-with-kopf/
https://kopf.readthedocs.io/
https://github.com/nolar/kopf

https://pykube.readthedocs.io/en/latest/index.html

# VIDEO
https://www.youtube.com/watch?v=vkhTdaAtcRE

## ERRORS

if

```python

aiohttp.client_exceptions.ClientResponseError: 503, message='Service Unavailable', url=URL('https://127.0.0.1:6443/apis/metrics.k8s.io/v1beta1')

```

then

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```
