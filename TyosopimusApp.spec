# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude large standard-library modules the app and its dependencies
    # (PyQt5, reportlab) never import, shrinking the frozen bundle and the
    # analysis/freeze work PyInstaller performs at build time.
    excludes=[
        'tkinter', 'tcl', 'unittest', 'pydoc', 'doctest', 'pdb',
        'profile', 'pstats', 'idlelib', 'turtle', 'ensurepip', 'venv',
        'distutils', 'lib2to3',
    ],
    noarchive=False,
    # Optimize frozen bytecode (drop docstrings and asserts) for smaller
    # modules and slightly faster module load at startup.
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Työsopimuskone',
    debug=False,
    bootloader_ignore_signals=False,
    # Strip debug symbols from the Mach-O executable for a smaller release bundle.
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='Työsopimuskone.app',
    icon='assets/app_icon.icns',
    bundle_identifier=None,
)
