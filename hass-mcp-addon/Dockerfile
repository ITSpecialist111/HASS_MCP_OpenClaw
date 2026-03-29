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
