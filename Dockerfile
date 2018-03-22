FROM python:3.6.4

ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD bot.py bot.py
ADD interactions.py interactions.py
ADD k8s_funcs.py k8s_funcs.py

ENTRYPOINT ["python", "bot.py"]
CMD ["slack"]
