# 2d-movie

The complete original animation project is extracted in [`Everyday_English_Project/`](Everyday_English_Project/README.md). The source ZIP has been removed; all 37 archived files are preserved in that folder.

To render Episode 01 with Python 3.11/3.12 and FFmpeg installed:

```sh
cd Everyday_English_Project
python -m pip install -r requirements.txt
python action_render.py --preview
python render_all.py --workers 2
```

See [Episode 02](episode2/README.md) for the continuation workflow. The original preview MP4 remains at the repository root.
