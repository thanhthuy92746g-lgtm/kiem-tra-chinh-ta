# Run on Windows x64. ONEDIR, shared dependencies; data copied by package_windows.py.
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
excludes = ['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
            'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtNetwork',
            'PySide6.QtMultimedia', 'PySide6.Qt3DCore', 'tkinter', 'pytest']

gui = Analysis([str(ROOT / 'packaging/gui_entry.py')], pathex=[str(ROOT / 'src')],
               excludes=excludes)
cli = Analysis([str(ROOT / 'packaging/cli_entry.py')], pathex=[str(ROOT / 'src')],
               excludes=excludes)
gui_pyz = PYZ(gui.pure)
cli_pyz = PYZ(cli.pure)
gui_exe = EXE(gui_pyz, gui.scripts, [], exclude_binaries=True, name='VietSpell',
              console=False, upx=False)
cli_exe = EXE(cli_pyz, cli.scripts, [], exclude_binaries=True, name='vietspell-cli',
              console=True, upx=False)
bundle = COLLECT(gui_exe, cli_exe, gui.binaries, cli.binaries, gui.datas, cli.datas,
                 strip=False, upx=False, name='VietSpell')
