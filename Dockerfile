# Use mambaforge as the base image for broad compatibility with Conda packages
FROM condaforge/mambaforge:latest

# Environment variables for NVIDIA and CUDA
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
ENV NVIDIA_REQUIRE_CUDA "cuda>=11.0"
ENV NODE_VERSION=16.13.1

# Set the working directory in the container
WORKDIR /app

# Set DEBIAN_FRONTEND to noninteractive to avoid prompts during build
ENV DEBIAN_FRONTEND noninteractive

# Install system dependencies including CUDA toolkit
RUN apt-get update && apt-get install -y \
    curl \
    libtiff5 \
    gnupg2 \
    wget \
    dpkg \
    build-essential \
    git \
    && wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb \
    && dpkg -i cuda-keyring_1.1-1_all.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get update \
    && apt-get install -y cuda-toolkit-11-3  # Ensure CUDA toolkit version matches PyTorch requirements

# Update Conda and install Python, PyTorch with GPU support, and other scientific packages
RUN mamba update --all --yes && \
    mamba install -y python=3.10 cudatoolkit=11.3
    #pytorch torchvision torchaudio  -c pytorch

# Install JupyterLab, RDKit, and other dependencies with Conda to ensure they are correctly installed
RUN mamba install -c conda-forge jupyterlab rdkit biopython

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu113

# Install additional dependencies from OpenFold's environment.yml
RUN pip install fair-esm nanome omegaconf ml_collections dm-tree modelcif einops


# Clone OpenFold repository and install it
RUN git clone https://github.com/aqlaboratory/openfold.git /app/openfold && \
    cd /app/openfold && pip install .

# Install Node.js for JupyterLab extensions or other Node.js applications
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs

# Create a non-root user for JupyterLab to enhance security
RUN useradd -m -s /bin/bash jupyteruser && \
    chown -R jupyteruser:jupyteruser /app

# Switch to root to install system-wide dependencies and perform downloads
USER root

# Create the directory for model checkpoints
RUN mkdir -p /home/jupyteruser/.cache/torch/hub/checkpoints/ && \
    chown -R jupyteruser:jupyteruser /home/jupyteruser/.cache

USER jupyteruser

# Download the folding models directly into the cache directory
RUN wget https://dl.fbaipublicfiles.com/fair-esm/models/esmfold_3B_v1.pt -O /home/jupyteruser/.cache/torch/hub/checkpoints/esmfold_3B_v1.pt && \
    wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t36_3B_UR50D.pt -O /home/jupyteruser/.cache/torch/hub/checkpoints/esm2_t36_3B_UR50D.pt


# Install JupyterLab for the non-root user
RUN pip install --user jupyterlab

# Copy requirements.txt and install Python dependencies as the non-root user
COPY --chown=jupyteruser:jupyteruser requirements.txt /app/
RUN pip install --user -r requirements.txt

# Copy package.json for any NPM dependencies and install them
COPY --chown=jupyteruser:jupyteruser package.json /app/
RUN npm install 

# Copy the rest of the application
COPY --chown=jupyteruser:jupyteruser . /app/

# Set the working directory for JupyterLab
WORKDIR /app/cookbook

# Expose the port JupyterLab will run on
EXPOSE 8888

# Command to run JupyterLab, making it accessible from outside the container
CMD ["jupyter", "lab", "--ip", "0.0.0.0", "--no-browser"]
