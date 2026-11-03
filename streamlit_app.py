# Entry point for Streamlit Community Cloud, which cannot install requirements from a folder name with a space.
# The dashboard itself is 05 Code/app.py.
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "05 Code" / "app.py"), run_name="__main__")
