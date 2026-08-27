# Official RunPod PyTorch image: CUDA 12.8.1 + torch 2.8, pre-cached on hosts.
# Do not override CMD — the base image's /start.sh owns SSH/Jupyter.
# Per-pod work runs from /post_start.sh after sshd is up.
#
#   docker build --platform=linux/amd64 -t YOUR_REGISTRY/ramsey-gpu:latest .
#   # On runpod.io: set Container image, then environment:
#   #   RAMSEY_JOB=1a          (one of phase0,1a,1b,1c,1d,2a,2b,2c,3a,3b,3c,3d)
#   #   RAMSEY_SCALE=runpod
# Launch 2–4 pods with distinct RAMSEY_JOB so they do not overlap cells.
# See README.md "RunPod".

FROM runpod/pytorch:1.0.3-cu1281-torch280-ubuntu2404

WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

COPY engine/ /workspace/engine/
COPY data/ /workspace/data/
COPY post_start.sh /post_start.sh
RUN chmod +x /post_start.sh && mkdir -p /workspace/data

# Inherit CMD ["/start.sh"] from the base image.
