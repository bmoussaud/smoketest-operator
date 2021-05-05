local-run: setup
	kopf run --log-format=full  ./katapult-operator.py

setup:
	pip3 install kopf 
	pip3 install pykube-ng 
	pip3 install stringcase 
	pip3 install kubernetes
	