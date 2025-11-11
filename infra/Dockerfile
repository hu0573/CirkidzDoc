# syntax=docker/dockerfile:1.6

ARG UBUNTU_VERSION=22.04

FROM ubuntu:${UBUNTU_VERSION} AS base

ENV DEBIAN_FRONTEND=noninteractive

# System prerequisites and Python 3.11 from deadsnakes PPA
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        locales \
        lsb-release \
        software-properties-common \
    && locale-gen en_US.UTF-8 zh_CN.UTF-8 \
    && update-locale LANG=en_US.UTF-8 \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        fontconfig \
        fonts-dejavu \
        fonts-noto-cjk \
        ghostscript \
        imagemagick \
        libreoffice \
        libreoffice-java-common \
        libffi-dev \
        libjpeg-dev \
        libopenjp2-7 \
        libpq-dev \
        libqpdf28 \
        libqpdf-dev \
        libssl-dev \
        libxml2 \
        libxml2-dev \
        libxslt1-dev \
        pandoc \
        pdftk-java \
        poppler-utils \
        qpdf \
        tesseract-ocr \
        tzdata \
        unoconv \
        wget \
    && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-distutils \
        python3.11-venv \
    && python3.11 -m ensurepip --upgrade \
    && python3.11 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

FROM base AS deps-builder

RUN python3.11 -m pip install --no-cache-dir uv

WORKDIR /opt/requirements
COPY infra/python/requirements.txt /opt/requirements/requirements.txt
RUN uv pip download \
        --python 3.11 \
        --target /opt/requirements/wheels \
        --requirement /opt/requirements/requirements.txt

FROM base AS runtime

COPY --from=deps-builder /opt/requirements /opt/requirements

RUN python3.11 -m pip install --no-cache-dir uv \
    && python3.11 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-index --find-links=/opt/requirements/wheels \
        -r /opt/requirements/requirements.txt \
    && rm -rf /opt/requirements/wheels

COPY infra/scripts /opt/scripts

RUN useradd -ms /bin/bash appuser \
    && chown -R appuser:appuser /opt/scripts \
    && chmod +x /opt/scripts/*.sh

ENV PATH="/opt/venv/bin:$PATH"
ENV RENDER_TMP_DIR=/workspace/tmp \
    RENDER_OUTPUT_DIR=/workspace/output

USER appuser
WORKDIR /workspace

ENTRYPOINT ["/opt/scripts/entrypoint.sh"]
CMD ["bash"]

