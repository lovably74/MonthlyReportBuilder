# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CM Report Server.

이 파일은 서버를 단일 디렉토리(onedir)로 패키징합니다.
build.bat에서 자동으로 사용되지만, 수동 실행도 가능합니다:

    cd h:\projects\MonthlyReportBuilder\server
    .venv\Scripts\activate
    pyinstaller ..\installer\server.spec
"""

import os
import sys
from pathlib import Path

# 서버 소스 경로
server_dir = Path(os.path.abspath(SPECPATH)).parent / 'server'

block_cipher = None

a = Analysis(
    [str(server_dir / 'app' / 'main.py')],
    pathex=[str(server_dir)],
    binaries=[],
    datas=[
        # Alembic 마이그레이션 파일 포함
        (str(server_dir / 'alembic'), 'alembic'),
        (str(server_dir / 'alembic.ini'), '.'),
    ],
    hiddenimports=[
        # SQLAlchemy async 드라이버
        'aiosqlite',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.sqlite.aiosqlite',
        # uvicorn 내부 모듈
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # FastAPI / Pydantic
        'fastapi',
        'pydantic',
        'pydantic_core',
        # zeroconf mDNS
        'zeroconf',
        'zeroconf._utils',
        # App 모듈
        'app',
        'app.main',
        'app.core',
        'app.core.database',
        'app.core.server_identity',
        'app.core.mdns_advertiser',
        'app.core.auth',
        'app.core.error_handlers',
        'app.core.exceptions',
        'app.models',
        'app.models.settings_profile',
        'app.schemas',
        'app.schemas.profile',
        'app.repositories',
        'app.repositories.profile_repository',
        'app.services',
        'app.services.profile_service',
        'app.routers',
        'app.routers.profile_router',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cm-report-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 서버는 콘솔 앱
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cm-report-server',
)
