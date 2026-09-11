# syntax=docker/dockerfile:1

# CUDA development image.
# "devel" includes the CUDA compiler/toolkit needed to build CUDA extensions.
FROM nvidia/cuda:13.3.1-cudnn-devel-ubuntu26.04

# Install Python 3.14 and build dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.14 \
    python3.14-dev \
    python3.14-venv \
    git \
    sudo \
    ca-certificates \
    clang \
    ccache \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Make Python 3.14 the default python/python3.
RUN ln -sf /usr/bin/python3.14 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.14 /usr/local/bin/python3

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# --- Incremental-build configuration ----------------------------------------
# ccache keys cached object files on preprocessed source content, so edits to
# open_spiel only recompile the translation units that actually changed.
#
# CMake reads the launcher vars the first time a build tree is configured.
ENV CC=clang \
    CXX=clang++ \
    CMAKE_C_COMPILER_LAUNCHER=ccache \
    CMAKE_CXX_COMPILER_LAUNCHER=ccache \
    CCACHE_DIR=/ccache \
    CCACHE_BASEDIR=/open_spiel \
    CCACHE_MAXSIZE=5G \
    CCACHE_SLOPPINESS=include_file_mtime,include_file_ctime,time_macros \
    DOWNLOAD_CACHE_DIR=/download_cache

# CUDA environment.
ENV CUDA_HOME=/usr/local/cuda \
    PATH=/usr/local/cuda/bin:${PATH} \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH}

# Clone our open_spiel fork and build it here, so the image is self-contained.
#
# The cache mounts persist ccache/download_cache across image rebuilds on the
# same builder without baking them into the image.
RUN --mount=type=cache,target=/ccache \
    --mount=type=cache,target=/download_cache \
    git clone https://github.com/Turu-Tamas/open_spiel.git /open_spiel \
    && cd /open_spiel \
    && ./install.sh

WORKDIR /workspace

# Cache mounts live on a separate filesystem, so uv can't hardlink from the
# cache into the venv; copy instead of warning + falling back per file.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock .python-version ./

# Build/install dependencies before copying src so source edits don't invalidate
# this expensive layer.
RUN uv sync

# Install this project in editable mode so host-mounted edits under
# /workspace/src are picked up without rebuilding the image.
COPY src ./src
RUN uv pip install --python /opt/venv/bin/python -e .

# Make the virtual environment the default Python environment.
ENV PATH=/opt/venv/bin:${PATH}

WORKDIR /workspace