from os import path
from pathlib import Path
import shutil

proj_dir = Path(__file__).parent
code_dir = proj_dir.joinpath('slam')
handin_dir = proj_dir.joinpath("handin")

shutil.make_archive(handin_dir, 'zip', code_dir)
