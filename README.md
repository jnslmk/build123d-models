# build123d-models

Collection of 3D printable models built with [build123d](https://github.com/gumyr/build123d).

## Setup

```bash
uv sync
```

## Viewing Models

Start the viewer server (Catppuccin Mocha themed):

```bash
uv run viewer
```

Open `http://127.0.0.1:3939` in your browser.

In another terminal, run a model:

```bash
uv run model cube
```

The model will appear in the browser viewer.

## Building All Models

```bash
uv run python main.py
```

Exports are saved to `exports/` as STEP and STL files.

## Models

| Model | Description |
|-------|-------------|
| `cube.py` | Simple 20mm cube |
