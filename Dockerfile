# Use mambaforge as the base image
FROM condaforge/mambaforge:latest

ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
ENV NVIDIA_REQUIRE_CUDA "cuda>=8.0"
ENV NODE_VERSION=16.13.1

WORKDIR /app

# Set DEBIAN_FRONTEND to noninteractive to avoid prompts during build
ENV DEBIAN_FRONTEND noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libtiff5 \
    gnupg2 \
    wget \
    dpkg \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb \
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && apt-get update \
    && apt-get install -y cuda-toolkit-11-8

# Install Python, PyTorch with GPU support, ESM, Nanome, and JupyterLab
RUN mamba update --all --yes && \
    mamba install -y python=3.10 pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch && \
    pip install fair-esm nanome && \
    pip install omegaconf && \
    pip install openfold && \
    mamba install -y -c conda-forge jupyterlab numpy swig sphinx sphinx_rtd_theme mdanalysis simpletraj ncurses openbabel rdkit pip pdbfixer openmm openff-toolkit openmmforcefields

# Copy the Python script to the container
#COPY ./download_esm_model.py /app/download_esm_model.py

# Run the script to download the models
#RUN python /app/download_esm_model.py

# Continue with the rest of your Dockerfile setup

# Directly install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Create a non-root user
RUN useradd -m -s /bin/bash jupyteruser && \
    chown -R jupyteruser:jupyteruser /app

USER jupyteruser

# Copy pip requirements and install additional dependencies
COPY --chown=jupyteruser:jupyteruser requirements.txt /app/
RUN pip install --user -r requirements.txt

# Copy and install NPM and Python dependencies
COPY --chown=jupyteruser:jupyteruser package.json /app/
RUN npm install 

# Copy the rest of the application
COPY --chown=jupyteruser:jupyteruser . /app/

# Set the working directory for JupyterLab
WORKDIR /app/cookbook

EXPOSE 8888

# Run JupyterLab
CMD ["jupyter", "lab", "--ip", "0.0.0.0", "--no-browser"]
