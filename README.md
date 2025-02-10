# Chronos 

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6%2B-blue)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt-6.5.0%2B-green)](https://www.riverbankcomputing.com/software/pyqt/)

<div align="center">
  <img src="icon.svg" alt="Chronos Logo" width="128" height="128">
</div>

一个基于PyQt6开发的图形化定时任务管理工具，支持cron表达式，可以方便地管理和监控Linux/Unix系统的定时任务。

## ✨ 主要特性

- 📝 图形化界面管理crontab任务
- 🔄 支持完整的cron表达式和时间间隔设置
- 📊 实时显示任务状态和统计信息
- 📋 支持任务的增删改查操作
- 🔍 内置日志查看器,支持日志导出
- 🔔 系统托盘支持，最小化后继续运行
- 🎯 支持任务的启用/禁用功能
- 📌 支持窗口置顶功能
- 🔧 支持脚本测试功能，可在添加或编辑任务时验证脚本执行效果

## 🚀 快速开始
### 系统要求

- Python 3.6 或更高版本
- Linux/Unix 操作系统（支持crontab）

### 安装步骤

1. 克隆或下载本项目到本地
```bash
git clone https://github.com/konbluesky/chronos.git
cd chronos
```

2. 安装依赖包
```bash
pip install -r requirements.txt
```

### 启动程序

1. 在项目目录下运行以下命令：
```bash
python main.py
```

2. 程序启动后会在系统托盘显示图标，可以通过以下方式操作：
   - 左键单击托盘图标：显示主窗口
   - 右键单击托盘图标：显示快捷菜单

### 基本使用

1. 添加任务
   - 点击工具栏的"添加任务"按钮或使用快捷键 Ctrl+N
   - 填写任务名称、执行命令和执行计划
   - 点击确定保存任务

2. 管理任务
   - 编辑任务：选中任务后点击"编辑任务"或使用快捷键 Ctrl+E
   - 删除任务：选中任务后点击"删除任务"或使用 Delete 键
   - 启用/禁用任务：选中任务后点击"启用/禁用任务"或使用快捷键 Ctrl+T
   - 窗口置顶：点击窗口右上角的图钉图标或使用快捷键 Ctrl+P

3. 查看日志
   - 选中任务后点击"查看日志"或使用快捷键 Ctrl+L
   - 日志窗口会实时更新显示任务的执行记录

### 使用命令行查看任务

当程序未运行时，您仍然可以使用以下命令来管理定时任务：

1. 查看所有任务
```bash
crontab -l
```

2. 编辑任务
```bash
crontab -e
```

注意：使用命令行编辑任务时，请确保遵循正确的cron表达式格式，以免影响任务的正常执行。

### 常见问题

1. 权限问题
   - 如果遇到"Operation not permitted"错误，通常是由于以下原因：
     1. 用户没有足够的权限执行crontab命令
     2. 系统安全设置限制了crontab的使用

   解决方案：
   1. 确保您的用户账户在crontab组中：
   ```bash
   sudo usermod -a -G crontab $USER
   ```

   2. 使用sudo执行命令：
   ```bash
   sudo crontab -e
   ```

   3. 检查系统权限设置：
   ```bash
   ls -l /usr/bin/crontab
   ```

   注意：
   - 使用sudo时要格外小心，确保了解命令的影响
   - 某些系统可能需要重新登录后才能使组权限生效
   - 建议先测试任务权限再添加到定时任务中

## 💡 使用说明
### 添加任务

1. 点击工具栏的"添加任务"按钮或使用快捷键 `Ctrl+N`
2. 在弹出的对话框中填写：
   - 任务名称
   - 执行命令
   - 执行计划（支持cron表达式或时间间隔）
3. 点击确定保存

## 👥 作者

- konbluesky - [@konbluesky](https://github.com/konbluesky)

## 📸 界面展示

### 主界面
![主界面](screenshots/main.png)

### 托盘菜单
![托盘菜单](screenshots/tray_menu.png)

### 添加任务
![添加任务](screenshots/add_task.png)

### 添加任务(命令测试)
![命令测试](screenshots/add_task_test.png)

### 日志查看
![日志查看](screenshots/view_log.png)

## 🙏 致谢

- [python-crontab](https://pypi.org/project/python-crontab/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
