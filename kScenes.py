import sys
import os
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar,
                               QLabel)

from kshandler import Commands
from ksshowpicture import ShowPicture
from ksshow import Show
from kssettings import Settings, About
from ksviewer import ImgView
from ksdialogs import MessageDialog


class ViewerMode(QWidget):
    def __init__(self):
        super(ViewerMode, self).__init__()
        self.commands = Commands()

        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.setWindowTitle('kScenes')

        screen = app.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()

        self.setGeometry(int((self.screen_width - 350) / 2), int((self.screen_height - 100) / 2), 350, 100)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.button_layout = QVBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.img_path_dialog_button = QPushButton('View a picture')
        self.button_layout.addWidget(self.img_path_dialog_button)
        self.img_path_dialog_button.setFixedSize(150, 20)
        self.img_path_dialog_button.clicked.connect(self.img_path_dialog)

        self.rolling_progressbar = QProgressBar()
        self.button_layout.addWidget(self.rolling_progressbar)
        self.rolling_progressbar.setFixedWidth(200)
        self.rolling_progressbar.setMinimum(0)
        self.rolling_progressbar.setMaximum(0)
        self.rolling_progressbar.hide()

        self.message_layout = QVBoxLayout()
        self.layout.addLayout(self.message_layout)

        self.message_label = QLabel()
        self.message_layout.addWidget(self.message_label)

        self.message_dialog = None
        self.image_viewer = None

        self.current_img_path = str()
        self.current_show_size = 'Half size'

        app_parameter_image, app_parameter_info = self.commands.get_app_parameter()

        if app_parameter_info == 'No support':
            self.message_label.setText(f'The file {os.path.basename(app_parameter_image)} is not supported!')
        elif app_parameter_info == 'Not found':
            self.message_label.setText(f'The file {os.path.basename(app_parameter_image)} is not found!')
        else:
            self.show_picture(app_parameter_image)
            self.message_label.setText('Currently kScenes is in Viewer Mode.')

    def show_picture(self, app_parameter_image):
        self.current_img_path = app_parameter_image
        show_picture = ShowPicture(self.current_img_path)
        show_picture.show_picture_error_signal.connect(self.show_picture_error)
        show_picture.show_picture_result_signal.connect(self.show_picture_result)

        self.setWindowState(Qt.WindowMinimized)

    def img_path_dialog(self):
        supported_formats = self.commands.read_supported_formats()
        filter_formats = str()

        for format_name in supported_formats:
            format_name = f'*{format_name}'
            filter_formats = filter_formats + ' ' + format_name

        img_path = QFileDialog.getOpenFileName(
            self,
            caption='Open File',
            dir=self.commands.read_pictures_folder_path(),
            filter=f'Supported files ({filter_formats});;All files (*.*)'
        )

        if img_path[0]:
            self.current_img_path = img_path[0]
            self.rolling_progressbar.show()
            show_picture = ShowPicture(self.current_img_path)
            show_picture.show_picture_error_signal.connect(self.show_picture_error)
            show_picture.show_picture_result_signal.connect(self.show_picture_result)

    def show_picture_error(self, error):
        self.rolling_progressbar.hide()
        self.message_dialog = MessageDialog(error)
        self.message_dialog.show()

    def show_picture_result(self, img_temp_path, need_temp):
        self.rolling_progressbar.hide()
        self.image_viewer = ImgView(img_temp_path, self.current_img_path, self.current_show_size, need_temp)
        self.image_viewer.show()

    def closeEvent(self, event):
        self.commands.remove_temp_folder()


class AlbumMode(QWidget):
    def __init__(self):
        super(AlbumMode, self).__init__()

        self.window_max_geometry = 'max'
        self.window_geometry = None
        self.window_max = None

        self.commands = Commands()

        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.setWindowTitle('kScenes')

        screen = app.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()

        latest_geometry_data = self.commands.read_latest_geometry()
        zoomed_size_data = self.commands.read_zoomed_size()
        latest_geometry = latest_geometry_data.split(',')
        if len(latest_geometry) == 4:
            window_x = int(latest_geometry[0])
            window_y = int(latest_geometry[1])
            window_width = int(latest_geometry[2])
            window_height = int(latest_geometry[3])
            if latest_geometry_data == zoomed_size_data:
                self.setWindowState(Qt.WindowMaximized)
        else:
            window_width = 1050
            if self.screen_height < 1080:
                window_height = 600
            else:
                window_height = 900
            window_x = int((self.screen_width - window_width) / 2)
            window_y = int((self.screen_height - window_height) / 2)

        self.setGeometry(window_x, window_y, window_width, window_height)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(5, 5, 5, 5)
        self.top_layout.setAlignment(Qt.AlignRight)
        self.layout.addLayout(self.top_layout)

        self.top_button_about = QPushButton('About')
        self.top_button_about.setFixedSize(80, 25)

        self.top_button_settings = QPushButton('Settings')
        self.top_button_settings.setFixedSize(80, 25)

        self.top_layout.addWidget(self.top_button_settings)
        self.top_layout.addWidget(self.top_button_about)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.main_layout)

        self.album_layout = QVBoxLayout()
        self.album_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.album_layout)
        self.album = Show(window_width)
        self.album_layout.addWidget(self.album)

        self.settings = Settings()
        self.about = About()

        self.settings_status = False
        self.about_status = False

        self.top_button_settings.clicked.connect(self.show_settings)
        self.top_button_about.clicked.connect(self.show_about)

        self.settings.return_home_signal.connect(self.album.open_pictures_folder)

    def get_current_geometry(self):
        x = self.geometry().x()
        y = self.geometry().y()
        width = self.geometry().width()
        height = self.geometry().height()

        right_x = x + width
        
        settings_x = right_x - 620
        settings_y = y + 50

        about_x = right_x - 520
        about_y = y + 50

        return settings_x, settings_y, about_x, about_y

    def show_settings(self):
        x, y, _, _ = self.get_current_geometry()

        self.settings.move(x, y)
        self.settings.show()
        self.settings_status = True

    def show_about(self):
        _, _, x, y = self.get_current_geometry()

        self.about.move(x, y)
        self.about.show()
        self.about_status = True

    def changeEvent(self, event):
        if self.geometry() != self.window_max_geometry:
            self.window_geometry = self.geometry()

        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                self.window_max = True
                self.window_max_geometry = self.geometry()

            elif self.window_max:
                self.window_max = False

                if self.window_geometry != self.window_max_geometry:
                    self.setGeometry(self.window_geometry)
                else:
                    window_width = 1050
                    if self.screen_height < 1080:
                        window_height = 600
                    else:
                        window_height = 900
                    window_x = int((self.screen_width - window_width) / 2)
                    window_y = int((self.screen_height - window_height) / 2)
                    self.setGeometry(window_x, window_y, window_width, window_height)
        
    def closeEvent(self, event):
        self.commands.remove_temp_folder()

        current_geometry = f'{self.geometry().x()},{self.geometry().y()},' \
                           f'{self.geometry().width()},{self.geometry().height()}'
        self.commands.save_latest_geometry(current_geometry)
        if self.windowState() == Qt.WindowMaximized:
            self.commands.save_zoomed_size(current_geometry)


if __name__ == '__main__':
    app = QApplication([])

    app_parameter_image, _ = Commands().get_app_parameter()
    if app_parameter_image:
        main_window = ViewerMode()
    else:
        main_window = AlbumMode()

    main_window.show()

    sys.exit(app.exec())
