deploy-crd:
	kubectl apply -f crd/100-namespace.yaml
	kubectl apply -f crd/300-katapulted-crd.yaml
	kubectl api-resources --api-group katapult.org
	
deploy-sample:	
	kubectl apply -f crd/500-maintest.yaml
	kubectl describe smoketests.katapult.org main-test  -n smok
	
undeploy-sample:
	#kubectl patch smoketests.katapult.org main-test  -n smok -p '{"metadata": {"finalizers": []}}' --type merge
	kubectl delete -f crd/500-maintest.yaml
	
undeploy:
	#kubectl patch katapulteds.katapult.org katapulted-sample  -n katapulted-crd -p '{"metadata": {"finalizers": []}}' --type merge
	kubectl delete -f crd
