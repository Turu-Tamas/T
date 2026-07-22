FROM python:3.13-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y git sudo
RUN pip install uv

RUN git clone https://github.com/Turu-Tamas/open_spiel.git
RUN mkdir wheels

WORKDIR /workspace/open_spiel
RUN ./install.sh
RUN python -m pip install --upgrade build
RUN python -m build
RUN cp ./dist/*.whl /workspace/wheels/
WORKDIR /workspace

ENV UV_PROJECT_ENVIRONMENT=/opt/venv
COPY pyproject.toml .python-version /workspace/
RUN uv sync