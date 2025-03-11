import os
import sys
from PyQt6.QtCore import QTimer, QTime, Qt, QUrl
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QSystemTrayIcon, QMenu, QRadioButton
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class KClockWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resource_dir = getattr(sys, '_MEIPASS', os.path.abspath("."))
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(self.get_resource_path('Kclock.png')))
        
        # 初始化变量
        self.curTime = QTime.currentTime()
        self.leftTime = QTime(0, 0, 0)
        self.clock = False
        self.alarm_duration = 0  # 0表示一直播放
        
        # 定时器设置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

        # 初始化闪烁定时器
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_icon)
        self.icon_visible = True
        
        # 先初始化变量
        resource_path = self.get_resource_path('Kclock.mp3')
        if os.path.exists(resource_path):
            self.mpUrl = QUrl.fromLocalFile(resource_path)
        else:
            self.mpUrl = QUrl()
        
        # 初始化媒体播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)  # 设置默认循环播放
        
        # 初始化UI
        self.init_ui()
        
        # 设置默认音乐
        self.set_default_music()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

    def get_resource_path(self, filename):
        return os.path.join(self.resource_dir, filename)
        

    
    def init_ui(self):
        # 主窗口设置
        self.setWindowTitle('Kclock（作者：曹开春）')
        
        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 时间显示区域
        self.current_time_label = QLabel('')
        self.current_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_time_label.hide()
        main_layout.addWidget(self.current_time_label)
        
        # 剩余时间和闹钟时间显示
        time_layout = QHBoxLayout()
        self.left_time_label = QLabel('剩余时间: --:--:--')
        self.alarm_time_label = QLabel('闹钟时间: --:--:--')
        time_layout.addWidget(self.left_time_label)
        time_layout.addWidget(self.alarm_time_label)
        main_layout.addLayout(time_layout)
        
        # 按钮布局
        self.create_control_buttons(main_layout)
        
        # 系统托盘图标
        self.create_system_tray()
    
    def create_control_buttons(self, layout):
        # 音乐选择控件
        music_group = QWidget()
        music_layout = QHBoxLayout(music_group)
        
        self.default_radio = QRadioButton('默认铃声')
        self.custom_radio = QRadioButton('自定义铃声')
        self.music_select_btn = QPushButton('选择音乐文件')
        self.music_select_btn.clicked.connect(self.select_music)
        self.music_select_btn.hide()
        
        self.default_radio.toggled.connect(lambda: self.set_default_music())
        self.default_radio.toggled.connect(lambda: self.music_select_btn.setHidden(True))
        self.custom_radio.toggled.connect(lambda: self.music_select_btn.setVisible(True))
        self.default_radio.setChecked(True)
        
        music_layout.addWidget(QLabel('闹钟音乐:'))
        music_layout.addWidget(self.default_radio)
        music_layout.addWidget(self.custom_radio)
        music_layout.addWidget(self.music_select_btn)
        layout.addWidget(music_group)

        # 时间调整按钮
        time_buttons = [
            ('+1m', 60), ('+5m', 300), ('+30m', 1800),
            ('-1m', -60), ('-5m', -300), ('-30m', -1800),
            ('+10s', 10), ('-10s', -10)
        ]
        
        btn_layout = QHBoxLayout()
        for text, value in time_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, v=value: self.adjust_time(v))
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        
        # 倒计时控制按钮
        self.start_btn = QPushButton('开始倒计时')
        self.start_btn.clicked.connect(self.toggle_clock)
        self.start_btn.hide()
        layout.addWidget(self.start_btn)
        
        # 试听按钮
        self.preview_btn = QPushButton('试听')
        self.preview_btn.clicked.connect(self.toggle_preview)
        layout.addWidget(self.preview_btn)
        
        # 退出按钮
        exit_btn = QPushButton('退出闹钟')
        exit_btn.clicked.connect(self.close)
        exit_btn.clicked.connect(QApplication.instance().quit)
        exit_btn.clicked.connect(self.cleanup_resources)
        layout.addWidget(exit_btn)
    
    def create_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.get_resource_path('Kclock.png')))
        
        tray_menu = QMenu()
        show_action = QAction('显示', self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(QApplication.instance().quit)
        exit_action.triggered.connect(self.cleanup_resources)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def adjust_time(self, seconds):
        total_seconds = self.leftTime.hour() * 3600 + self.leftTime.minute() * 60 + self.leftTime.second()
        total_seconds = max(0, total_seconds + seconds)
        self.leftTime = QTime(0, 0, 0).addSecs(total_seconds)
        
        # 更新界面显示
        self.left_time_label.setText('剩余时间: ' + self.leftTime.toString('HH:mm:ss'))
        alarm_time = QTime.currentTime().addSecs(total_seconds)
        self.alarm_time_label.setText('闹钟时间: ' + alarm_time.toString('HH:mm:ss'))

        # 停止当前播放的音乐
        self.player.stop()
        self.blink_timer.stop()

        # 更新当前时间并启动定时器
        self.curTime = QTime.currentTime()
        if not self.timer.isActive():
            self.clock = True
            self.start_btn.setText('停止倒计时')
            self.start_btn.show()
            self.current_time_label.show()
            self.timer.start(1000)
    
    def set_default_music(self):
        resource_path = self.get_resource_path('Kclock.mp3')
        if os.path.exists(resource_path):
            self.mpUrl = QUrl.fromLocalFile(resource_path)
            self.player.setSource(self.mpUrl)
        else:
            self.alarm_time_label.setText('错误: 找不到默认音频文件')

    def select_music(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择音乐文件', '', '音频文件 (*.mp3 *.wav)')
        if file_name:
            try:
                self.player.setSource(QUrl.fromLocalFile(file_name))
                self.mpUrl = QUrl.fromLocalFile(file_name)
                self.custom_radio.setChecked(True)
            except Exception as e:
                self.alarm_time_label.setText(f'错误: {str(e)}')
            # 更新预览播放器源
            if hasattr(self, 'preview_player'):
                self.preview_player.setSource(self.mpUrl)

    def toggle_icon(self):
        self.icon_visible = not self.icon_visible
        if self.icon_visible:
            self.tray_icon.setIcon(QIcon(self.get_resource_path('Kclock.png')))
        else:
            self.tray_icon.setIcon(QIcon())

    def toggle_clock(self):
        self.clock = not self.clock
        if self.clock:
            self.start_btn.setText('停止倒计时')
            self.start_btn.show()
            self.current_time_label.show()
            self.timer.start(1000)
            self.blink_timer.start(500)  # 500ms闪烁间隔
            self.curTime = QTime.currentTime()
        else:
            self.start_btn.setText('开始倒计时')
            self.start_btn.hide()
            self.current_time_label.hide()
            self.leftTime = QTime(0, 0, 0)
            self.left_time_label.setText('剩余时间: --:--:--')
            self.alarm_time_label.setText('闹钟时间: --:--:--')
            self.player.stop()
            self.timer.stop()
            self.blink_timer.stop()
            self.tray_icon.setIcon(QIcon(self.get_resource_path('Kclock.png')))
    
    def toggle_preview(self):
        if self.preview_btn.text() == '试听':
            self.preview_player = QMediaPlayer()
            self.preview_audio_output = QAudioOutput()
            self.preview_player.setAudioOutput(self.preview_audio_output)
            self.preview_player.setSource(self.mpUrl)
            self.preview_btn.setText('停止试听')
            self.preview_player.play()
            # 添加错误状态监听
            self.preview_player.errorOccurred.connect(self.handle_preview_error)
            self.preview_player.playbackStateChanged.connect(self.handle_preview_state)
        else:
            self.preview_player.stop()
            self.preview_btn.setText('试听')

    def handle_preview_error(self, error):
        self.alarm_time_label.setText(f'播放错误: {error.name}')
        self.preview_btn.setText('试听')
    
    def handle_preview_state(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.preview_btn.setText('试听')
    
    def update_time(self):
        # 更新当前时间
        self.curTime = self.curTime.addSecs(1)
        self.current_time_label.setText('当前时间: ' + self.curTime.toString('HH:mm:ss'))
        
        # 更新剩余时间
        total_seconds = self.leftTime.hour() * 3600 + \
                      self.leftTime.minute() * 60 + \
                      self.leftTime.second()
        
        if total_seconds > 0:
            total_seconds -= 1
            self.leftTime = self.leftTime.addSecs(-1)
            self.left_time_label.setText('剩余时间: ' + self.leftTime.toString('HH:mm:ss'))
        
        # 触发闹钟
        if self.clock and total_seconds <= 0:
            self.player.play()
            self.blink_timer.start(500)
            self.left_time_label.setText('剩余时间: --:--:--')
            self.alarm_time_label.setText('闹钟时间: --:--:--')

    def cleanup_resources(self):
        self.timer.stop()
        self.blink_timer.stop()
        self.player.stop()
        self.audio_output.deleteLater()
        self.player.deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KClockWindow()
    window.show()
    sys.exit(app.exec())
