#!/bin/bash

uri=public.ecr.aws/h7r1e4h2/cookbook
tag=latest
docker-compose build
docker tag plugin-cookbook_cookbook:latest $uri:$tag
docker push $uri:$tag