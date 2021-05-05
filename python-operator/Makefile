local-run: setup
	kopf run --log-format=full  -m jobrunner ./katapult-operator.py

setup:
	pip3 install kopf
	pip3 install kubernetes
	pip3 install pykube-ng
