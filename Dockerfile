FROM jupyter/minimal-notebook

COPY . .
RUN pip install -r requirements.txt
