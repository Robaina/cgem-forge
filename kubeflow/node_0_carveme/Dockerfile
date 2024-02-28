FROM mambaorg/micromamba:latest
USER root

WORKDIR /app

COPY environment.yml /app/environment.yml
COPY script.py /app/

RUN micromamba env create -n carveme -f environment.yml

ENTRYPOINT ["micromamba", "shell", "exec", "-n", "carveme", "--", "python", "script.py"]