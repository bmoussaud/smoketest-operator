NAMESPACE=smoketest-operator

crd: namespace
	kubectl apply -f crd/300-katapulted-crd.yaml
	kubectl api-resources --api-group katapult.org
	
deploy-sample:	
	kubectl apply -f crd/500-maintest.yaml -n $(NAMESPACE)
	kubectl describe smoketests.katapult.org main-test  -n $(NAMESPACE)
	kubectl get smoketests.katapult.org -n $(NAMESPACE) main-test
	
undeploy-sample:
	#kubectl patch smoketests.katapult.org main-test  -n $(NAMESPACE) -p '{"metadata": {"finalizers": []}}' --type merge
	kubectl delete -f crd/500-maintest.yaml
	
undeploy-crd:
	kubectl delete -f crd/300-katapulted-crd.yaml
	kubectl api-resources --api-group katapult.org

namespace:
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl get namespace $(NAMESPACE) 


# https://craignewtondev.medium.com/how-to-fix-kubernetes-namespace-deleting-stuck-in-terminating-state-5ed75792647e
force-delete-ns:
	kubectl get namespace $(NAMESPACE) -o json > smok.json
	cat smok.json | grep -v '"kubernetes' > smoked.json
	kubectl replace --raw "/api/v1/namespaces/smok/finalize" -f ./smoked.json
	kubectl delete ns $(NAMESPACE)
	
