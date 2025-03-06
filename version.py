#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""版本信息管理模块"""

import os
import json
import subprocess
from pathlib import Path

# 版本文件路径
VERSION_FILE = Path(__file__).parent / '.version'

def load_build_number():
    """加载构建号"""
    try:
        if VERSION_FILE.exists():
            with open(VERSION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('build_number', 0)
        return 0
    except Exception:
        return 0

def save_build_number(build_number):
    """保存构建号"""
    try:
        with open(VERSION_FILE, 'w') as f:
            json.dump({'build_number': build_number}, f)
    except Exception:
        pass

def get_git_revision():
    """获取git提交版本信息"""
    try:
        # 检查是否在git仓库中
        subprocess.check_output(['git', 'rev-parse', '--git-dir']).decode('utf-8').strip()
        
        try:
            # 获取最新的git commit hash
            git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            git_hash = 'no-commit'
            
        try:
            # 获取最新的git tag
            git_tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).decode('utf-8').strip()
            
            # 解析主版本号和次版本号
            if '.' in git_tag:
                parts = git_tag.split('.')
                if len(parts) >= 2:
                    try:
                        major = int(parts[0].lstrip('v'))
                        minor = int(parts[1])
                        # 获取当前构建号并增加
                        build_number = load_build_number() + 1
                        save_build_number(build_number)
                        # 检查是否需要进位
                        if build_number >= 10:  # 次版本号满10进位
                            major += 1
                            build_number = 0
                            save_build_number(0)  # 重置构建号
                        git_tag = f'v{major}.{build_number}'
                    except ValueError:
                        git_tag = 'v0.0'
                else:
                    git_tag = 'v0.0'
            else:
                git_tag = 'v0.0'
                
        except subprocess.CalledProcessError:
            # 如果没有git tag，使用默认版本号
            build_number = load_build_number()
            major = build_number // 10  # 计算主版本号
            minor = build_number % 10   # 计算次版本号
            
            # 增加构建号
            build_number += 1
            save_build_number(build_number)
            
            git_tag = f'v{major}.{minor}'
            
        return git_tag, git_hash
        
    except subprocess.CalledProcessError:
        # 不在git仓库中
        build_number = load_build_number()
        major = build_number // 10
        minor = build_number % 10
        build_number += 1
        save_build_number(build_number)
        return f'v{major}.{minor}', 'no-git'

def get_version():
    """生成完整的版本号"""
    from datetime import datetime
    
    git_tag, git_hash = get_git_revision()
    
    # 获取当前时间戳（格式：YYYYMMDD）
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # 版本号格式：主版本号.次版本号.时间戳.git简短hash
    # 例如：v1.0.20250208.43163bb
    version = f'{git_tag}.{timestamp}.{git_hash}'
    return version

# 当前版本号
VERSION = get_version()

if __name__ == '__main__':
    print(f'当前版本: {VERSION}')