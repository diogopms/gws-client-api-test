FROM python:3

ADD main.py /

RUN pip install requests

CMD ["python","-u","main.py"]
