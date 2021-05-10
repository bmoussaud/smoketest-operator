deploy-crd:
	kubectl apply -f crd/300-katapulted-crd.yaml
	kubectl api-resources --api-group katapult.org
	
deploy-sample:	
	kubectl apply -f crd/500-maintest.yaml
	kubectl describe smoketests.katapult.org main-test  -n smok
	kubectl get smoketests.katapult.org -n smok main-test
	
undeploy-sample:
	#kubectl patch smoketests.katapult.org main-test  -n smok -p '{"metadata": {"finalizers": []}}' --type merge
	kubectl delete -f crd/500-maintest.yaml
	
undeploy-crd:
	kubectl delete -f crd/300-katapulted-crd.yaml
	kubectl api-resources --api-group katapult.org

deploy-ns:
	kubectl apply -f crd/100-namespace.yaml


# https://craignewtondev.medium.com/how-to-fix-kubernetes-namespace-deleting-stuck-in-terminating-state-5ed75792647e
force-delete-ns:
	kubectl get namespace smok -o json > smok.json
	cat smok.json | grep -v '"kubernetes' > smoked.json
	kubectl replace --raw "/api/v1/namespaces/smok/finalize" -f ./smoked.json
	kubectl delete -f crd/100-namespace.yaml
	
