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
# A fresh `git checkout` rewrites every source file's mtime to "now", so a
# reused CMake build tree would recompile everything regardless. ccache sidesteps
# that by keying cached object files on the *preprocessed source content*: when
# you move to a newer commit, only the translation units that actually changed
# are recompiled; the rest are served from the cache. CMake reads the launcher
# vars below the first time a build tree is configured.
ENV CC=clang \
    CXX=clang++ \
    CMAKE_C_COMPILER_LAUNCHER=ccache \
    CMAKE_CXX_COMPILER_LAUNCHER=ccache \
    CCACHE_DIR=/ccache \
    CCACHE_BASEDIR=/open_spiel \
    CCACHE_MAXSIZE=5G \
    CCACHE_SLOPPINESS=include_file_mtime,include_file_ctime,time_macros \
    DOWNLOAD_CACHE_DIR=/download_cache

ARG OPEN_SPIEL_REF=82c4d12f8e8354e8ef99cd82a55df10260090feb
RUN git clone https://github.com/Turu-Tamas/open_spiel.git /open_spiel \
    && cd /open_spiel \
    && git checkout ${OPEN_SPIEL_REF}

WORKDIR /open_spiel

# Fetch the C++ dependencies (abseil, pybind11, dds, ...). install.sh stores them
# under $DOWNLOAD_CACHE_DIR; a cache mount there avoids re-downloading them every
# time OPEN_SPIEL_REF changes.
RUN --mount=type=cache,target=/download_cache,sharing=locked \
    ./install.sh

# Build the wheel. --no-isolation keeps the build in the stable /open_spiel/build
# tree so ccache sees identical compile command lines (and thus cache hits)
# across commits; without it, `build` compiles in a random temp dir and every
# object misses the cache. The /ccache mount is where the reusable object cache
# lives; dist/ is not mounted, so the produced wheel stays in the image layer.
RUN --mount=type=cache,target=/ccache \
    python -m build --wheel --no-isolation \
    && ccache --show-stats


FROM python:3.13-slim AS runtime

WORKDIR /workspace

RUN pip install uv
# Cache mounts live on a separate filesystem, so uv can't hardlink from the
# cache into the venv; copy instead of warning + falling back per file.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
COPY pyproject.toml .python-version ./
COPY --from=open_spiel /open_spiel/dist/*.whl wheels/
# Persist uv's download/build cache so unchanged dependencies aren't refetched
# or rebuilt on subsequent image builds.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
COPY --from=open_spiel /open_spiel /open_spiel