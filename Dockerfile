# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sudo \
    ca-certificates \
    clang \
    ccache \
    && rm -rf /var/lib/apt/lists/*

# --- Incremental-build configuration ----------------------------------------
# ccache keys cached object files on *preprocessed source content*, so edits to
# open_spiel only recompile the translation units that actually changed; the
# rest are served from the cache. CMake reads the launcher vars below the
# first time a build tree is configured.
ENV CC=clang \
    CXX=clang++ \
    CMAKE_C_COMPILER_LAUNCHER=ccache \
    CMAKE_CXX_COMPILER_LAUNCHER=ccache \
    CCACHE_DIR=/ccache \
    CCACHE_BASEDIR=/open_spiel \
    CCACHE_MAXSIZE=5G \
    CCACHE_SLOPPINESS=include_file_mtime,include_file_ctime,time_macros \
    DOWNLOAD_CACHE_DIR=/download_cache
# Clone our open_spiel fork and build it here, so the image is self-contained
# and requires nothing beyond `docker build` (no sibling host checkout, no
# postCreateCommand). The cache mounts persist ccache/download_cache across
# image rebuilds on the same builder without baking them into the image.
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

# Builds open-spiel from /open_spiel (using CC/CXX/ccache above) along with
# the rest of the dependency set. This has no [build-system] table, so uv
# never builds/installs the root "t" package here — kept before COPY src so
# source edits don't invalidate this (expensive, C++-build-inclusive) layer.
RUN uv sync --locked

# Installs this project in editable mode so host-mounted edits under
# /workspace/src are picked up without a rebuild.
COPY src ./src
RUN uv pip install --python /opt/venv/bin/python -e .