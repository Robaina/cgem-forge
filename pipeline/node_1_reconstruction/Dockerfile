FROM mambaorg/micromamba:latest

USER root
WORKDIR /app

# Install system dependencies including git and curl
RUN apt-get update && apt-get install -y \
    libexpat1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file and entrypoint
COPY environment.yml /app/environment.yml
COPY entrypoint.py /app/

# Create conda environment
RUN micromamba env create -n carveme -f environment.yml

# Download and install the wheel file
RUN curl -L https://github.com/Robaina/cgem-forge/raw/main/dist/cgemforge-0.0.2-py3-none-any.whl -o cgemforge-0.0.2-py3-none-any.whl \
    && micromamba run -n carveme pip install cgemforge-0.0.2-py3-none-any.whl \
    && rm cgemforge-0.0.2-py3-none-any.whl

ENTRYPOINT ["micromamba", "run", "-n", "carveme", "python", "entrypoint.py"]