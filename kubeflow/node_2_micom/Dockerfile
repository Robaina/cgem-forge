FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY script.py /app/

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "script.py"]
