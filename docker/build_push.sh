#!/bin/bash
repo="public.ecr.aws/h7r1e4h2/cookbook"
tag="hub4"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker build -t  $repo:$tag $SCRIPT_DIR/..

docker push  $repo:$tag

# kubectl rollout restart deployment hub proxy user-scheduler
