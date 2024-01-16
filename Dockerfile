# Use miniconda image
FROM continuumio/miniconda3:4.10.3

# Set environment variables
ENV NODE_VERSION=16.13.1 \
    NVM_DIR=/opt/nvm

RUN conda update conda

# Create a non-root user
RUN useradd -m -s /bin/bash jupyteruser && \
    mkdir -p /app /opt/nvm && \
    chown -R jupyteruser:jupyteruser /app /opt/nvm
# Switch to non-root user
USER jupyteruser

# Set working directory
WORKDIR /app

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install JupyterLab, RDKit, Pip
# Copy pip requirements and install 
RUN conda install -c conda-forge jupyterlab
COPY --chown=jupyteruser:jupyteruser requirements.txt .
RUN pip install -r requirements.txt

USER jupyteruser

# Install Node.js using NVM
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash && \
    . "$NVM_DIR/nvm.sh" && \
    nvm install ${NODE_VERSION} && \
    nvm alias default ${NODE_VERSION} && \
    nvm use default

# Update PATH for Node.js
ENV PATH="/opt/nvm/versions/node/v${NODE_VERSION}/bin:${PATH}"

# Copy and install NPM and Python dependencies
COPY --chown=jupyteruser:jupyteruser package.json .
RUN npm install 

# Copy the rest of the application
COPY --chown=jupyteruser:jupyteruser . /app/

# Set the working directory for JupyterLab
WORKDIR /app/cookbook

# Generate Jupyter config
RUN jupyter lab server --generate-config

# Expose the port JupyterLab will use
EXPOSE 8888

# Run JupyterLab
CMD ["jupyter", "lab", "--ip", "0.0.0.0", "--no-browser"]
