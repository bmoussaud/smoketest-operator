local-run: setup
	kopf run --log-format=full  ./katapult-operator.py

setup:
	pip3 install --upgrade kopf 
	pip3 install --upgrade pykube-ng 
	pip3 install --upgrade stringcase 
	pip3 install --upgrade kubernetes
	