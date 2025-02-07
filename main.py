import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QDialog, QLabel, QLineEdit, QFormLayout, QMessageBox,
                             QHeaderView, QComboBox, QTextEdit, QScrollBar, QMenu,
                             QToolBar, QStatusBar, QSizePolicy, QSystemTrayIcon)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QAction, QCursor
import os
import datetime
from crontab import CronTab

class CronEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)  # 增加垂直间距
        layout.setContentsMargins(10, 10, 10, 10)  # 添加边距

        # 创建水平布局来组织时间选择器
        time_layout = QHBoxLayout()
        time_layout.setSpacing(20)  # 设置水平间距

        # 创建各个时间单位的选择器
        self.minute_combo = self.create_combo_box('分钟', ['*'] + [str(i) for i in range(60)])
        self.hour_combo = self.create_combo_box('小时', ['*'] + [str(i) for i in range(24)])
        self.day_combo = self.create_combo_box('日期', ['*'] + [str(i) for i in range(1, 32)])
        self.month_combo = self.create_combo_box('月份', ['*'] + [str(i) for i in range(1, 13)])
        self.weekday_combo = self.create_combo_box('星期', ['*', '0', '1', '2', '3', '4', '5', '6'])

        # 添加到水平布局
        time_layout.addWidget(self.minute_combo)
        time_layout.addWidget(self.hour_combo)
        time_layout.addWidget(self.day_combo)
        time_layout.addWidget(self.month_combo)
        time_layout.addWidget(self.weekday_combo)

        # 将水平布局添加到主布局
        layout.addLayout(time_layout)

        # 添加表达式翻译标签
        self.translation_label = QLabel()
        self.translation_label.setWordWrap(True)
        self.translation_label.setStyleSheet('padding: 10px; background-color: rgba(0, 0, 0, 0.1); border-radius: 5px;')
        layout.addWidget(self.translation_label)
        layout.addStretch()  # 添加弹性空间

        # 连接信号
        self.minute_combo.findChild(QComboBox).currentTextChanged.connect(self.update_cron_expression)
        self.hour_combo.findChild(QComboBox).currentTextChanged.connect(self.update_cron_expression)
        self.day_combo.findChild(QComboBox).currentTextChanged.connect(self.update_cron_expression)
        self.month_combo.findChild(QComboBox).currentTextChanged.connect(self.update_cron_expression)
        self.weekday_combo.findChild(QComboBox).currentTextChanged.connect(self.update_cron_expression)

        self.cron_expression = '* * * * *'
        self.update_translation()

    def create_combo_box(self, label, items):
        widget = QWidget()
        layout = QVBoxLayout(widget)  # 改为垂直布局
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)  # 设置垂直间距

        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐
        combo = QComboBox()
        combo.setFixedWidth(80)  # 统一下拉框宽度

        layout.addWidget(label_widget)
        layout.addWidget(combo)

        combo.addItems(items)
        return widget

    def update_cron_expression(self):
        minute = self.minute_combo.findChild(QComboBox).currentText()
        hour = self.hour_combo.findChild(QComboBox).currentText()
        day = self.day_combo.findChild(QComboBox).currentText()
        month = self.month_combo.findChild(QComboBox).currentText()
        weekday = self.weekday_combo.findChild(QComboBox).currentText()

        self.cron_expression = f'{minute} {hour} {day} {month} {weekday}'
        self.update_translation()

    def update_translation(self):
        translation = '当前规则：'
        minute, hour, day, month, weekday = self.cron_expression.split()

        # 翻译分钟
        if minute == '*':
            translation += '每分钟'
        else:
            translation += f'第 {minute} 分钟'

        # 翻译小时
        if hour == '*':
            translation += '的每小时'
        else:
            translation += f'的 {hour} 点'

        # 翻译日期
        if day == '*':
            if weekday == '*':
                translation += '的每一天'
            else:
                translation += ''
        else:
            translation += f'的 {day} 日'

        # 翻译月份
        if month == '*':
            translation += ''
        else:
            translation += f'的 {month} 月'

        # 翻译星期
        if weekday != '*':
            weekday_names = ['日', '一', '二', '三', '四', '五', '六']
            translation += f'的星期{weekday_names[int(weekday)]}'

        translation += '执行'
        self.translation_label.setText(translation)

    def get_cron_expression(self):
        return self.cron_expression

    def set_cron_expression(self, expression):
        try:
            parts = expression.strip().split()
            if len(parts) == 5:
                self.minute_combo.findChild(QComboBox).setCurrentText(parts[0])
                self.hour_combo.findChild(QComboBox).setCurrentText(parts[1])
                self.day_combo.findChild(QComboBox).setCurrentText(parts[2])
                self.month_combo.findChild(QComboBox).setCurrentText(parts[3])
                self.weekday_combo.findChild(QComboBox).setCurrentText(parts[4])
        except Exception:
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
        self.setMinimumWidth(600)  # 增加窗口宽度

        # 创建并设置输入框
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumWidth(400)
        self.command_edit = QLineEdit()
        self.command_edit.setMinimumWidth(400)
        self.cron_editor = CronEditor()

        # 设置标签的对齐方式
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 添加表单项
        layout.addRow('任务名称:', self.name_edit)
        layout.addRow('执行命令:', self.command_edit)
        layout.addRow('执行计划:', self.cron_editor)

        # 创建按钮布局
        buttons = QHBoxLayout()
        buttons.setSpacing(10)  # 设置按钮之间的间距
        self.ok_button = QPushButton('确定')
        self.cancel_button = QPushButton('取消')
        self.ok_button.setFixedWidth(100)  # 统一按钮宽度
        self.cancel_button.setFixedWidth(100)
        buttons.addStretch()
        buttons.addWidget(self.ok_button)
        buttons.addWidget(self.cancel_button)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        layout.addRow('', buttons)

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
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton('清除日志')
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.update_log()

    def update_log(self):
        try:
            with open(self.log_file, 'r') as f:
                content = f.read()
                if content != self.log_text.toPlainText():
                    self.log_text.setText(content)
                    self.log_text.verticalScrollBar().setValue(
                        self.log_text.verticalScrollBar().maximum()
                    )
        except Exception as e:
            self.log_text.setText(f"无法读取日志文件：{str(e)}")

    def clear_log(self):
        try:
            with open(self.log_file, 'w') as f:
                f.write(f"=== Log cleared at {datetime.datetime.now()} ===\n")
            self.update_log()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'清除日志失败：{str(e)}')

class JobManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chronos - 时序管理器')
        self.setup_ui()
        self.cron = CronTab(user=True)
        self.log_dir = os.path.expanduser('~/.job_manager/logs')
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_tray()
        self.refresh_jobs()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.svg'))
        self.tray_icon.setToolTip('任务管理器')

        # 创建托盘菜单
        self.tray_menu = QMenu()
        self.show_action = QAction('显示主窗口', self)
        self.show_action.triggered.connect(self.show)
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addSeparator()

        # 添加状态子菜单
        self.status_menu = QMenu('任务状态', self)
        self.tray_menu.addMenu(self.status_menu)
        self.tray_menu.addSeparator()

        self.quit_action = QAction('退出', self)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # 连接托盘图标的点击信号
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # 左键单击
            self.show()
            self.activateWindow()

    def update_status_menu(self):
        self.status_menu.clear()
        for job in self.cron:
            status = '启用' if job.is_enabled() else '禁用'
            action = QAction(f'{job.comment}: {status}', self)
            action.setEnabled(False)
            self.status_menu.addAction(action)
        if self.status_menu.isEmpty():
            action = QAction('暂无任务', self)
            action.setEnabled(False)
            self.status_menu.addAction(action)

    def refresh_jobs(self):
        self.table.setRowCount(0)
        enabled_count = 0
        disabled_count = 0
        for job in self.cron:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(job.comment)))
            self.table.setItem(row, 1, QTableWidgetItem(str(job.command)))
            self.table.setItem(row, 2, QTableWidgetItem(str(job.slices)))
            self.table.setItem(row, 3, QTableWidgetItem('启用' if job.is_enabled() else '禁用'))
            if job.is_enabled():
                enabled_count += 1
            else:
                disabled_count += 1
        
        total_count = enabled_count + disabled_count
        self.status_bar.showMessage(f'总任务数: {total_count} | 已启用: {enabled_count} | 已禁用: {disabled_count}')
        self.update_status_menu()
        self.update_status_menu()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage('任务管理器', '程序已最小化到系统托盘', QSystemTrayIcon.MessageIcon.Information)

    def setup_ui(self):
        self.setMinimumSize(1000, 500)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建菜单栏
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')
        self.add_action = QAction('添加任务', self)
        self.add_action.setShortcut('Ctrl+N')
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

        self.toggle_action = QAction('启用/禁用任务', self)
        self.toggle_action.setShortcut('Ctrl+T')
        self.toggle_action.setToolTip('启用或禁用选中的任务')
        edit_menu.addAction(self.toggle_action)

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

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # 创建工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                font-size: 14px;
                padding: 8px;
                margin: 2px;
                min-width: 40px;
            }
        """)

        # 添加动作到工具栏
        toolbar.addAction(self.add_action)
        toolbar.addAction(self.edit_action)
        toolbar.addAction(self.delete_action)
        toolbar.addAction(self.toggle_action)
        toolbar.addAction(self.view_log_action)
        toolbar.addAction(self.refresh_action)


        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['任务名称', '执行命令', '执行计划', '状态'])
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 100)  # 调整任务名称列宽度
        self.table.setColumnWidth(3, 60)  # 调整状态列宽度
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁用编辑
        
        # 设置表格选择模式为整行选择
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # 添加右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')

        # 连接信号
        self.add_action.triggered.connect(self.add_job)
        self.edit_action.triggered.connect(self.edit_job)
        self.delete_action.triggered.connect(self.delete_job)
        self.toggle_action.triggered.connect(self.toggle_job)
        self.refresh_action.triggered.connect(self.refresh_jobs)
        self.view_log_action.triggered.connect(self.view_log)

    def add_job(self):
        dialog = JobDialog(self)
        if dialog.exec():
            name = dialog.name_edit.text()
            command = dialog.command_edit.text()
            schedule = dialog.cron_editor.get_cron_expression()

            try:
                log_file = os.path.join(self.log_dir, f"{name}.log")
                wrapped_command = f"{command} >> \"{log_file}\" 2>&1"
                job = self.cron.new(command=wrapped_command, comment=name)
                job.setall(schedule)
                try:
                    self.cron.write()
                except IOError as e:
                    if 'Operation not permitted' in str(e):
                        QMessageBox.critical(self, '权限错误',
                            '无法修改定时任务，因为当前用户没有足够的权限。\n\n'
                            '请尝试以下解决方案：\n'
                            '1. 使用管理员权限运行此程序\n'
                            '2. 确保当前用户有权限修改crontab文件')
                        return
                    raise e
                # 创建日志文件
                with open(log_file, 'a') as f:
                    f.write(f"=== Job created at {datetime.datetime.now()} ===\n")
                self.refresh_jobs()
            except Exception as e:
                error_msg = str(e)
                if 'Operation not permitted' in error_msg:
                    QMessageBox.critical(self, '权限错误',
                        '无法修改定时任务，因为当前用户没有足够的权限。\n\n'
                        '请尝试以下解决方案：\n'
                        '1. 使用管理员权限运行此程序\n'
                        '2. 确保当前用户有权限修改crontab文件')
                else:
                    QMessageBox.critical(self, '错误', f'添加任务失败：{error_msg}')

    def edit_job(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '警告', '请先选择一个任务')
            return

        name = self.table.item(current_row, 0).text()
        for job in self.cron:
            if job.comment == name:
                dialog = JobDialog(self)
                dialog.name_edit.setText(name)
                dialog.command_edit.setText(job.command)
                dialog.cron_editor.set_cron_expression(str(job.slices))

                if dialog.exec():
                    try:
                        job.command = dialog.command_edit.text()
                        job.setall(dialog.cron_editor.get_cron_expression())
                        job.comment = dialog.name_edit.text()
                        self.cron.write()
                        self.refresh_jobs()
                    except Exception as e:
                        QMessageBox.critical(self, '错误', f'编辑任务失败：{str(e)}')
                break

    def delete_job(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '警告', '请先选择一个任务')
            return

        name = self.table.item(current_row, 0).text()
        reply = QMessageBox.question(self, '确认', f'确定要删除任务 "{name}" 吗？',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            for job in self.cron:
                if job.comment == name:
                    self.cron.remove(job)
                    self.cron.write()
                    self.refresh_jobs()
                    break

    def refresh_jobs(self):
        self.table.setRowCount(0)
        enabled_count = 0
        disabled_count = 0
        for job in self.cron:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(job.comment)))
            self.table.setItem(row, 1, QTableWidgetItem(str(job.command)))
            self.table.setItem(row, 2, QTableWidgetItem(str(job.slices)))
            self.table.setItem(row, 3, QTableWidgetItem('启用' if job.is_enabled() else '禁用'))
            if job.is_enabled():
                enabled_count += 1
            else:
                disabled_count += 1
        
        total_count = enabled_count + disabled_count
        self.status_bar.showMessage(f'总任务数: {total_count} | 已启用: {enabled_count} | 已禁用: {disabled_count}')
        self.update_status_menu()

    def view_log(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, '警告', '请先选择一个任务')
            return

        name = self.table.item(current_row, 0).text()
        log_file = os.path.join(self.log_dir, f"{name}.log")
        
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

    def show_context_menu(self, position):
        menu = QMenu()
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

    def show_about(self):
        QMessageBox.about(self, '关于', 'Chronos - 时序管理器 v1.0\n\n一个简单的定时任务管理工具，支持cron表达式，可以方便地管理和监控定时任务。')


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.svg'))
    window = JobManager()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()