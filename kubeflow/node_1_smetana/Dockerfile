FROM mambaorg/micromamba:latest
USER root

WORKDIR /app

COPY environment.yml /app/environment.yml
COPY script.py /app/

RUN micromamba env create -n smetana -f environment.yml

ENTRYPOINT ["micromamba", "run", "-n", "smetana", "python", "script.py"]