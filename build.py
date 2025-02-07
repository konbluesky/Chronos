#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chronos打包脚本
使用PyInstaller将程序打包成独立可执行文件
"""

import os
import sys
import PyInstaller.__main__

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
        '--hidden-import=python-crontab',
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
            '--target-arch=arm64',
            '--codesign-identity=',  # 不使用代码签名
            '--osx-bundle-identifier=com.konbluesky.chronos',
            '--windowed',
            '--onedir',
            '--osx-bundle-identifier=com.konbluesky.chronos',
            '--name=Chronos',
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
            settings = {
                'format': 'UDBZ',
                'size': '100M',
                'files': ['dist/Chronos.app'],
                'symlinks': {'Applications': '/Applications'},
                'icon': 'icon.icns',
                'badge_icon': 'icon.icns',
                'background': 'dmg_background.png',
                'icon_size': 128,
                'window_rect': ((100, 100), (640, 480)),
                'icon_locations': {
                    'Chronos.app': (120, 240),
                    'Applications': (520, 240)
                }
            }
            dmgbuild.build_dmg('Chronos.dmg', 'Chronos', settings)
            print('DMG打包完成：Chronos.dmg')
        except ImportError:
            print('请先安装dmgbuild：pip install dmgbuild')
        except Exception as e:
            print(f'创建DMG时出错：{str(e)}')


if __name__ == '__main__':
    build()