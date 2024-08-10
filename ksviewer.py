import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor, QAction, QPixmap, QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QFileDialog, QMenu, QVBoxLayout, QScrollArea,
                               QFrame)

from kshandler import Commands, ImageMagickHandler
from ksdialogs import MessageDialog, SaveSizeDialog, ExifDialog
from ksfeatures import SaveAs, ImageMagickClip, ViewerPictureLabel


class ImgView(QWidget):
    def __init__(self, img_temp_path, img_path, show_size, need_temp):
        super(ImgView, self).__init__()
        self.commands = Commands()
        self.imagemagick_handler = ImageMagickHandler()

        self.setWindowFlag(Qt.Window, True)

        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.img_path = img_path

        if need_temp:
            self.image_original = QPixmap(img_temp_path)
        else:
            self.image_original = QPixmap(self.img_path)

        self.img_original_width = self.image_original.width()
        self.img_original_height = self.image_original.height()

        self.img_one_third_width = int(self.img_original_width / 3)
        self.img_one_third_height = int(self.img_original_height / 3)
        self.img_one_third_size = QSize(self.img_one_third_width, self.img_one_third_height)
        
        self.image_one_third_size = self.image_original.scaled(self.img_one_third_size, Qt.KeepAspectRatio)

        self.img_half_width = int(self.img_original_width / 2)
        self.img_half_height = int(self.img_original_height / 2)
        self.img_half_size = QSize(self.img_half_width, self.img_half_height)

        self.image_half_size = self.image_original.scaled(self.img_half_size, Qt.KeepAspectRatio)

        screen = QApplication.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()

        if show_size == 'One-third size':
            self.img = self.image_one_third_size
        elif show_size == 'Half size':
            self.img = self.image_half_size
        elif show_size == 'Full size':
            self.img = self.image_original
        else:
            if self.img_original_width + 21 > self.screen_width:
                self.img = self.image_half_size
            else:
                self.img = self.image_original

        img_width = self.img.width()
        img_height = self.img.height()

        self.rename_title(img_width, img_height)

        self.decide_window_size(img_width, img_height)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.picture_layout = QVBoxLayout()
        self.picture_layout.setContentsMargins(0, 0, 0, 0)

        self.picture_widget = QWidget()
        self.picture_widget.setLayout(self.picture_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(self.picture_widget)

        self.label = ViewerPictureLabel()
        self.label.setAlignment(Qt.AlignTop)
        self.picture_layout.addWidget(self.label)
        self.label.setPixmap(self.img)

        self.exif_dialog = None
        self.message_dialog = None
        self.save_size_dialog = None

        self.clip_width = int()
        self.clip_height = int()
        self.clip_begin_x = int()
        self.clip_begin_y = int()

        self.menu = QMenu()
        self.action_one_third_size = QAction('One-third size')
        self.action_half_size = QAction('Half size')
        self.action_full_size = QAction('Full size')
        self.action_show_exif = QAction('Show Exif')
        self.action_save_as = QAction('Save as')

        self.action_clip = QAction('Save this clip')

        self.label.mouse_painter_signal.connect(self.clip_ready)
        self.label.mouse_right_click_signal.connect(self.right_click_menu)

        self.action_one_third_size.triggered.connect(self.show_one_third_size)
        self.action_half_size.triggered.connect(self.show_half_size)
        self.action_full_size.triggered.connect(self.show_full_size)
        self.action_show_exif.triggered.connect(self.show_exif)
        self.action_save_as.triggered.connect(self.save_dialog)

        self.action_clip.triggered.connect(self.clip_dialog)

    def clip_ready(self, width, height, begin_x, begin_y):
        if begin_x > self.img.width() or begin_y > self.img.height():
            return

        self.clip_width = width
        self.clip_height = height
        self.clip_begin_x = begin_x
        self.clip_begin_y = begin_y

        self.menu.clear()
        self.menu.addAction(self.action_clip)
        self.menu.move(QCursor.pos())
        self.menu.show()

    def clip_dialog(self):
        img_name = os.path.basename(self.img_path)
        img_name = img_name.split('.')
        target_default_name = f'{img_name[0]}_clip'

        target_path = QFileDialog.getSaveFileName(
            self,
            caption='Save File',
            dir=os.path.join(self.commands.read_pictures_folder_path(), f'{target_default_name}.png'),
            filter="PNG (*.png);;JPEG (*.jpg);;GIF (*.gif)"
        )

        imagemagick_program_status, imagemagick_program_path = \
            self.imagemagick_handler.check_imagemagick_available()

        if imagemagick_program_status and target_path[0]:
            if self.img == self.image_original:
                resize_option = ''
            else:
                img_width = self.img.width()
                resize_option = str(img_width)
            imagemagick_clip_thread = ImageMagickClip(
                self.img_path, target_path[0], resize_option,
                self.clip_width, self.clip_height, self.clip_begin_x, self.clip_begin_y
            )
            imagemagick_clip_thread.clip_result_signal.connect(self.clip_result)

    def clip_result(self, target_path):
        target_name = os.path.basename(target_path)
        self.message_dialog = MessageDialog(f'The picture is clipped as {target_name} successfully!')
        self.message_dialog.show()

    def decide_window_size(self, img_width, img_height):
        if os.name == 'nt':
            if img_width < self.screen_width:
                if img_width + 17 > self.screen_width:
                    window_width = self.screen_width
                else:
                    window_width = img_width
            else:
                window_width = self.screen_width

            if self.screen_height < 1080:
                if img_height < int(self.screen_height * 0.95):
                    if img_height + 17 < int(self.screen_height * 0.95):
                        window_height = img_height
                    else:
                        window_height = int(self.screen_height * 0.95)
                else:
                    window_height = int(self.screen_height * 0.95)
            else:
                if img_height < int(self.screen_height * 0.975):
                    if img_height + 17 < int(self.screen_height * 0.975):
                        window_height = img_height
                    else:
                        window_height = int(self.screen_height * 0.975)
                else:
                    window_height = int(self.screen_height * 0.975)

            if window_height != img_height and img_width + 17 < self.screen_width:
                window_width = img_width + 17

        else:
            if img_width < self.screen_width:
                if img_width + 17 > self.screen_width:
                    window_width = self.screen_width
                else:
                    window_width = img_width
            else:
                window_width = self.screen_width

            if self.screen_height < 1080:
                if img_height < int(self.screen_height * 0.95):
                    if img_height + 17 < int(self.screen_height * 0.95):
                        window_height = img_height
                    else:
                        window_height = int(self.screen_height * 0.95)
                else:
                    window_height = int(self.screen_height * 0.95)
            else:
                if img_height < int(self.screen_height * 0.975):
                    if img_height + 17 < int(self.screen_height * 0.975):
                        window_height = img_height
                    else:
                        window_height = int(self.screen_height * 0.975)
                else:
                    window_height = int(self.screen_height * 0.975)

            if window_height != img_height and img_width + 17 < self.screen_width:
                window_width = img_width + 17

        if window_height != img_height:
            self.setGeometry(
                int((self.screen_width - window_width) / 2),
                33,
                window_width, window_height
            )
        else:
            self.setGeometry(
                int((self.screen_width - window_width) / 2),
                int((self.screen_height - window_height) / 2),
                window_width, window_height
            )

    def right_click_menu(self, event):
        self.menu.clear()

        if self.img == self.image_one_third_size:
            self.menu.addAction(self.action_half_size)
            self.menu.addAction(self.action_full_size)
            self.menu.addAction(self.action_show_exif)
            self.menu.addAction(self.action_save_as)

        if self.img == self.image_half_size:
            self.menu.addAction(self.action_one_third_size)
            self.menu.addAction(self.action_full_size)
            self.menu.addAction(self.action_show_exif)
            self.menu.addAction(self.action_save_as)

        if self.img == self.image_original:
            self.menu.addAction(self.action_one_third_size)
            self.menu.addAction(self.action_half_size)
            self.menu.addAction(self.action_show_exif)
            self.menu.addAction(self.action_save_as)

        self.menu.move(QCursor.pos())
        self.menu.show()

    def show_exif(self):
        exif_details = self.imagemagick_handler.read_exif(self.img_path)
        self.exif_dialog = ExifDialog(exif_details)
        self.exif_dialog.show()

    def rename_title(self, img_width, img_height):
        title_text = f'{os.path.basename(self.img_path)} | Current size: {img_width}x{img_height}'
        self.setWindowTitle(title_text)

    def show_one_third_size(self):
        self.img = self.image_one_third_size
        self.label.setPixmap(self.img)

        img_width = self.img.width()
        img_height = self.img.height()

        self.rename_title(img_width, img_height)

        self.decide_window_size(img_width, img_height)

    def show_half_size(self):
        self.img = self.image_half_size
        self.label.setPixmap(self.img)

        img_width = self.img.width()
        img_height = self.img.height()

        self.rename_title(img_width, img_height)

        self.decide_window_size(img_width, img_height)

    def show_full_size(self):
        self.img = self.image_original
        self.label.setPixmap(self.img)

        img_width = self.image_original.width()
        img_height = self.image_original.height()

        self.rename_title(img_width, img_height)

        self.decide_window_size(img_width, img_height)

    def save_dialog(self):
        self.save_size_dialog = SaveSizeDialog(
            f'{self.img.width()}x{self.img.height()}',
            f'{self.image_original.width()}x{self.image_original.height()}'
        )
        self.save_size_dialog.show()

        self.save_size_dialog.option_signal.connect(self.save_path)

    def save_path(self, resize_option, img_quality, img_format):
        target_default_name = self.commands.get_filename(self.img_path)

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
            save_as_thread = SaveAs(self.img_path, target_path[0], resize_option, img_quality)
            save_as_thread.save_as_result_signal.connect(
                lambda: self.save_as(target_path[0])
            )

    def save_as(self, target_path):
        target_name = os.path.basename(target_path)
        self.message_dialog = MessageDialog(
            f'The picture is saved as {target_name} successfully!'
        )
        self.message_dialog.show()
