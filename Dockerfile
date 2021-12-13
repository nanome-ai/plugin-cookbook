FROM jupyter/minimal-notebook

USER root
RUN conda install -c rdkit rdkit

RUN npm install
# RUN jupyterlab --generate-config
USER jovyan

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .