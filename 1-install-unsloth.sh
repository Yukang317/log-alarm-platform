#!/bin/sh

apt update
apt upgrade -y
apt install -y cmake
apt install -y libcurl4-gnutls-dev

pip install uv
uv tool install modelscope
uv tool update-shell

uv init proj_t1
cd proj_t1 && uv add huggingface-hub==0.36.0 && uv add modelscope==1.33.0 && uv add unsloth-zoo==2025.10.1 && uv add unsloth==2025.10.1
