FROM python:3.10-alpine
RUN apk add py3-pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY generate_site.py /generate_site.py
ENTRYPOINT ["/generate_site.py"]
