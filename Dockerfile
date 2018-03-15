FROM python:3.6.4-alpine

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD listener.py listener.py
ADD network.py network.py
ADD k8s.py k8s.py

ENTRYPOINT ["python", "listener.py"]
CMD ["slack"]

