ARG BUILD_FROM
FROM ${BUILD_FROM}

# ---------------------------------------------------------------------------
# System packages — v2.0 + Part II (God Mode delta)
# ---------------------------------------------------------------------------
# Build toolchain (paramiko/cryptography/onvif), shell power-tools (rg, git,
# ssh, sqlite, docker), networking (tcpdump, nmap, iproute2, bind-tools),
# hardware (i2c-tools, lirc, bluez, rtl-sdr, uhubctl), wireguard, ipmitool,
# ffmpeg + sshpass + tshark for forensics / multimedia / replication.
RUN apk add --no-cache \
    python3 py3-pip py3-setuptools py3-wheel \
    build-base python3-dev libffi-dev openssl-dev cargo rust \
    bash coreutils findutils grep tar gzip unzip \
    curl iputils bind-tools iproute2 \
    ripgrep git openssh-client sshpass sqlite docker-cli \
    tcpdump nmap tshark \
    i2c-tools lirc bluez rtl_433 rtl-sdr uhubctl \
    wireguard-tools ipmitool ffmpeg \
    py3-serial \
    || apk add --no-cache python3 py3-pip py3-setuptools py3-wheel build-base \
       python3-dev libffi-dev openssl-dev cargo rust bash coreutils findutils \
       grep tar gzip unzip curl iputils bind-tools iproute2 ripgrep git \
       openssh-client sqlite docker-cli ffmpeg

# Virtual environment to dodge PEP 668
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY app/ /app/
COPY run.sh /
RUN chmod a+x /run.sh

WORKDIR /
ENV PYTHONUNBUFFERED=1

CMD [ "/run.sh" ]
ARG BUILD_FROM
FROM ${BUILD_FROM}

# System packages: compilers (paramiko/cryptography), shell tools, ripgrep,
# git, openssh-client, sqlite cli, docker cli for shell_exec helpers.
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    ripgrep \
    git \
    openssh-client \
    sqlite \
    docker-cli \
    curl \
    iputils \
    bind-tools \
    iproute2 \
    bash \
    coreutils \
    findutils \
    grep \
    tar \
    gzip \
    unzip

# Virtual environment to dodge PEP 668
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY app/ /app/
COPY run.sh /
RUN chmod a+x /run.sh

WORKDIR /

ENV PYTHONUNBUFFERED=1

CMD [ "/run.sh" ]
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python 3 and pip
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools

# Create a virtual environment to avoid PEP 668 issues
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy application code
COPY app/ /app/

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /

# Ensure unbuffered output
ENV PYTHONUNBUFFERED=1

CMD [ "/run.sh" ]
