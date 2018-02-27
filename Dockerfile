FROM python:3.6.4-alpine

ADD https://storage.googleapis.com/kubernetes-release/release/v1.9.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD listener.py listener.py
ADD network.py network.py
ADD k8s.py k8s.py

ENTRYPOINT ["python", "listener.py"]

