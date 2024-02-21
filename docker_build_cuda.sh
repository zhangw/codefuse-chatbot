#!/bin/bash

docker build -t devopsgpt:py39-cuda -f Dockerfile-cuda .

# run a container, and build the autogptq
docker run --name temp-container devopsgpt:py39-cuda /home/user/install-autogptq.sh

docker commit -m 'autogptq installed' temp-container devopsgpt:py39