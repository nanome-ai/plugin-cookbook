#!/bin/bash

uri=public.ecr.aws/h7r1e4h2/cookbook
tag=latest
docker-compose build
docker tag plugin-cookbook_cookbook:latest $uri:$tag
docker push $uri:$tag
cd /home/mike/workspace/helm-charts && helm uninstall test && helm install test -f values-cookbook.yaml nanome/plugins/cookbook