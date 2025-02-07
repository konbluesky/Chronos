#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chronos打包脚本
使用PyInstaller将程序打包成独立可执行文件
"""

import os
import sys
import PyInstaller.__main__
from pathlib import Path

def build():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置打包参数
    args = [
        'main.py',  # 主程序文件
        '--name=Chronos',  # 应用名称
        '--windowed',  # 使用GUI模式
        f'--icon={os.path.join(current_dir, "icon.png")}',  # 应用图标
        '--clean',  # 清理临时文件
        '--noconfirm',  # 不确认覆盖
        # 添加数据文件
        f'--add-data={os.path.join(current_dir, "icon.png")}:.',
        f'--add-data={os.path.join(current_dir, "icon.svg")}:.',
        # 设置Info.plist选项（macOS）
        '--osx-bundle-identifier=com.konbluesky.chronos',
        # 隐藏控制台窗口
        '--noconsole',
        # 添加必要的依赖
        '--collect-submodules=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtSvg',
        '--hidden-import=PyQt6.QtSvgWidgets',
        '--hidden-import=crontab',
        '--collect-submodules=crontab',
        '--add-data=Info.plist:.',
        # 优化macOS打包配置
        '--osx-bundle-identifier=com.konbluesky.chronos'
    ]
    
    # 如果是macOS系统，添加特定配置
    if sys.platform == 'darwin':
        args.extend([
            '--runtime-tmpdir=.',  # 设置运行时临时目录
            '--osx-entitlements-file=',  # 不使用entitlements文件
            '--disable-windowed-traceback',  # 禁用窗口化错误回溯
            '--target-arch=arm64',  # 使用系统原生架构
            # DMG打包配置
            '--codesign-identity=',  # 不使用代码签名
            '--windowed',
            '--onedir',
            '--icon=icon.icns',
            '--add-data=icon.icns:.',
            '--add-data=icon.png:.',
            '--add-data=icon.svg:.',
            '--add-data=Info.plist:.',
            '--clean',
            '--noconfirm'
        ])
    
    # 运行PyInstaller
    PyInstaller.__main__.run(args)
    
    # 如果是macOS系统，创建DMG
    if sys.platform == 'darwin':
        try:
            import dmgbuild
            app_path = os.path.join(current_dir, 'dist', 'Chronos.app')
            icon_path = os.path.join(current_dir, 'icon.icns')
            settings = {
                'format': 'UDBZ',
                'size': '500M',
                'files': [str(app_path)],  # 转换为字符串
                'symlinks': {'Applications': '/Applications'},
                'icon': str(icon_path),  # 转换为字符串
                'badge_icon': str(icon_path),  # 转换为字符串
                'background': None,
                'icon_size': 128,
                'window_rect': ((100, 100), (640, 480)),
                'icon_locations': {
                    'Chronos.app': (120, 240),
                    'Applications': (520, 240)
                },
                'show_status_bar': False,
                'show_tab_view': False,
                'show_toolbar': False,
                'show_pathbar': False,
                'show_sidebar': False
            }
            dmgbuild.build_dmg(os.path.join(current_dir, 'Chronos.dmg'), 'Chronos', settings=settings)
            print('DMG打包完成：Chronos.dmg')
        except ImportError:
            print('请先安装dmgbuild：pip install dmgbuild')
        except Exception as e:
            import traceback
            print(f'创建DMG时出错：{str(e)}')
            print('错误堆栈信息：')
            traceback.print_exc()


if __name__ == '__main__':
    build()