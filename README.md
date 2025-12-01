# build123d-models

Collection of 3D printable models built with [build123d](https://github.com/gumyr/build123d).

## Setup

```bash
uv sync
```

## Viewing Models

Start the transparent viewer:

```bash
uv run viewer
```

In another terminal, run a model:

```bash
uv run model cube
```

The model will appear in the viewer window.

## Rendering to SVG

Generate SVG projections without a viewer:

```bash
uv run render cube                    # exports/cube_iso.svg
uv run render cube --view top         # exports/cube_top.svg
uv run render cube --view front       # exports/cube_front.svg
```

Available views: `iso`, `front`, `back`, `left`, `right`, `top`, `bottom`

## Building All Models

```bash
uv run python main.py
```

Exports are saved to `exports/` as STEP and STL files.

## Models

| Model | Description |
|-------|-------------|
| `cube.py` | Simple 20mm cube |
