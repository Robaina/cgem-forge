FROM mambaorg/micromamba:latest

USER root

WORKDIR /app

# Install system dependencies including git
RUN apt-get update && apt-get install -y \
    libexpat1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file and entrypoint
COPY environment.yml /app/environment.yml
COPY entrypoint.py /app/

# Create conda environment
RUN micromamba env create -n carveme -f environment.yml


ENTRYPOINT ["micromamba", "run", "-n", "carveme", "python", "entrypoint.py"]