FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY script.py /app/
COPY build_taxa_table.py /app/
COPY build_cgem.py /app/
COPY get_elasticities.py /app/
COPY get_exchanges.py /app/
COPY get_medium_from_media_db.py /app/

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "script.py"]
