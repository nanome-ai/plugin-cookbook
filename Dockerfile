FROM jupyter/minimal-notebook

COPY . .

USER root
RUN npm install
USER jovyan
RUN pip install -r requirements.txt
