# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS open_spiel

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    sudo \
    ca-certificates \
    clang \
    ccache \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade build setuptools wheel cmake ninja

# --- Incremental-build configuration ----------------------------------------
# /open_spiel is not baked into the image: it's bind-mounted at container
# runtime from a sibling checkout of the open_spiel fork on the host (see
# .devcontainer/devcontainer.json), so there's a single source of truth instead
# of a separate host clone plus an image-baked clone that can drift apart.
# ccache keys cached object files on *preprocessed source content*, so edits to
# the mounted checkout only recompile the translation units that actually
# changed; the rest are served from the cache. CMake reads the launcher vars
# below the first time a build tree is configured.
ENV CC=clang \
    CXX=clang++ \
    CMAKE_C_COMPILER_LAUNCHER=ccache \
    CMAKE_CXX_COMPILER_LAUNCHER=ccache \
    CCACHE_DIR=/ccache \
    CCACHE_BASEDIR=/open_spiel \
    CCACHE_MAXSIZE=5G \
    CCACHE_SLOPPINESS=include_file_mtime,include_file_ctime,time_macros \
    DOWNLOAD_CACHE_DIR=/download_cache
RUN mkdir -p /ccache /open_spiel

WORKDIR /workspace

RUN pip install uv
# Cache mounts live on a separate filesystem, so uv can't hardlink from the
# cache into the venv; copy instead of warning + falling back per file.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
COPY pyproject.toml .python-version ./

# open_spiel isn't built here: at image-build time /open_spiel is empty (the
# bind mount only exists once the container starts), so install.sh and
# `uv sync` run from the devcontainer's postCreateCommand instead. This layer
# just makes sure the rest of the toolchain is ready to go by then.
