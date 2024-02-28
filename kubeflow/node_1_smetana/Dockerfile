FROM mambaorg/micromamba:latest
USER root

WORKDIR /app

COPY environment.yml /app/environment.yml
COPY script.py /app/

RUN micromamba env create -n smetana -f environment.yml

ENTRYPOINT ["micromamba", "shell", "exec", "-n", "smetana", "--", "python", "script.py"]