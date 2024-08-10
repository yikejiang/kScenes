import os
import sys
import webbrowser
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QComboBox, QLabel,
                               QFileDialog, QStyle)

from kshandler import Commands, ImageMagickHandler
from ksfeatures import SettingsScanFolder, CleanDatabaseAndCache
from ksdialogs import MessageDialog


class Settings(QWidget):
    return_home_signal = Signal()

    def __init__(self):
        super(Settings, self).__init__()

        # Instantiation and definition
        self.commands = Commands()
        self.imagemagick_handler = ImageMagickHandler()

        self.temp_folder_path = self.commands.read_temp_folder_path()
        self.stop_caching_signal = os.path.join(self.temp_folder_path, 'stop_caching_signal')

        self.pictures_folder_path = self.commands.read_pictures_folder_path()

        self.message_dialog = None
        self.folder_path_dialog_status = False

        # Layouts
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.setWindowTitle('Settings')
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(600)

        self.top_layout = QVBoxLayout()
        self.top_layout.setAlignment(Qt.AlignTop)
        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.setAlignment(Qt.AlignTop)
        self.layout.addLayout(self.top_layout)
        self.layout.addLayout(self.bottom_layout)

        self.top_layout.setContentsMargins(15, 20, 0, 10)
        self.bottom_layout.setContentsMargins(15, 0, 0, 25)

        self.folder_layout = QVBoxLayout()
        
        self.cache_layout = QHBoxLayout()
        self.cache_layout.setAlignment(Qt.AlignLeft)

        self.cache_buttons_layout = QHBoxLayout()
        self.cache_buttons_layout.setSpacing(0)

        self.info_layout = QVBoxLayout()
        self.changes_info_layout = QVBoxLayout()
        self.progress_info_layout = QVBoxLayout()

        self.top_layout.addLayout(self.folder_layout)
        self.top_layout.addLayout(self.cache_layout)

        self.top_layout.addLayout(self.info_layout)
        self.top_layout.addLayout(self.changes_info_layout)
        self.top_layout.addLayout(self.progress_info_layout)

        self.notice_layout = QVBoxLayout()
        
        self.bottom_layout.addLayout(self.notice_layout)
        
        # Set default folder
        self.folder_path_dialog_button = QPushButton('Set default folder')
        self.folder_path_dialog_button.setFixedSize(150, 30)
        self.folder_layout.addWidget(self.folder_path_dialog_button)
        self.folder_path_dialog_button.clicked.connect(self.folder_path_dialog)

        # Cache default folder
        # Set multiprocessing number
        self.cache_threads_option_label = QLabel('Caching Option')
        self.cache_threads_option_label.setFixedWidth(90)
        self.cache_threads_option_label.setToolTip(
            'A higher number accelerates indexing and caching with higher CPU usage.'
        )
        self.cache_layout.addWidget(self.cache_threads_option_label)

        self.cache_threads_option = QComboBox()
        self.cache_threads_option.setFixedWidth(35)
        self.cache_layout.addWidget(self.cache_threads_option)

        max_cache_threads_number = int(os.cpu_count() / 2)
        cache_threads_number_list = list()
        for n in range(max_cache_threads_number):
            cache_threads_number_list.append(str(n+1))

        self.cache_threads_option.addItems(cache_threads_number_list)
        self.cache_threads_option.setEditable(False)

        saved_cache_threads_number = self.commands.read_cache_threads_number()
        if not saved_cache_threads_number:
            self.cache_threads_option.setCurrentText(max_cache_threads_number)
        else:
            self.cache_threads_option.setCurrentText(str(saved_cache_threads_number))

        self.cache_threads_option.activated.connect(self.save_cache_threads_value)

        # Control caching process
        self.cache_layout.addLayout(self.cache_buttons_layout)

        self.stop_caching_button = QPushButton()
        self.stop_caching_button.setDisabled(True)
        self.stop_caching_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_caching_button.setToolTip('Stop caching')
        self.stop_caching_button.setFixedSize(30, 30)
        self.cache_buttons_layout.addWidget(self.stop_caching_button)
        self.stop_caching_button.clicked.connect(self.stop_caching)

        self.start_caching_button = QPushButton()
        self.start_caching_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.start_caching_button.setToolTip('Start scanning and caching')
        self.start_caching_button.setFixedSize(30, 30)
        self.cache_buttons_layout.addWidget(self.start_caching_button)
        self.start_caching_button.clicked.connect(self.start_caching)

        # Clean index data and cache files
        self.clean_database_and_cache_button = QPushButton()
        self.clean_database_and_cache_button.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.clean_database_and_cache_button.setFixedSize(30, 30)
        self.clean_database_and_cache_button.setToolTip(
            'Remove database records of pictures not found in default folder;\n'
            'Remove duplicate records from database;\n'
            'Remove cache folder\'s files not related to default folder\'s pictures.'
        )
        self.cache_buttons_layout.addWidget(self.clean_database_and_cache_button)
        self.clean_database_and_cache_button.clicked.connect(self.clean_database_and_cache)

        # Show caching progress
        self.scan_progressbar = QProgressBar()
        self.scan_progressbar.setFixedWidth(300)
        self.cache_layout.addWidget(self.scan_progressbar)
        self.scan_progressbar.hide()

        self.cache_progressbar = QProgressBar()
        self.cache_progressbar.setFixedWidth(300)
        self.cache_layout.addWidget(self.cache_progressbar)
        self.cache_progressbar.hide()

        # Show the results of scanning and caching
        self.info_label = QLabel()
        self.info_layout.addWidget(self.info_label)

        self.changes_info_label = QLabel()
        self.changes_info_layout.addWidget(self.changes_info_label)

        self.progress_info_label = QLabel()
        self.progress_info_layout.addWidget(self.progress_info_label)

        # Show notice
        self.notice_label = QLabel()
        self.notice_layout.addWidget(self.notice_label)
        imagemagick_program_status, imagemagick_program_path = \
            self.imagemagick_handler.check_imagemagick_available()
        if not imagemagick_program_status:
            if sys.platform == 'darwin':
                self.notice_label.setText(
                    'If you have installed ImageMagick, make sure that "convert" and "identify"\n'
                    'are in the folder "/opt/local/bin".'
                )
            elif os.name == 'posix':
                self.notice_label.setText(
                    'You may install ImageMagick for your distro.\n'
                    'Make sure that "convert" and "identify" are in the folder "/usr/bin".\n'
                    'And make sure that ImageMagick\'s library for HEIC is installed.'
                )
            else:
                self.notice_label.setText('')

        # Scan default folder when the app starts
        self.start_caching()

    def save_cache_threads_value(self):
        cache_threads_number = self.cache_threads_option.currentText()
        self.commands.save_cache_threads_number(cache_threads_number)

    def folder_path_dialog(self):
        self.folder_path_dialog_status = True

        folder_path = QFileDialog.getExistingDirectory(
            self,
            caption='Set Default Folder',
            dir=self.pictures_folder_path
        )

        self.folder_path_dialog_status = False

        if folder_path:
            folder_path = os.path.normpath(folder_path)
            self.commands.save_pictures_folder_path(folder_path)
            self.pictures_folder_path = folder_path
            self.scan_folder(folder_path)

    def stop_caching(self):
        with open(self.stop_caching_signal, 'w') as temp:
            temp.write('')

    def start_caching(self):
        if os.path.exists(self.stop_caching_signal):
            os.remove(self.stop_caching_signal)

        self.scan_folder(self.pictures_folder_path)

    def scan_folder(self, folder_path):
        if not os.path.exists(self.pictures_folder_path):
            self.info_label.setText(
                f'Default pictures folder {self.pictures_folder_path} does not exist.\n'
                f'Please set a valid folder.'
            )
            return

        self.folder_path_dialog_button.setDisabled(True)
        self.start_caching_button.setDisabled(True)
        self.clean_database_and_cache_button.setDisabled(True)
        
        self.scan_progressbar.show()
        self.scan_progressbar.setMinimum(0)
        self.scan_progressbar.setMaximum(0)

        settings_scan_folder_thread = SettingsScanFolder(folder_path)
        settings_scan_folder_thread.scan_result_signal.connect(self.scan_result)
        settings_scan_folder_thread.nochange_signal.connect(self.pictures_nochange)
        settings_scan_folder_thread.pictures_changes_result_signal.connect(self.pictures_changes_result)
        settings_scan_folder_thread.cachepictures_progress_signal.connect(self.cachepictures_progress)
        settings_scan_folder_thread.cachepictures_result_signal.connect(self.cachepictures_result)

    def scan_result(self, scanned_files_number):
        self.scan_progressbar.hide()

        self.info_label.setText(f'Default pictures folder is {self.pictures_folder_path}.\n'
                                f'Found {scanned_files_number} images.')

    def pictures_nochange(self):
        self.changes_info_label.setText(f'There is no change.')
        self.folder_path_dialog_button.setDisabled(False)
        self.start_caching_button.setDisabled(False)
        self.clean_database_and_cache_button.setDisabled(False)

    def pictures_changes_result(self, removed_number, moved_number, added_number):
        added_number_info = f'There are {added_number} newly added images.\n'
        moved_number_info = f'Positional changes of {moved_number} images are found.\n'
        removed_number_info = f'{removed_number} images have been removed from the folder.'

        if added_number == 0:
            added_number_info = ''
            self.folder_path_dialog_button.setDisabled(False)
        if moved_number == 0:
            moved_number_info = ''
        if removed_number == 0:
            removed_number_info = ''

        if added_number == 1:
            added_number_info = 'A newly added image is found.\n'
        if moved_number == 1:
            moved_number_info = 'There is the positional change of an image.\n'
        if removed_number == 1:
            removed_number_info = 'An image has been removed from the folder.'

        self.changes_info_label.setText(f'{added_number_info}'
                                        f'{moved_number_info}'
                                        f'{removed_number_info}')

        self.folder_path_dialog_button.setDisabled(False)
        self.clean_database_and_cache_button.setDisabled(False)

    def cachepictures_progress(self, src_path, handled_percents):
        self.stop_caching_button.setDisabled(False)
        self.cache_progressbar.show()
        self.cache_progressbar.setRange(0, 100)
        self.cache_progressbar.setValue(handled_percents)
        self.changes_info_label.setText('Pictures are being indexed and cached by multiprocessing.\n'
                                        'The process may have high CPU usage and '
                                        'it will take a lot of time.')
        self.progress_info_label.setText(f'{src_path} is handled.')

    def cachepictures_result(self, cached_img_number):
        self.stop_caching_button.setDisabled(True)
        self.start_caching_button.setDisabled(False)
        if cached_img_number == 1:
            self.progress_info_label.setText('An image is cached this time.')
        elif cached_img_number == 0:
            self.progress_info_label.setText('No image is cached this time.')
        else:
            self.progress_info_label.setText(f'{cached_img_number} images are cached this time.')
        self.cache_progressbar.hide()

    def clean_database_and_cache(self):
        self.folder_path_dialog_button.setDisabled(True)
        self.start_caching_button.setDisabled(True)
        self.clean_database_and_cache_button.setDisabled(True)

        clean_database_and_cache_thread = CleanDatabaseAndCache()
        clean_database_and_cache_thread.clean_database_and_cache_result_signal.connect(
            self.clean_database_and_cache_result
        )

    def clean_database_and_cache_result(
            self, removed_records_number, removed_files_number, database_records_number, cache_folder_files_number
    ):

        if removed_records_number == 0:
            removed_records_info = 'No record is removed from database.'
        elif removed_records_number == 1:
            removed_records_info = 'Removed one record from database.'
        else:
            removed_records_info = f'Removed {removed_records_number} records from database.'

        if removed_files_number == 0:
            removed_files_info = 'No file is removed from cache folder.'
        elif removed_files_number == 1:
            removed_files_info = 'Removed one file from cache folder.'
        else:
            removed_files_info = f'Removed {removed_files_number} files from cache folder.'

        self.message_dialog = MessageDialog(
            f'{removed_records_info}\n{removed_files_info}\n'
            f'Currently there are {database_records_number} records in the database.\n'
            f'And there are {cache_folder_files_number} files in cache folder.'
        )
        self.close()
        self.message_dialog.show()

        self.return_home_signal.emit()

        self.folder_path_dialog_button.setDisabled(False)
        self.start_caching_button.setDisabled(False)
        self.clean_database_and_cache_button.setDisabled(False)

    def changeEvent(self, event):
        if not self.isActiveWindow() and not self.folder_path_dialog_status:
            self.close()


