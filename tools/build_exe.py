"""Builds AntaresIDE.exe (one file, with the icon, help and examples inside) with PyInstaller.

  python tools/build_exe.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sep = ";" if sys.platform == "win32" else ":"
work = HERE / "build"
# With Anaconda's Python, Tk's DLLs (tcl86t, tk86t, zlib) are in Libraryin, which is
# only on the PATH in an activated Anaconda prompt; put it there so they are found.
env = dict(os.environ)
conda_bin = Path(sys.prefix) / "Library" / "bin"
if conda_bin.is_dir():
    env["PATH"] = str(conda_bin) + os.pathsep + env.get("PATH", "")
subprocess.run([
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
    "--name", "AntaresIDE", "--icon", str(HERE / "assets" / "icon.ico"),
    "--add-data", f"{HERE / 'assets'}{sep}assets",
    "--add-data", f"{HERE / 'examples'}{sep}examples",
    # only the standard library is used (PIL is just for the self-test's screenshots)
    *[x for m in ["PIL", "numpy", "setuptools", "pkg_resources", "distutils", "pydoc", "unittest", "email", "http",
                   "xml", "xmlrpc", "multiprocessing", "sqlite3", "lib2to3", "test"] for x in ("--exclude-module", m)],
    "--distpath", str(work / "dist"), "--workpath", str(work / "tmp"), "--specpath", str(work),
    str(HERE / "antares_ide.py"),
], check=True, cwd=HERE, env=env)
exe = work / "dist" / ("AntaresIDE.exe" if sys.platform == "win32" else "AntaresIDE")
target = HERE / exe.name
shutil.copy2(exe, target)
shutil.rmtree(work, ignore_errors=True)
print(f"Built {target} ({target.stat().st_size // 1024 // 1024} MB)")
