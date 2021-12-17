#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

echo "./deploy.sh $*" > redeploy.sh
chmod +x redeploy.sh

docker-compose up