class About(QWidget):
    def __init__(self):
        super(About, self).__init__()
        self.commands = Commands()

        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.setWindowTitle('About kScenes')
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.setFixedWidth(500)

        self.top_layout = QHBoxLayout()
        self.layout.addLayout(self.top_layout)

        self.app_name = QLabel('kScenes')
        self.app_name.setContentsMargins(15, 30, 0, 10)
        self.app_name_font = QFont()
        self.app_name_font.setPointSize(40)
        self.app_name_font.setBold(True)
        self.app_name.setFont(self.app_name_font)
        self.top_layout.addWidget(self.app_name)

        version = '3.1.0'
        self.app_version = QLabel()
        self.app_version.setContentsMargins(25, 55, 0, 10)
        self.app_version_font = QFont()
        self.app_version_font.setPointSize(12)
        self.app_version.setFont(self.app_version_font)
        self.app_version.setText(
            f'Version {version}'
        )
        self.top_layout.addWidget(self.app_version)

        self.app_description_one = QLabel()
        self.app_description_one.setContentsMargins(15, 5, 0, 5)

        if os.name == 'nt':
            self.app_description_one.setText(
                'kScenes is a viewer for pictures in PNG, GIF, HEIC, JPEG, WEBP, BMP, TIFF,\n'
                'DCM, DDS and XCF formats. A picture can be converted to the format PNG,\n'
                'JPEG, WebP or GIF. kScenes supports resizing and clipping a picture.\n'
                'Moreover, you may create multiple-page PDF document from pictures.'
            )
        elif sys.platform == 'darwin':
            self.app_description_one.setText(
                'kScenes is a viewer for pictures in PNG, GIF, HEIC, JPEG, WEBP, BMP, TIFF,\n'
                'DCM, DDS and XCF formats. A picture can be converted to the format PNG,\n'
                'JPEG, WebP or GIF. kScenes supports resizing and clipping a picture.\n'
                'Moreover, you may create multiple-page PDF document from pictures.'
            )
        else:
            self.app_description_one.setText(
                'kScenes for Linux is a viewer for pictures in PNG, GIF, HEIC, JPEG, WEBP,\n'
                'BMP, TIFF, DCM, DDS and XCF formats. A picture can be converted to the\n'
                'format PNG, JPEG, WebP or GIF. kScenes supports resizing and clipping a\n'
                'picture. Moreover, you may create multiple-page PDF document from pictures.\n\n'
                'ImageMagick is needed for handling images.'
            )

        self.layout.addWidget(self.app_description_one)

        self.app_description_two = QLabel()
        self.app_description_two.setContentsMargins(15, 5, 0, 5)
        self.app_description_two.setText(
            'kScenes is released as free software under GNU General Public License\n'
            'version 3.\n\n'
            'kScenes is designed using Python and PySide6. The app includes Qt libraries\n'
            'and ImageMagick.\n\n'
            'PySide6 is Qt module for Python to output interface, while ImageMagick is\n'
            'a command-line program that handles images.\n\n'
            'kScenes uses Qt libraries dynamically under GNU Lesser General Public\n'
            'License version 3. There is no modification in Qt source code.\n\n'
            'The copyright of ImageMagick is owned by ImageMagick Studio LLC. The\n'
            'use of ImageMagick is licensed under the ImageMagick License.'
        )
        self.layout.addWidget(self.app_description_two)

        self.app_website_layout = QVBoxLayout()
        self.layout.addLayout(self.app_website_layout)

        self.app_website_link_layout = QVBoxLayout()
        self.layout.addLayout(self.app_website_link_layout)

        self.app_website_description = QLabel()
        self.app_website_description.setContentsMargins(15, 5, 0, 5)
        self.app_website_description.setText(
            'For more information, please visit the official website of kScenes:'
        )
        self.app_website_layout.addWidget(self.app_website_description)

        self.app_website_link = QLabel()
        self.app_website_link.setContentsMargins(15, 5, 0, 25)
        self.app_website_link.setText('<a href="https://www.kscenes.com">https://www.kscenes.com</a>')
        self.app_website_link_layout.addWidget(self.app_website_link)
        self.app_website_link.linkActivated.connect(self.open_link)

    def changeEvent(self, event):
        if not self.isActiveWindow():
            self.close()

    @staticmethod
    def open_link():
        webbrowser.open('https://www.kscenes.com')
