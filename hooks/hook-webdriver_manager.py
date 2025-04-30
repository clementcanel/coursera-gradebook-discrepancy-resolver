# hook-webdriver_manager.py
from PyInstaller.utils.hooks import collect_submodules

# collect all submodules of webdriver_manager so they’re included
hiddenimports = collect_submodules('webdriver_manager')