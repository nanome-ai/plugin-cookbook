FROM continuumio/miniconda3:latest

WORKDIR /app
ENV NODE_VERSION=16.13.1
RUN apt-get update
RUN apt-get install -y curl

# Install Node and NPM.
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
RUN node --version
RUN npm --version

# RUN npm install
COPY package.json .
# COPY package-lock.json .
RUN npm install 

RUN conda install -c conda-forge jupyterlab

ENV username=jupyter
RUN useradd -ms /bin/bash $username

COPY . .
USER $username

RUN pip install -r requirements.txt

CMD jupyter lab 
