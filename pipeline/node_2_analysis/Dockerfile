FROM python:3.10

WORKDIR /app

# Install system dependencies including CMake and curl
RUN apt-get update && \
    apt-get install -y cmake curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
COPY entrypoint.py /app/
COPY build_taxa_table.py /app/
COPY build_cgem.py /app/
COPY cgem_utils.py /app/
COPY grow_workflow.py /app/
COPY get_elasticities.py /app/
COPY get_exchanges.py /app/
COPY get_medium_from_media_db.py /app/

# Install requirements
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download and install the wheel file
RUN curl -L https://github.com/Robaina/cgem-forge/raw/main/dist/cgemforge-0.0.2-py3-none-any.whl -o cgemforge-0.0.2-py3-none-any.whl && \
    pip install cgemforge-0.0.2-py3-none-any.whl && \
    rm cgemforge-0.0.2-py3-none-any.whl

ENTRYPOINT ["python", "entrypoint.py"]