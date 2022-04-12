FROM python:3.8-slim

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

ADD https://storage.googleapis.com/kubernetes-release/release/v1.23.5/bin/linux/amd64/kubectl /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

ARG user=operator
ARG group=operator
ARG uid=1000
ARG gid=37
ARG HOME=/home/operator

RUN useradd -d "$HOME" -u ${uid} -g ${group} -m -s /bin/bash ${user} \
    && mkdir -p $HOME \
    && chown ${uid}:${gid} $HOME \
    && mkdir $HOME/.kube

USER ${user}

ENV KUBECONFIG $HOME/.kube/config.yaml
WORKDIR /home/operator

COPY . /home/operator/
    
CMD kopf run --log-format=full $HOME/smoketest-operator.py
