import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QProgressBar, QComboBox, QLabel,
                               QScrollArea, QFileDialog, QMenu, QFrame)
from PySide6.QtGui import QPixmap, QAction, QCursor, QIcon

from kshandler import Commands, ImageMagickHandler
from ksfeatures import PictureLabel, SaveAs, OpenFolder, ReadSubdirectories, ImportImages, ExportPDF
from ksdialogs import MessageDialog, YesNoDialog, ExifDialog, SaveSizeDialog, MakePDFDialog
from ksshowpicture import ShowPicture
from ksviewer import ImgView


class Show(QWidget):
    def __init__(self, window_width):
        super(Show, self).__init__()
        self.commands = Commands()
        self.imagemagick_handler = ImageMagickHandler()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.features_layout = QHBoxLayout()
        self.features_layout.setContentsMargins(5, 0, 5, 5)
        self.item_info_layout = QHBoxLayout()
        self.item_info_layout.setContentsMargins(5, 5, 5, 5)
        self.album_layout = QVBoxLayout()

        self.layout.addLayout(self.features_layout)
        self.layout.addLayout(self.item_info_layout)

        self.img_path_dialog_button = QPushButton('View a picture')
        self.img_path_dialog_button.setFixedSize(120, 30)
        self.img_path_dialog_button.clicked.connect(self.img_path_dialog)

        self.folder_path_dialog_button = QPushButton('Open a folder')
        self.folder_path_dialog_button.setFixedSize(120, 30)
        self.folder_path_dialog_button.clicked.connect(self.folder_path_dialog)

        self.refresh_button = QPushButton('Refresh Album')
        self.refresh_button.setFixedSize(120, 30)
        self.refresh_button.clicked.connect(self.refresh_album)

        self.import_images_button = QPushButton('Import Images')
        self.import_images_button.setFixedSize(120, 30)
        self.import_images_button.clicked.connect(self.import_images)

        self.import_status = QWidget()
        self.import_status.setFixedSize(300, 100)
        self.import_status.setWindowTitle('Import Process')
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.import_status.setWindowIcon(QIcon(logo_path))

        self.import_status_layout = QVBoxLayout()
        self.import_status.setLayout(self.import_status_layout)
        self.import_progressbar = QProgressBar()
        self.import_progressbar.setFixedWidth(200)
        self.import_progressbar.setRange(0, 0)
        self.import_status_layout.addWidget(self.import_progressbar)
        self.import_info = QLabel()
        self.import_status_layout.addWidget(self.import_info)

        self.rolling_progressbar = QProgressBar()
        self.rolling_progressbar.setFixedWidth(200)
        self.rolling_progressbar.setRange(0, 0)

        self.features_layout.setAlignment(Qt.AlignLeft)
        self.features_layout.addWidget(self.img_path_dialog_button)
        self.features_layout.addWidget(self.folder_path_dialog_button)
        self.features_layout.addWidget(self.refresh_button)
        self.features_layout.addWidget(self.import_images_button)
        self.features_layout.addWidget(self.rolling_progressbar)

        self.rolling_progressbar.hide()

        self.pictures_folder_button = QPushButton('Home')
        self.pictures_folder_button.setFixedSize(60, 25)
        self.pictures_folder_button.clicked.connect(self.open_pictures_folder)

        self.subdirectories_combobox = QComboBox()
        self.subdirectories_combobox.setFixedWidth(200)

        self.message_label = QLabel()
        self.item_path = QLabel()

        self.item_info_layout.setAlignment(Qt.AlignLeft)
        self.item_info_layout.addWidget(self.pictures_folder_button)
        self.item_info_layout.addWidget(self.subdirectories_combobox)
        self.item_info_layout.addWidget(self.message_label)
        self.item_info_layout.addWidget(self.item_path)

        self.album_widget = QWidget()
        self.album_widget.setLayout(self.album_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.layout.addWidget(self.scroll_area)

        self.window_width = window_width
        self.window_height = int()

        self.menu = QMenu()
        self.action_one_third_size = QAction('One-third size')
        self.action_half_size = QAction('Half size')
        self.action_full_size = QAction('Full size')
        self.action_show_exif = QAction('Show Exif')
        self.action_save_as = QAction('Save as')
        self.action_export_pdf = QAction('Export PDF')
        self.action_remove_permanently = QAction('Remove permanently')

        self.mouse_left_click_start_time = None
        self.mouse_slide_start_x = None
        self.mouse_slide_start_y = None

        self.cache_folder_path = self.commands.read_cache_folder_path()
        self.pictures_folder_path = self.commands.read_pictures_folder_path()

        self.current_album_path = str()

        self.subdirectories_dict = dict()

        self.last_subdirectory = str()

        self.picture = dict()
        self.picture_label = dict()
        self.canvas_item = dict()

        self.picture_lock = dict()

        self.previous_lines_number = int()
        self.album_parts_number = int()
        self.album_pictures_list = list()
        self.pictures_data_dict = dict()
        self.album_pictures_part = dict()
        self.continue_button = dict()

        self.album_shown_widgets_list = list()
        self.album_refresh_pictures_list = list()
        self.album_refresh_continue_button_number = int()
        self.album_refresh_mode = False

        self.current_img_path = str()
        self.current_show_size = str()

        self.continue_button_number = int()

        self.yesno_dialog = None
        self.exif_dialog = None
        self.message_dialog = None
        self.save_size_dialog = None
        self.export_pdf_dialog = None
        self.image_viewer = None

        if os.path.exists(self.pictures_folder_path):
            self.open_album()
            self.show_subdirectories()
        else:
            self.message_label.setText('No valid album is found.')

        self.subdirectories_combobox.activated.connect(self.open_subdirectory)

        self.action_one_third_size.triggered.connect(lambda: self.view_original_picture('One-third size'))
        self.action_half_size.triggered.connect(lambda: self.view_original_picture('Half size'))
        self.action_full_size.triggered.connect(lambda: self.view_original_picture('Full size'))
        self.action_show_exif.triggered.connect(self.show_exif)
        self.action_save_as.triggered.connect(self.save_dialog)
        self.action_export_pdf.triggered.connect(self.export_pdf)
        self.action_remove_permanently.triggered.connect(self.open_yesno_dialog)

        self.export_pdf_dialog = MakePDFDialog()
        self.export_pdf_dialog.option_signal.connect(self.save_pdf_path)
        self.action_export_pdf.triggered.connect(lambda: self.export_pdf_dialog.add_picture(self.current_img_path))

    def resizeEvent(self, event):
        self.window_width = event.size().width()
        self.window_height = event.size().height()

    def refresh_album(self):
        if os.path.exists(self.pictures_folder_path):
            self.album_refresh_mode = True
            self.open_album()
        else:
            self.message_label.setText('The album does not exist.')

    def open_album(self):
        self.folder_path_dialog_button.setDisabled(True)
        self.refresh_button.setDisabled(True)
        self.subdirectories_combobox.setDisabled(True)
        self.pictures_folder_button.setDisabled(True)

        for widget in self.album_shown_widgets_list:
            widget.hide()

        self.album_shown_widgets_list = []

        self.album()

    def album(self):
        if not self.current_album_path:
            folder_path = self.pictures_folder_path
        else:
            folder_path = self.current_album_path

        self.previous_lines_number = int()
        self.album_pictures_list = list()
        self.pictures_data_dict = dict()
        self.album_pictures_part = dict()
        self.continue_button = dict()

        pictures_path_data, _, _, pictures_cached_name_data = self.commands.read_latest_pictures_data()

        self.pictures_data_dict = dict(zip(pictures_path_data, pictures_cached_name_data))

        for picture_path in pictures_path_data:
            if folder_path in picture_path:
                self.album_pictures_list.append(picture_path)

        self.album_parts_number = int(len(self.album_pictures_list) / 200) + 1

        for n in range(self.album_parts_number):
            start = n * 200
            stop = start + 200
            self.album_pictures_part[n] = self.album_pictures_list[start:stop]
            if n == self.album_parts_number - 1:
                self.album_pictures_part[n] = self.album_pictures_list[start:]

        if self.album_refresh_pictures_list:
            self.album_part(self.album_refresh_pictures_list, self.album_refresh_continue_button_number)
        else:
            self.album_part(self.album_pictures_part[0], 0)

        self.refresh_button.setDisabled(False)
        self.folder_path_dialog_button.setDisabled(False)
        self.subdirectories_combobox.setDisabled(False)
        self.pictures_folder_button.setDisabled(False)

    def album_part(self, album_pictures_list, continue_button_number):
        line = dict()
        line_width = 0
        n = 0
        line[0] = list()
        for picture_path in album_pictures_list:
            if os.path.exists(picture_path):
                picture_cached_name = self.pictures_data_dict[picture_path]

                if picture_cached_name:
                    picture_cached_path = os.path.join(self.cache_folder_path, picture_cached_name)
                else:
                    picture_cached_path = ''

                if os.path.exists(picture_cached_path):
                    picture_width = QPixmap(picture_cached_path).width()
                    line_width = line_width + picture_width + 5
                    if line_width + 5 >= self.window_width:
                        n = n + 1
                        line[n] = list()
                        line_width = 0 + picture_width + 5

                    line[n].append(picture_path)

        lines_number = len(line)
        line_layout = dict()
        for n in range(lines_number):
            line_layout[n] = QHBoxLayout()
            line_layout[n].setAlignment(Qt.AlignLeft)
            self.album_layout.addLayout(line_layout[n])
            for img in line[n]:
                picture_cached_name = self.pictures_data_dict[img]
                picture_cached_path = os.path.join(self.cache_folder_path, picture_cached_name)

                m = self.album_pictures_list.index(img)
                self.picture[m] = QPixmap(picture_cached_path)
                self.picture_label[m] = PictureLabel()
                self.picture_label[m].setPixmap(self.picture[m])

                self.picture_label[m].mouse_right_click_signal.connect(
                    lambda event, img_path=img: self.right_click_menu(event, img_path)
                )
                self.picture_label[m].mouse_double_click_signal.connect(
                    lambda event, img_path=img: self.double_click_picture(img_path)
                )
                self.picture_label[m].mouse_enter_signal.connect(
                    lambda event, img_path=img: self.mouse_enter(img_path)
                )
                self.picture_label[m].mouse_leave_signal.connect(self.mouse_leave)

                line_layout[n].addWidget(self.picture_label[m])

                self.album_shown_widgets_list.append(self.picture_label[m])
                if not self.album_refresh_mode:
                    self.album_refresh_pictures_list.append(img)

        self.previous_lines_number = self.previous_lines_number + lines_number

        self.continue_button_number = continue_button_number
        self.album_refresh_continue_button_number = self.continue_button_number

        if continue_button_number + 1 < self.album_parts_number - 1:
            self.continue_button[continue_button_number] = QPushButton('Click to continue')
            self.continue_button[continue_button_number].setFixedSize(120, 25)
            self.album_layout.addWidget(self.continue_button[continue_button_number])
            self.album_shown_widgets_list.append(self.continue_button[continue_button_number])
            self.continue_button[continue_button_number].clicked.connect(self.next_part)

        self.scroll_area.setWidget(self.album_widget)

    def next_part(self):
        self.album_refresh_mode = False
        self.continue_button[self.continue_button_number].hide()
        self.album_part(self.album_pictures_part[self.continue_button_number + 1], self.continue_button_number + 1)

    def mouse_enter(self, img_path):
        if os.path.exists(img_path):
            picture_creation_time = self.commands.read_picture_creation_time(img_path)
            self.item_path.setText(f'{img_path} {picture_creation_time}')

    def mouse_leave(self):
        self.item_path.setText('')

    def right_click_menu(self, event, img_path):
        self.current_img_path = img_path

        self.menu.addAction(self.action_one_third_size)
        self.menu.addAction(self.action_half_size)
        self.menu.addAction(self.action_full_size)
        self.menu.addAction(self.action_show_exif)
        self.menu.addAction(self.action_save_as)
        self.menu.addAction(self.action_export_pdf)
        self.menu.addAction(self.action_remove_permanently)

        self.menu.move(QCursor.pos())
        self.menu.show()

    def show_exif(self):
        exif_details = self.imagemagick_handler.read_exif(self.current_img_path)
        self.exif_dialog = ExifDialog(exif_details)
        self.exif_dialog.show()

    def double_click_picture(self, img_path):
        self.current_img_path = img_path
        self.view_original_picture('Half size')

    def view_original_picture(self, show_size):
        if self.current_img_path not in self.picture_lock.keys() or not self.picture_lock[self.current_img_path]:
            if os.path.exists(self.current_img_path):
                self.current_show_size = show_size
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

    def open_yesno_dialog(self):
        self.yesno_dialog = YesNoDialog(self.current_img_path)
        self.yesno_dialog.option_signal.connect(
            lambda option: self.yesno_dialog_option(option, self.current_img_path)
        )
        self.yesno_dialog.show()

    def yesno_dialog_option(self, option, img_path):
        if option == 'Yes':
            self.remove_permanently(img_path)

    def remove_permanently(self, img_path):
        m = self.album_pictures_list.index(img_path)
        self.picture_label[m].hide()

        os.remove(img_path)

        picture_cached_name = self.pictures_data_dict[img_path]
        picture_cached_path = os.path.join(self.cache_folder_path, picture_cached_name)

        reserved_cache_files_list = self.commands.check_reserved_cache_files()
        if picture_cached_path not in reserved_cache_files_list:
            if os.path.exists(picture_cached_path):
                os.remove(picture_cached_path)

        self.commands.remove_picture_record(img_path)

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
            self.current_show_size = 'Half size'
            self.rolling_progressbar.show()
            show_picture = ShowPicture(self.current_img_path)
            show_picture.show_picture_error_signal.connect(self.show_picture_error)
            show_picture.show_picture_result_signal.connect(self.show_picture_result)

    def folder_path_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            caption='Open Folder',
            dir=self.commands.read_pictures_folder_path()
        )
        if folder_path:
            folder_path = os.path.normpath(folder_path)
            self.open_folder(folder_path)

    def open_folder(self, folder_path):
        self.album_refresh_pictures_list = list()
        self.album_refresh_continue_button_number = int()
        self.album_refresh_mode = False

        self.current_album_path = folder_path
        folder_name = os.path.basename(folder_path)

        if folder_path not in self.subdirectories_dict.values():
            self.show_subdirectories()
        else:
            self.subdirectories_combobox.setCurrentText(folder_name)

        self.features_layout.addWidget(self.rolling_progressbar)
        self.rolling_progressbar.setMinimum(0)
        self.rolling_progressbar.setMaximum(0)

        open_folder_thread = OpenFolder(folder_path)
        open_folder_thread.scan_result_signal.connect(self.scan_result)
        open_folder_thread.open_folder_signal.connect(self.open_album)

    def scan_result(self, scanned_files_number):
        self.rolling_progressbar.hide()
        self.message_label.setText(f'Found {scanned_files_number} images.')

    def save_dialog(self):
        self.save_size_dialog = SaveSizeDialog('', '')
        self.save_size_dialog.show()

        self.save_size_dialog.option_signal.connect(self.save_path)

    def save_path(self, resize_option, img_quality, img_format):
        target_default_name = self.commands.get_filename(self.current_img_path)

        if img_format == 'JPEG (.jpg)':
            target_path = QFileDialog.getSaveFileName(
                self,
                caption='Save File',
                dir=os.path.join(self.commands.read_pictures_folder_path(), f'{target_default_name}.jpg'),
                filter="JPEG (*.jpg)"
            )
        elif img_format == 'PNG (.png)':
            target_path = QFileDialog.getSaveFileName(
                self,
                caption='Save File',
                dir=os.path.join(self.commands.read_pictures_folder_path(), f'{target_default_name}.png'),
                filter="PNG (*.png)"
            )
        elif img_format == 'WebP (.webp)':
            target_path = QFileDialog.getSaveFileName(
                self,
                caption='Save File',
                dir=os.path.join(self.commands.read_pictures_folder_path(), f'{target_default_name}.webp'),
                filter="WebP (*.webp)"
            )
        else:
            target_path = QFileDialog.getSaveFileName(
                self,
                caption='Save File',
                dir=os.path.join(self.commands.read_pictures_folder_path(), f'{target_default_name}.gif'),
                filter="GIF (*.gif)"
            )

        if target_path[0]:
            save_as_thread = SaveAs(self.current_img_path, target_path[0], resize_option, img_quality)
            save_as_thread.save_as_result_signal.connect(
                lambda: self.save_as(target_path[0])
            )

    def save_as(self, target_path):
        target_name = os.path.basename(target_path)
        self.message_dialog = MessageDialog(
            f'The picture is saved as {target_name} successfully!'
        )
        self.message_dialog.show()

    def export_pdf(self):
        self.export_pdf_dialog.show()

    def save_pdf_path(self, file_with_resolution_list, page_size_value, page_layout_value, background_colour_value, density_value, img_quality_value):
        target_default_name = self.commands.get_filename(self.current_img_path)

        target_path = QFileDialog.getSaveFileName(
            self,
            caption='Save File',
            dir=os.path.join(self.commands.read_pictures_folder_path(), f'{target_default_name}.pdf'),
            filter="PDF (*.pdf)"
        )

        if target_path[0]:
            export_pdf_thread = ExportPDF(file_with_resolution_list, target_path[0], page_size_value, page_layout_value,
                                          background_colour_value, density_value, img_quality_value)
            export_pdf_thread.export_pdf_result_signal.connect(
                lambda: self.save_pdf_result(target_path[0])
            )

    def save_pdf_result(self, target_path):
        target_name = os.path.basename(target_path)
        self.message_dialog = MessageDialog(
            f'The PDF document is successfully exported as {target_name}!'
        )
        self.message_dialog.show()

    def show_subdirectories(self):
        if self.current_album_path:
            folder_path = self.current_album_path
        else:
            folder_path = self.pictures_folder_path

        read_subdirectories_thread = ReadSubdirectories(folder_path)
        read_subdirectories_thread.subdirectories_dict_signal.connect(self.receive_subdirectories_dict)
        read_subdirectories_thread.subdirectories_signal.connect(self.set_subdirectories_combobox)

    def receive_subdirectories_dict(self, subdirectories_dict):
        self.subdirectories_dict = subdirectories_dict

    def set_subdirectories_combobox(self, images_included_subdirectories_name_list):
        self.subdirectories_combobox.clear()
        self.subdirectories_combobox.addItems(images_included_subdirectories_name_list)
        self.subdirectories_combobox.setEditable(False)

        self.subdirectories_combobox.setCurrentIndex(-1)
        if self.current_album_path:
            self.subdirectories_combobox.setPlaceholderText(os.path.basename(self.current_album_path))
        else:
            self.subdirectories_combobox.setPlaceholderText(os.path.basename(self.pictures_folder_path))

    def open_subdirectory(self):
        if self.subdirectories_combobox.currentText():
            folder_name = self.subdirectories_combobox.currentText()
            folder_path = self.subdirectories_dict[folder_name]
            self.open_folder(folder_path)

    def open_pictures_folder(self):
        self.album_refresh_pictures_list = list()
        self.album_refresh_continue_button_number = int()
        self.album_refresh_mode = False

        self.pictures_folder_path = self.commands.read_pictures_folder_path()
        self.current_album_path = self.pictures_folder_path
        self.message_label.setText('')

        self.open_album()
        self.show_subdirectories()

    def import_images(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            caption='Choose the folder from which images will be imported',
            dir=self.commands.read_pictures_folder_path()
        )
        if folder_path:
            folder_path = os.path.normpath(folder_path)
            import_images = ImportImages(folder_path)

            import_images.imported_number_signal.connect(self.import_result)
            import_images.import_finish_signal.connect(self.import_result)

            self.import_status.show()
            self.import_progressbar.show()
            self.import_info.setText('Searching images ...')

    def import_result(self, value1, value2):
        if value2 != 'Done':
            self.import_info.setText(f'Please wait ... {value2} images are imported.')
        if value2 == 'Done':
            self.import_progressbar.hide()
            self.import_info.setText(f'Import is finished. {value1} images are imported.')
            self.open_folder(self.pictures_folder_path)
