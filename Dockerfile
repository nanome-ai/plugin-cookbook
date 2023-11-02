FROM continuumio/miniconda3:4.10.3

WORKDIR /app
ENV NODE_VERSION=16.13.1

RUN apt-get --allow-releaseinfo-change update && apt-get -y upgrade
RUN apt-get install -y curl build-essential

# Set up jupyter conda environment
RUN conda update conda
RUN conda install -c conda-forge jupyterlab rdkit pip

# Install Node and NPM.
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"
COPY package.json .
RUN npm install

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

WORKDIR /app/cookbook
RUN jupyter server --generate-config
CMD jupyter lab --ip 0.0.0.0 --allow-root
