#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chronos - 图形化定时任务管理工具

这个程序提供了一个基于PyQt6的图形界面，用于管理和监控Linux/Unix系统的crontab任务。
主要功能包括：
- 可视化管理crontab任务
- 支持完整的cron表达式
- 实时任务状态监控
- 内置日志查看器
- 系统托盘支持

作者：konbluesky
许可证：MIT
"""

import sys
import re
import subprocess
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QSystemTrayIcon, QMenu, QToolBar, QStatusBar,
                             QHeaderView, QCheckBox, QDialog, QPlainTextEdit, QTextEdit, QComboBox,
                             QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QAction, QCursor, QBrush, QColor
import os
import datetime
from crontab import CronTab
from version import VERSION

class CronEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def create_combo_box(self, label, options):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签
        label_widget = QLabel(label)
        label_widget.setStyleSheet('font-size: 13px; color: #333; font-weight: 500;')
        layout.addWidget(label_widget)
        
        # 创建下拉框
        combo = QComboBox()
        if label == '分钟':
            combo.addItem('*', '*')
            combo.addItem('每分钟', '*')
            for i in [1,2,3,5,10,15,20,30]:
                combo.addItem(f'每{i}分钟', f'*/{i}')
            for i in range(60):
                combo.addItem(f'{i:02d} 分', str(i))
        elif label == '小时':
            combo.addItem('*', '*')
            combo.addItem('每小时', '*')
            for i in [1,2,3,4,6,8,12]:
                combo.addItem(f'每{i}小时', f'*/{i}')
            for i in range(24):
                combo.addItem(f'{i:02d} 时', str(i))
        elif label == '日期':
            combo.addItem('*', '*')
            combo.addItem('每天', '*')
            for i in [2,3,5,7,10,15]:
                combo.addItem(f'每{i}天', f'*/{i}')
            for i in range(1, 32):
                combo.addItem(f'{i:02d} 日', str(i))
        elif label == '月份':
            combo.addItem('*', '*')
            for i in range(1, 13):
                combo.addItem(f'{i:02d} 月', str(i))
        elif label == '星期':
            combo.addItem('*', '*')
            weekdays = ['日', '一', '二', '三', '四', '五', '六']
            for i, day in enumerate(weekdays):
                combo.addItem(f'星期{day}', str(i))

        combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                min-width: 90px;
                color: #333;
            }
            QComboBox:hover {
                border-color: #007bff;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 5px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ddd;
                background-color: white;
                color: #333;
                selection-background-color: #007bff;
                selection-color: white;
            }
        """)
        layout.addWidget(combo)
        
        return container

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # 增加垂直间距
        layout.setContentsMargins(10, 10, 10, 10)  # 添加边距

        # 创建水平布局来组织时间选择器
        time_layout = QHBoxLayout()
        time_layout.setSpacing(20)  # 设置水平间距

        # 创建各个时间单位的选择器
        self.minute_combo = self.create_combo_box('分钟', [])
        self.hour_combo = self.create_combo_box('小时', [])
        self.day_combo = self.create_combo_box('日期', [])
        self.month_combo = self.create_combo_box('月份', [])
        self.weekday_combo = self.create_combo_box('星期', [])

        # 添加到水平布局
        time_layout.addWidget(self.minute_combo)
        time_layout.addWidget(self.hour_combo)
        time_layout.addWidget(self.day_combo)
        time_layout.addWidget(self.month_combo)
        time_layout.addWidget(self.weekday_combo)

        # 将水平布局添加到主布局
        layout.addLayout(time_layout)

        # 添加表达式编辑框
        self.expression_edit = QLineEdit()
        self.expression_edit.setStyleSheet('padding: 8px; font-size: 12px; color: #666; background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px;')
        self.expression_edit.textChanged.connect(self.on_expression_changed)
        layout.addWidget(self.expression_edit)

        self.translation_label = QLabel()
        self.translation_label.setWordWrap(True)
        self.translation_label.setStyleSheet('padding: 8px; font-size: 13px; background-color: #e3f2fd; border: 1px solid #90caf9; border-radius: 4px; margin-top: 5px;')
        layout.addWidget(self.translation_label)
        layout.addStretch()  # 添加弹性空间

        # 连接信号
        self.minute_combo.findChild(QComboBox).currentIndexChanged.connect(self.update_cron_expression)
        self.hour_combo.findChild(QComboBox).currentIndexChanged.connect(self.update_cron_expression)
        self.day_combo.findChild(QComboBox).currentIndexChanged.connect(self.update_cron_expression)
        self.month_combo.findChild(QComboBox).currentIndexChanged.connect(self.update_cron_expression)
        self.weekday_combo.findChild(QComboBox).currentIndexChanged.connect(self.update_cron_expression)

        self.cron_expression = '* * * * *'
        self.expression_edit.setText(self.cron_expression)
        self.update_translation()

    def on_expression_changed(self):
        self.cron_expression = self.expression_edit.text()
        self.update_translation()

    def update_cron_expression(self):
        # 获取各个下拉框的值
        minute = self.minute_combo.findChild(QComboBox).currentData()
        hour = self.hour_combo.findChild(QComboBox).currentData()
        day = self.day_combo.findChild(QComboBox).currentData()
        month = self.month_combo.findChild(QComboBox).currentData()
        weekday = self.weekday_combo.findChild(QComboBox).currentData()
        
        # 更新cron表达式
        self.cron_expression = f'{minute} {hour} {day} {month} {weekday}'
        self.expression_edit.setText(self.cron_expression)  # 更新编辑框的内容
        
        # 更新翻译
        self.update_translation()

    def update_translation(self):
        # 更新翻译后的内容
        translation = '执行规则：'
        try:
            parts = self.cron_expression.strip().split()
            if len(parts) != 5:
                self.translation_label.setText('无效的cron表达式')
                return
            minute, hour, day, month, weekday = parts
        except:
            self.translation_label.setText('无效的cron表达式')
            return

        # 翻译分钟
        if minute == '*':
            translation += '每分钟'
        elif '/' in minute:
            interval = minute.split('/')[1]
            translation += f'每{interval}分钟'
        else:
            translation += f'在第{minute}分钟'

        # 翻译小时
        if hour == '*':
            translation += '的每小时'
        elif '/' in hour:
            interval = hour.split('/')[1]
            translation += f'的每{interval}小时'
        else:
            translation += f'的{hour}点'

        # 翻译日期
        if day == '*':
            if weekday == '*':
                translation += '的每一天'
            else:
                translation += ''
        elif '/' in day:
            interval = day.split('/')[1]
            translation += f'的每{interval}天'
        else:
            translation += f'的{day}日'

        # 翻译月份
        if month == '*':
            translation += ''
        elif '/' in month:
            interval = month.split('/')[1]
            translation += f'的每{interval}个月'
        else:
            translation += f'的{month}月'

        # 翻译星期
        if weekday != '*':
            if '/' in weekday:
                interval = weekday.split('/')[1]
                translation += f'的每{interval}天'
            else:
                try:
                    weekday_num = int(weekday)
                    if 0 <= weekday_num <= 6:
                        weekday_names = ['日', '一', '二', '三', '四', '五', '六']
                        translation += f'的星期{weekday_names[weekday_num]}'
                    else:
                        translation += f'(无效的星期值: {weekday})'
                except ValueError:
                    translation += f'(无效的星期值: {weekday})'

        translation += '执行'
        self.translation_label.setText(translation)

    def get_cron_expression(self):
        return self.cron_expression

    def set_cron_expression(self, expression):
        try:
            parts = expression.strip().split()
            if len(parts) == 5:
                # 使用setCurrentData而不是setCurrentText来设置值
                def set_combo_value(combo, value):
                    combo_box = combo.findChild(QComboBox)
                    # 查找匹配的数据值
                    index = combo_box.findData(value)
                    if index >= 0:
                        combo_box.setCurrentIndex(index)
                    else:
                        # 如果找不到匹配的数据值，尝试直接设置文本
                        combo_box.setCurrentText(value)

                set_combo_value(self.minute_combo, parts[0])
                set_combo_value(self.hour_combo, parts[1])
                set_combo_value(self.day_combo, parts[2])
                set_combo_value(self.month_combo, parts[3])
                set_combo_value(self.weekday_combo, parts[4])
        except Exception as e:
            print(f"设置cron表达式时出错: {str(e)}")
            pass

class JobDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加/编辑任务')
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)  # 增加表单项之间的间距
        layout.setContentsMargins(20, 20, 20, 20)  # 设置边距
        self.setMinimumWidth(800)  # 增加窗口宽度

        # 设置标签样式
        label_style = 'font-size: 13px; color: #333; font-weight: 500;'
        name_label = QLabel('任务名称')
        name_label.setStyleSheet('font-size: 14px; color: #2c3e50; font-weight: 500; margin-bottom: 5px;')
        command_label = QLabel('执行命令')
        command_label.setStyleSheet('font-size: 14px; color: #2c3e50; font-weight: 500; margin-bottom: 5px;')
        schedule_label = QLabel('执行计划')
        schedule_label.setStyleSheet('font-size: 14px; color: #2c3e50; font-weight: 500; margin-bottom: 5px;')

        # 创建并设置输入框
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumWidth(700)
        self.name_edit.setMaximumWidth(700)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        self.command_edit = QPlainTextEdit()
        self.command_edit.setMinimumWidth(700)
        self.command_edit.setMaximumWidth(700)
        self.command_edit.setMinimumHeight(80)
        self.command_edit.setPlaceholderText('请输入要执行的命令')
        self.command_edit.setStyleSheet("""
            QPlainTextEdit {
                padding: 8px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPlainTextEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
        self.cron_editor = CronEditor()

        # 设置标签的对齐方式
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 添加表单项
        layout.addRow(name_label, self.name_edit)
        layout.addRow(command_label, self.command_edit)
        layout.addRow(schedule_label, self.cron_editor)

        # 创建按钮布局
        buttons = QHBoxLayout()
        buttons.setSpacing(10)  # 设置按钮之间的间距
        self.test_button = QPushButton('测试命令')
        self.ok_button = QPushButton('确定')
        self.cancel_button = QPushButton('取消')
        self.test_button.setFixedWidth(100)  # 统一按钮宽度
        self.ok_button.setFixedWidth(100)
        self.cancel_button.setFixedWidth(100)
        buttons.addWidget(self.test_button)
        buttons.addStretch()
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        self.test_button.clicked.connect(self.test_command)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        layout.addRow('', buttons)

    def test_command(self):
        """测试命令功能"""
        command = self.command_edit.toPlainText().strip()
        if not command:
            QMessageBox.warning(self, '警告', '请输入要测试的命令')
            return
            
        try:
            # 创建一个临时的日志文件来捕获命令输出
            import tempfile
            import subprocess
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(timeout=10)
                
                if process.returncode == 0:
                    temp_file.write(f"命令执行成功！\n\n输出：\n{stdout}")
                    title = '测试成功'
                else:
                    temp_file.write(f"命令执行失败！\n\n错误输出：\n{stderr}\n\n标准输出：\n{stdout}")
                    title = '测试失败'
                    
            # 显示结果对话框
            with open(temp_file.name, 'r') as f:
                content = f.read()
                
            msg = QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(content)
            msg.setDetailedText(content)
            msg.setIcon(QMessageBox.Icon.Information if process.returncode == 0 else QMessageBox.Icon.Warning)
            
            # 添加打开日志目录和脚本目录的按钮
            open_logs_button = msg.addButton('打开日志目录', QMessageBox.ButtonRole.ActionRole)
            open_scripts_button = msg.addButton('打开脚本目录', QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            
            # 设置弹窗样式和布局
            msg.setStyleSheet("""
                QMessageBox {
                    min-width: 600px;
                }
                QLabel {
                    min-width: 500px;
                    font-size: 13px;
                    padding: 10px;
                }
                QMessageBox QLabel#qt_msgbox_label {
                    min-height: 40px;
                }
                QMessageBox QLabel#qt_msgboxex_icon_label {
                    min-width: 100px;
                    padding-right: 20px;
                }
                QPushButton {
                    min-width: 100px;
                    padding: 6px;
                }
            """)
            
            result = msg.exec()
            
            # 处理按钮点击事件
            clicked_button = msg.clickedButton()
            if clicked_button == open_logs_button:
                self.parent().open_logs_directory()
            elif clicked_button == open_scripts_button:
                self.parent().open_scripts_directory()
            
            # 清理临时文件
            os.unlink(temp_file.name)
            
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, '错误', '命令执行超时')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'执行命令时发生错误：{str(e)}')

class LogViewerDialog(QDialog):
    def __init__(self, log_file, parent=None):
        super().__init__(parent)
        self.log_file = log_file
        self.setWindowTitle('日志查看器')
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_log)
        self.timer.start(1000)  # 每秒更新一次

    def setup_ui(self):
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        
        # 添加工具栏
        toolbar = QHBoxLayout()
        self.auto_scroll_checkbox = QCheckBox('自动滚动')
        self.auto_scroll_checkbox.setChecked(True)
        toolbar.addWidget(self.auto_scroll_checkbox)
        
        self.clear_button = QPushButton('清除日志')
        self.clear_button.clicked.connect(self.clear_log)
        toolbar.addWidget(self.clear_button)
        
        self.export_button = QPushButton('导出日志')
        self.export_button.clicked.connect(self.export_log)
        toolbar.addWidget(self.export_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('font-family: monospace; background-color: #f8f9fa; padding: 10px;')
        layout.addWidget(self.log_text)
        
        self.update_log()

    def update_log(self):
        try:
            if not os.path.exists(self.log_file):
                self.log_text.setText('日志文件不存在')
                return
                
            with open(self.log_file, 'r') as f:
                content = f.read()
                if content != self.log_text.toPlainText():
                    self.log_text.setText(content)
                    if self.auto_scroll_checkbox.isChecked():
                        self.log_text.verticalScrollBar().setValue(
                            self.log_text.verticalScrollBar().maximum()
                        )
        except PermissionError:
            self.log_text.setText('无法读取日志文件：权限不足')
        except Exception as e:
            self.log_text.setText(f'读取日志文件时发生错误：{str(e)}')

    def clear_log(self):
        reply = QMessageBox.question(self, '确认', '确定要清除日志吗？',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.log_file, 'w') as f:
                    f.write(f"=== 日志清除于 {datetime.datetime.now()} ===\n")
                self.update_log()
                QMessageBox.information(self, '成功', '日志已清除')
            except PermissionError:
                QMessageBox.critical(self, '错误', '无法清除日志：权限不足')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'清除日志失败：{str(e)}')

    def export_log(self):
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f'log_export_{timestamp}.txt'
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                '导出日志',
                os.path.join(os.path.expanduser('~/Desktop'), default_name),
                '文本文件 (*.txt);;所有文件 (*)'
            )
            
            if file_path:
                with open(self.log_file, 'r') as src, open(file_path, 'w') as dst:
                    dst.write(src.read())
                QMessageBox.information(self, '成功', f'日志已导出到：{file_path}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出日志失败：{str(e)}')

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()

class JobManager(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置应用程序名称和组织信息
        QApplication.setApplicationName('Chronos')
        QApplication.setApplicationDisplayName('Chronos')
        QApplication.setOrganizationName('konbluesky')
        QApplication.setOrganizationDomain('github.com/konbluesky')
        
        self.setWindowTitle(f'Chronos {VERSION}')
        
        # 设置目录路径
        self.base_dir = os.path.expanduser('~/.chronos')
        self.log_dir = os.path.join(self.base_dir, 'logs')
        self.scripts_dir = os.path.join(self.base_dir, 'scripts')
        
        # 创建必要的目录
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            os.makedirs(self.scripts_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法创建必要的目录：{str(e)}\n请确保当前用户有权限创建目录。')
            sys.exit(1)
            
        self.setup_ui()
        try:
            self.cron = CronTab(user=True)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法初始化crontab：{str(e)}\n请确保系统支持crontab且当前用户有权限访问。')
            sys.exit(1)

        # 初始化日志和脚本目录
        self.base_dir = os.path.expanduser('~/.chronos')
        self.log_dir = os.path.join(self.base_dir, 'logs')
        self.scripts_dir = os.path.join(self.base_dir, 'scripts')
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            os.makedirs(self.scripts_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法创建必要的目录：{str(e)}\n请确保当前用户有权限创建目录。')
            sys.exit(1)

        self.setup_tray()
        self.refresh_jobs()

        # 设置自动刷新定时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_jobs)
        self.refresh_timer.start(60000)  # 每分钟刷新一次

    def closeEvent(self, event):
        if not self.tray_icon.isVisible():
            # 如果托盘图标不可见，则正常退出
            self.cleanup_resources()
            event.accept()
        else:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage('Chronos', '程序已最小化到系统托盘', QSystemTrayIcon.MessageIcon.Information)

    def cleanup_resources(self):
        """清理程序资源"""
        try:
            if hasattr(self, 'refresh_timer') and self.refresh_timer is not None:
                self.refresh_timer.stop()
                self.refresh_timer.deleteLater()
                self.refresh_timer = None
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
                self.tray_icon = None
        except Exception as e:
            print(f"清理资源时发生错误: {str(e)}")
            pass

    def __del__(self):
        self.cleanup_resources()

    def setup_tray(self):
        # 检查系统是否支持系统托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.warning(self, '警告', '系统不支持托盘图标功能，程序将以普通窗口模式运行。')
            return

        self.tray_icon = QSystemTrayIcon(self)
        
        # 检查图标文件是否存在
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.svg')
        if not os.path.exists(icon_path):
            QMessageBox.warning(self, '警告', '找不到图标文件，将使用默认图标。')
        else:
            self.tray_icon.setIcon(QIcon(icon_path))
            
        self.tray_icon.setToolTip('任务管理器')

        # 创建托盘菜单
        self.tray_menu = QMenu()
        self.show_action = QAction('显示主窗口', self)
        self.show_action.triggered.connect(lambda: (self.show(), self.activateWindow()))
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addSeparator()

        # 添加状态子菜单
        self.status_menu = QMenu('任务状态', self)
        self.tray_menu.addMenu(self.status_menu)
        
        # 添加任务管理子菜单
        self.job_menu = QMenu('任务管理', self)
        self.tray_menu.addMenu(self.job_menu)
        
        # 添加目录访问子菜单
        self.directory_menu = QMenu('打开目录', self)
        self.open_logs_action = QAction('日志目录', self)
        self.open_logs_action.triggered.connect(self.open_logs_directory)
        self.directory_menu.addAction(self.open_logs_action)
        
        self.open_scripts_action = QAction('脚本目录', self)
        self.open_scripts_action.triggered.connect(self.open_scripts_directory)
        self.directory_menu.addAction(self.open_scripts_action)
        self.tray_menu.addMenu(self.directory_menu)
        
        self.tray_menu.addSeparator()

        self.quit_action = QAction('退出', self)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # 连接托盘图标的点击信号
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def update_status_menu(self):
        self.status_menu.clear()
        self.job_menu.clear()
        for job in self.cron:
            # 更新状态菜单
            status = '启用' if job.is_enabled() else '禁用'
            status_action = QAction(f'{job.comment}: {status}', self)
            status_action.setEnabled(False)
            self.status_menu.addAction(status_action)
            
            # 更新任务管理菜单
            job_submenu = QMenu(job.comment, self)
            
            enable_action = QAction('启用', self)
            enable_action.triggered.connect(lambda checked, j=job: self.enable_job_from_tray(j))
            enable_action.setEnabled(not job.is_enabled())
            job_submenu.addAction(enable_action)
            
            disable_action = QAction('禁用', self)
            disable_action.triggered.connect(lambda checked, j=job: self.disable_job_from_tray(j))
            disable_action.setEnabled(job.is_enabled())
            job_submenu.addAction(disable_action)
            
            self.job_menu.addMenu(job_submenu)
            
        if self.status_menu.isEmpty():
            status_action = QAction('暂无任务', self)
            status_action.setEnabled(False)
            self.status_menu.addAction(status_action)
            
            job_action = QAction('暂无任务', self)
            job_action.setEnabled(False)
            self.job_menu.addAction(job_action)
            
    def enable_job_from_tray(self, job):
        job.enable()
        self.cron.write()
        self.refresh_jobs()
        
    def disable_job_from_tray(self, job):
        job.enable(False)
        self.cron.write()
        self.refresh_jobs()

    def refresh_jobs(self):
        self.table.setRowCount(0)
        enabled_count = 0
        disabled_count = 0
        
        for job in self.cron:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name = job.comment
            
            # 从脚本文件中读取原始命令
            script_path = self.get_script_path(name)
            original_command = ""
            if os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    lines = f.readlines()
                    # 查找以 ## 开头的行来获取原始命令
                    for line in lines:
                        line = line.strip()
                        if line.startswith('## '):
                            original_command = line[3:].strip()  # 去掉 '## ' 前缀
                            break
            
            if not original_command:
                original_command = job.command
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(original_command))
            self.table.setItem(row, 2, QTableWidgetItem(str(job.slices)))
            
            # 添加启用/禁用状态
            status_item = QTableWidgetItem('⬤')
            if job.is_enabled():
                status_item.setForeground(QBrush(QColor('#2e7d32')))  # 绿色圆点
                enabled_count += 1
            else:
                status_item.setForeground(QBrush(QColor('#d32f2f')))  # 红色圆点
                disabled_count += 1
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, status_item)
        
        total_count = enabled_count + disabled_count
        self.status_bar.showMessage(f'总任务数: {total_count} | 已启用: {enabled_count} | 已禁用: {disabled_count} | 版本: {VERSION}')
        self.update_status_menu()

    def setup_ui(self):
        self.setMinimumSize(1000, 500)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #eee;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #f5f5f5;
                color: #333;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #ddd;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QStatusBar {
                background-color: #f8f9fa;
                color: #666;
            }
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 0;
                margin: 2px;
            }
            QMenu::item {
                padding: 8px 24px;
                font-size: 13px;
                color: #333;
            }
            QMenu::item:selected {
                background-color: #f0f7ff;
                color: #007bff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #eee;
                margin: 4px 12px;
            }
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #ddd;
            }
            QMenuBar::item {
                padding: 8px 12px;
                font-size: 13px;
                color: #333;
            }
            QMenuBar::item:selected {
                background-color: #f0f7ff;
                color: #007bff;
            }
            QMenuBar::item:pressed {
                background-color: #f0f7ff;
                color: #007bff;
            }
        """)

        # 创建菜单栏
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')
        self.add_action = QAction('添加任务', self)
        self.add_action.setShortcut('Ctrl+N')

        # 添加置顶动作
        self.stay_on_top_action = QAction('窗口置顶', self)
        self.stay_on_top_action.setCheckable(True)
        self.stay_on_top_action.setShortcut('Ctrl+T')
        self.stay_on_top_action.triggered.connect(self.toggle_stay_on_top)
        file_menu.addAction(self.stay_on_top_action)
        file_menu.addSeparator()
        self.add_action.setToolTip('添加新任务')
        file_menu.addAction(self.add_action)

        file_menu.addSeparator()
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        self.edit_action = QAction('编辑任务', self)
        self.edit_action.setShortcut('Ctrl+E')
        self.edit_action.setToolTip('编辑选中的任务')
        edit_menu.addAction(self.edit_action)

        self.delete_action = QAction('删除任务', self)
        self.delete_action.setShortcut('Delete')
        self.delete_action.setToolTip('删除选中的任务')
        edit_menu.addAction(self.delete_action)

        self.enable_action = QAction('启用任务', self)
        self.enable_action.setShortcut('Ctrl+T')
        self.enable_action.setToolTip('启用选中的任务')
        edit_menu.addAction(self.enable_action)

        self.disable_action = QAction('禁用任务', self)
        self.disable_action.setShortcut('Ctrl+D')
        self.disable_action.setToolTip('禁用选中的任务')
        edit_menu.addAction(self.disable_action)

        # 视图菜单
        view_menu = menubar.addMenu('视图')
        self.view_log_action = QAction('查看日志', self)
        self.view_log_action.setShortcut('Ctrl+L')
        self.view_log_action.setToolTip('查看选中任务的日志')
        view_menu.addAction(self.view_log_action)

        self.refresh_action = QAction('刷新', self)
        self.refresh_action.setShortcut('F5')
        self.refresh_action.setToolTip('刷新任务列表')
        view_menu.addAction(self.refresh_action)

        # 添加打开目录的菜单项
        view_menu.addSeparator()
        self.open_logs_action = QAction('打开日志目录', self)
        self.open_logs_action.setToolTip('打开存放日志文件的目录')
        self.open_logs_action.triggered.connect(self.open_logs_directory)
        view_menu.addAction(self.open_logs_action)

        self.open_scripts_action = QAction('打开脚本目录', self)
        self.open_scripts_action.setToolTip('打开存放脚本文件的目录')
        self.open_scripts_action.triggered.connect(self.open_scripts_directory)
        view_menu.addAction(self.open_scripts_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        help_menu = menubar.addMenu('帮助')

        # 添加导入/导出菜单
        import_export_menu = menubar.addMenu('导入/导出')
        self.export_action = QAction('导出任务', self)
        self.export_action.setShortcut('Ctrl+Shift+E')
        self.export_action.setToolTip('将当前任务配置导出到文件')
        self.export_action.triggered.connect(self.export_tasks)
        import_export_menu.addAction(self.export_action)

        self.import_action = QAction('导入任务', self)
        self.import_action.setShortcut('Ctrl+Shift+I')
        self.import_action.setToolTip('从文件导入任务配置')
        self.import_action.triggered.connect(self.import_tasks)
        import_export_menu.addAction(self.import_action)

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # 创建工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)  # 禁用工具栏右键菜单
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                border: solid 1px #007bff;
                font-size: 14px;
                padding: 8px;
                margin: 2px;
                min-width: 40px;
                border-radius: 4px;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: rgba(0, 123, 255, 0.1);
            }
            QToolButton:pressed {
                background-color: rgba(0, 123, 255, 0.2);
            }
        """)

        # 添加动作到工具栏
        toolbar.addAction(self.add_action)
        toolbar.addAction(self.edit_action)
        toolbar.addAction(self.delete_action)
        toolbar.addAction(self.enable_action)
        toolbar.addAction(self.disable_action)
        toolbar.addAction(self.view_log_action)
        toolbar.addAction(self.refresh_action)


        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['任务名称', '执行命令', '执行计划', '状态'])
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)  # 禁用最后一列自动拉伸
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # 将状态列设置为固定宽度
        self.table.setColumnWidth(0, 150)  # 调整任务名称列宽度
        self.table.setColumnWidth(3, 50)  # 设置状态列固定宽度为50px
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁用编辑
        
        # 设置表格选择模式为整行选择，支持多选
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # 添加右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 添加双击事件处理
        self.table.cellDoubleClicked.connect(self.edit_job)

        layout.addWidget(self.table)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')

        # 连接信号
        self.add_action.triggered.connect(self.add_job)
        self.edit_action.triggered.connect(self.edit_job)
        self.delete_action.triggered.connect(self.delete_job)
        self.enable_action.triggered.connect(self.enable_jobs)
        self.disable_action.triggered.connect(self.disable_jobs)
        self.refresh_action.triggered.connect(self.refresh_jobs)
        self.view_log_action.triggered.connect(self.view_log)

    

    def add_job(self):
        dialog = JobDialog(self)
        if dialog.exec():
            name = dialog.name_edit.text().strip()
            command = dialog.command_edit.toPlainText().strip()
            schedule = dialog.cron_editor.get_cron_expression()

            # 验证输入
            if not name:
                QMessageBox.warning(self, '输入错误', '任务名称不能为空')
                return
            if not command:
                QMessageBox.warning(self, '输入错误', '执行命令不能为空')
                return

            try:
                # 检查任务名是否重复
                for job in self.cron:
                    if job.comment == name:
                        QMessageBox.warning(self, '输入错误', '任务名称已存在，请使用其他名称')
                        return

                # 创建执行脚本
                script_path = self.create_script_file(name, command)
                # 添加到crontab
                job = self.cron.new(command=script_path, comment=name)
                job.setall(schedule)

                try:
                    self.cron.write()
                    # 创建日志文件并添加初始记录
                    log_file = self.get_log_path(name)
                    with open(log_file, 'a') as f:
                        f.write(f"=== 任务创建于 {datetime.datetime.now()} ===\n")
                        f.write(f"任务名称: {name}\n")
                        f.write(f"执行命令: {command}\n")
                        f.write(f"执行计划: {schedule}\n\n")
                    self.refresh_jobs()
                    self.status_bar.showMessage(f'任务 "{name}" 创建成功', 3000)
                except IOError as e:
                    if 'Operation not permitted' in str(e):
                        QMessageBox.critical(self, '权限错误',
                            '无法修改定时任务，因为当前用户没有足够的权限。\n\n'
                            '请尝试以下解决方案：\n'
                            '1. 使用管理员权限运行此程序\n'
                            '2. 确保当前用户有权限修改crontab文件')
                    else:
                        QMessageBox.critical(self, '错误', f'写入定时任务失败：{str(e)}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'创建任务失败：{str(e)}')

    def edit_job(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '警告', '请选择要编辑的任务')
            return

        try:
            cron_jobs = list(self.cron)
            if current_row >= len(cron_jobs):
                QMessageBox.warning(self, '错误', '无法找到选中的任务，请刷新任务列表后重试')
                return
            job = cron_jobs[current_row]
            name = job.comment
        
            # 从脚本文件中读取原始命令
            script_path = self.get_script_path(name)
            original_command = job.command
            if os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    lines = f.readlines()
                    # 查找以 ## 开头的行来获取原始命令
                    for line in lines:
                        line = line.strip()
                        if line.startswith('## '):
                            original_command = line[3:].strip()  # 去掉 '## ' 前缀
                            break
            
            dialog = JobDialog(self)
            dialog.name_edit.setText(name)
            dialog.command_edit.setPlainText(original_command)
            dialog.cron_editor.set_cron_expression(str(job.slices))

            if dialog.exec() == QDialog.DialogCode.Accepted:
                try:
                    new_name = dialog.name_edit.text().strip()
                    new_command = dialog.command_edit.toPlainText().strip()
                    
                    # 如果任务名称改变，需要删除旧的脚本文件
                    if new_name != name:
                        old_script_path = self.get_script_path(name)
                        if os.path.exists(old_script_path):
                            os.remove(old_script_path)
                    
                    # 创建新的脚本文件
                    script_path = self.create_script_file(new_name, new_command)
                    
                    # 更新crontab任务
                    job.set_command(script_path)
                    job.set_comment(new_name)
                    job.setall(dialog.cron_editor.get_cron_expression())
                    self.cron.write()
                    self.refresh_jobs()
                    self.status_bar.showMessage(f'任务 "{new_name}" 更新成功', 3000)
                except IOError as e:
                    if 'Operation not permitted' in str(e):
                        QMessageBox.critical(self, '权限错误',
                            '无法修改定时任务，因为当前用户没有足够的权限。\n\n'
                            '请尝试以下解决方案：\n'
                            '1. 使用管理员权限运行此程序\n'
                            '2. 确保当前用户有权限修改crontab文件')
                    else:
                        QMessageBox.critical(self, '错误', f'写入定时任务失败：{str(e)}')
                except Exception as e:
                    QMessageBox.critical(self, '错误', f'更新任务失败：{str(e)}')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'编辑任务失败：{str(e)}')

    def normalize_task_name(self, name):
        """将任务名称转换为有效的文件名"""
        # 替换所有非字母数字字符为下划线
        return re.sub(r'[^\w]', '_', name)

    def get_script_path(self, name):
        """获取任务对应的脚本文件路径"""
        normalized_name = self.normalize_task_name(name)
        return os.path.join(self.scripts_dir, f"{normalized_name}.sh")

    def get_log_path(self, name):
        """获取任务对应的日志文件路径"""
        normalized_name = self.normalize_task_name(name)
        return os.path.join(self.log_dir, f"{normalized_name}.log")

    def create_script_file(self, name, command):
        """创建任务的执行脚本"""
        script_path = self.get_script_path(name)
        log_path = self.get_log_path(name)
        
        script_content = f"#!/bin/bash\n\n# Task: {name}\n# Created: {datetime.datetime.now()}\n\n## {command}\n\n# 设置错误处理\nset -e\n\n# 设置工作目录\ncd $(dirname \"$0\")\n\n# 添加分隔符\necho \"\n----------------------------------------\n执行时间: $(date '+%Y-%m-%d %H:%M:%S')\n----------------------------------------\n\" | tee -a \"{log_path}\"\n\n# 执行命令并记录日志\n{{ {command}; }} 2>&1 | tee -a \"{log_path}\" || {{\n    echo \"[$(date '+%Y-%m-%d %H:%M:%S')] 执行失败\" | tee -a \"{log_path}\"\n    exit 1\n}}\n\necho \"[$(date '+%Y-%m-%d %H:%M:%S')] 执行成功\" | tee -a \"{log_path}\"\n"
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)  # 设置可执行权限
            return script_path
        except Exception as e:
            raise Exception(f'创建脚本文件失败：{str(e)}')

    def delete_job(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '请先选择要删除的任务')
            return

        # 获取选中的行
        rows = list(set(item.row() for item in selected_items))
        names = [self.table.item(row, 0).text() for row in rows]
        
        # 构建确认消息
        message = '确定要删除以下任务吗？\n\n' + '\n'.join(f'- {name}' for name in names)
        reply = QMessageBox.question(self, '确认删除', message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                for name in names:
                    # 删除crontab中的任务
                    for job in self.cron:
                        if job.comment == name:
                            self.cron.remove(job)
                            break
                    
                    # 清理相关文件
                    script_path = self.get_script_path(name)
                    log_path = self.get_log_path(name)
                    
                    if os.path.exists(script_path):
                        os.remove(script_path)
                    if os.path.exists(log_path):
                        os.remove(log_path)
                
                # 写入crontab文件
                self.cron.write()
                self.refresh_jobs()
                self.status_bar.showMessage(f'已删除 {len(names)} 个任务', 3000)
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除任务失败：{str(e)}')

    def refresh_jobs(self):
        self.table.setRowCount(0)
        enabled_count = 0
        disabled_count = 0
        
        for job in self.cron:
            row = self.table.rowCount()
            self.table.insertRow(row)
            name = job.comment
            
            # 从脚本文件中读取原始命令
            script_path = self.get_script_path(name)
            original_command = ""
            if os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    lines = f.readlines()
                    # 查找以 ## 开头的行来获取原始命令
                    for line in lines:
                        line = line.strip()
                        if line.startswith('## '):
                            original_command = line[3:].strip()  # 去掉 '## ' 前缀
                            break
            
            if not original_command:
                original_command = job.command
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(original_command))
            self.table.setItem(row, 2, QTableWidgetItem(str(job.slices)))
            
            # 添加启用/禁用状态
            status_item = QTableWidgetItem('⬤')
            if job.is_enabled():
                status_item.setForeground(QBrush(QColor('#2e7d32')))  # 绿色圆点
                enabled_count += 1
            else:
                status_item.setForeground(QBrush(QColor('#d32f2f')))  # 红色圆点
                disabled_count += 1
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, status_item)
        
        total_count = enabled_count + disabled_count
        self.status_bar.showMessage(f'总任务数: {total_count} | 已启用: {enabled_count} | 已禁用: {disabled_count} | 版本: {VERSION}')
        self.update_status_menu()

    def view_log(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '警告', '请先选择一个任务')
            return

        name = self.table.item(current_row, 0).text()
        log_file = self.get_log_path(name)
        
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write(f"=== Log file created at {datetime.datetime.now()} ===\n")
        
        dialog = LogViewerDialog(log_file, self)
        dialog.exec()

    def toggle_job(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '警告', '请先选择一个任务')
            return

        name = self.table.item(current_row, 0).text()
        for job in self.cron:
            if job.comment == name:
                if job.is_enabled():
                    job.enable(False)
                else:
                    job.enable(True)
                self.cron.write()
                self.refresh_jobs()
                break

    def enable_jobs(self):
        """启用选中的任务"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '请先选择要启用的任务')
            return

        # 获取选中的行
        rows = list(set(item.row() for item in selected_items))
        for row in rows:
            job_name = self.table.item(row, 0).text()
            try:
                for job in self.cron.find_comment(job_name):
                    job.enable()
                self.cron.write()
            except IOError as e:
                if 'Operation not permitted' in str(e):
                    QMessageBox.critical(self, '权限错误',
                        f'无法启用任务 {job_name}，因为当前用户没有足够的权限。\n\n'
                        '请尝试以下解决方案：\n'
                        '1. 使用管理员权限运行此程序\n'
                        '2. 确保当前用户有权限修改crontab文件')
                else:
                    QMessageBox.critical(self, '错误', f'启用任务 {job_name} 失败：{str(e)}')
                return
            except Exception as e:
                QMessageBox.critical(self, '错误', f'启用任务 {job_name} 失败：{str(e)}')
                return

        self.refresh_jobs()
        QMessageBox.information(self, '成功', '任务已启用')

    def disable_jobs(self):
        """禁用选中的任务"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '警告', '请先选择要禁用的任务')
            return

        # 获取选中的行
        rows = list(set(item.row() for item in selected_items))
        for row in rows:
            job_name = self.table.item(row, 0).text()
            try:
                for job in self.cron.find_comment(job_name):
                    job.enable(False)
                self.cron.write()
            except IOError as e:
                if 'Operation not permitted' in str(e):
                    QMessageBox.critical(self, '权限错误',
                        f'无法禁用任务 {job_name}，因为当前用户没有足够的权限。\n\n'
                        '请尝试以下解决方案：\n'
                        '1. 使用管理员权限运行此程序\n'
                        '2. 确保当前用户有权限修改crontab文件')
                else:
                    QMessageBox.critical(self, '错误', f'禁用任务 {job_name} 失败：{str(e)}')
                return
            except Exception as e:
                QMessageBox.critical(self, '错误', f'禁用任务 {job_name} 失败：{str(e)}')
                return

        self.refresh_jobs()
        QMessageBox.information(self, '成功', '任务已禁用')

    def show_context_menu(self, position):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 0;
                margin: 2px;
            }
            QMenu::item {
                padding: 8px 24px;
                font-size: 13px;
                color: #333;
            }
            QMenu::item:selected {
                background-color: #f0f7ff;
                color: #007bff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #eee;
                margin: 4px 12px;
            }
        """)
        edit_action = menu.addAction('编辑任务')
        delete_action = menu.addAction('删除任务')
        toggle_action = menu.addAction('启用/禁用')
        view_log_action = menu.addAction('查看日志')

        # 获取当前选中的行
        current_row = self.table.currentRow()
        actions_enabled = current_row >= 0

        # 根据是否选中行来启用/禁用菜单项
        edit_action.setEnabled(actions_enabled)
        delete_action.setEnabled(actions_enabled)
        toggle_action.setEnabled(actions_enabled)
        view_log_action.setEnabled(actions_enabled)

        # 显示菜单并获取用户选择的操作
        action = menu.exec(self.table.viewport().mapToGlobal(position))

        # 根据用户选择执行相应操作
        if action == edit_action:
            self.edit_job()
        elif action == delete_action:
            self.delete_job()
        elif action == toggle_action:
            self.toggle_job()
        elif action == view_log_action:
            self.view_log()


    def open_logs_directory(self):
        """打开日志目录"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            self.open_directory(self.log_dir)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开日志目录：{str(e)}')

    def open_scripts_directory(self):
        """打开脚本目录"""
        try:
            os.makedirs(self.scripts_dir, exist_ok=True)
            self.open_directory(self.scripts_dir)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开脚本目录：{str(e)}')

    def open_directory(self, path):
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', path])
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['explorer', path])
        else:  # Linux and other Unix-like systems
            subprocess.run(['xdg-open', path])

    def show_about(self):
        about_text = '<div style="padding: 20px;">' \
                     f'<h2 style="margin-bottom: 15px;">Chronos {VERSION}</h2>' \
                     '<p style="margin: 10px 0;">一个简单的定时任务管理工具，支持cron表达式，可以方便地管理和监控定时任务。</p>' \
                     '<p style="margin: 10px 0;">GitHub: <a href="https://github.com/konbluesky/chronos.git" style="color: #007bff; text-decoration: none;">https://github.com/konbluesky/chronos.git</a></p>' \
                     '</div>'
        QMessageBox.about(self, '关于', about_text)

    def export_tasks(self):
        """导出任务配置到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '导出任务',
            '',
            'JSON文件 (*.json);;所有文件 (*)'
        )
        if not file_path:
            return

        try:
            tasks = []
            for row in range(self.table.rowCount()):
                task = {
                    'name': self.table.item(row, 0).text(),
                    'command': self.table.item(row, 1).text(),
                    'schedule': self.table.item(row, 2).text(),
                    'enabled': self.table.item(row, 3).text() == '是'
                }
                tasks.append(task)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, '成功', '任务配置已成功导出！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导出任务配置时发生错误：{str(e)}')

    def import_tasks(self):
        """从文件导入任务配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '导入任务',
            '',
            'JSON文件 (*.json);;所有文件 (*)'
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            if not isinstance(tasks, list):
                raise ValueError('无效的任务配置文件格式')

            for task in tasks:
                if not all(key in task for key in ['name', 'command', 'schedule', 'enabled']):
                    raise ValueError('任务配置缺少必要字段')

                # 添加任务到表格
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(task['name']))
                self.table.setItem(row, 1, QTableWidgetItem(task['command']))
                self.table.setItem(row, 2, QTableWidgetItem(task['schedule']))
                self.table.setItem(row, 3, QTableWidgetItem('是' if task['enabled'] else '否'))

            QMessageBox.information(self, '成功', '任务配置已成功导入！')
            self.save_tasks()  # 保存导入的任务
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导入任务配置时发生错误：{str(e)}')

    def save_tasks(self):
        """将表格中的任务保存到 crontab"""
        try:
            # 清空现有的 crontab 任务
            self.cron.remove_all()
            
            # 遍历表格中的所有任务
            for row in range(self.table.rowCount()):
                name = self.table.item(row, 0).text()
                command = self.table.item(row, 1).text()
                schedule = self.table.item(row, 2).text()
                enabled = self.table.item(row, 3).text() == '⬤' and self.table.item(row, 3).foreground().color().name() == '#2e7d32'
                
                # 创建执行脚本
                script_path = self.create_script_file(name, command)
                
                # 添加到 crontab
                job = self.cron.new(command=script_path, comment=name)
                job.setall(schedule)
                
                # 设置任务状态
                if not enabled:
                    job.enable(False)
            
            # 写入 crontab 文件
            self.cron.write()
            self.refresh_jobs()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存任务配置时发生错误：{str(e)}')

    def toggle_stay_on_top(self):
        flags = self.windowFlags()
        if self.stay_on_top_action.isChecked():
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.activateWindow()
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.activateWindow()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 单击
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.svg'))
    window = JobManager()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()