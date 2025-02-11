FROM mambaorg/micromamba:latest
USER root

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY environment.yml /app/environment.yml
COPY entrypoint.py /app/

RUN micromamba env create -n carveme -f environment.yml

ENTRYPOINT ["micromamba", "run", "-n", "carveme", "python", "entrypoint.py"]