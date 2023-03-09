FROM python:3.10-alpine
RUN apk add py3-pip
RUN pip install Jinja2==3.1.2
COPY generate_site.py /generate_site.py
ENTRYPOINT ["/generate_site.py"]
