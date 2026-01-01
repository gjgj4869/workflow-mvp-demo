FROM apache/airflow:2.8.1-python3.11

USER root

# Install system dependencies and Docker client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add airflow user to docker group (GID 961 matches host)
RUN groupadd -g 961 docker || true \
    && usermod -aG docker airflow

USER airflow

# Install additional Python packages
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
