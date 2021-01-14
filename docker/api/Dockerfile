FROM python:3.8

WORKDIR /code

ENV FLASK_APP api.py
ENV FLASK_RUN_HOST 0.0.0.0

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ARG GEOIP_DB_PATH
RUN if [ ! -f $GEOIP_DB_PATH ]; then python manage.py prepare_geoip_db; fi

ARG NODES_INIT_PATH
RUN python manage.py add_nodes --path $NODES_INIT_PATH

CMD flask run
