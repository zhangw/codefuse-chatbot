#!/bin/bash
# install autogptq from source code on a running container (not during the docker image building)
# more details, please see: https://github.com/pytorch/extension-cpp/issues/71
python -c 'import torch; print(".".join(map(str, torch.cuda.get_device_capability(0))))'
python -c 'import torch; print(torch.cuda.device_count())'
python -c 'import torch; print(torch.cuda.get_arch_list())'
pip install gekko
pip install -e /opt/AutoGPTQ-0.6.0