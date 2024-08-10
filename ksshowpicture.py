import os
from threading import Thread
from PySide6.QtCore import Signal, QObject

from kshandler import Commands, ImageMagickHandler


class ShowPicture(QObject):
    show_picture_error_signal = Signal(str)
    show_picture_result_signal = Signal(str, bool)

    def __init__(self, img_path):
        super(ShowPicture, self).__init__()
        self.commands = Commands()
        self.imagemagick_handler = ImageMagickHandler()

        self.temp_folder_path = self.commands.read_temp_folder_path()

        self.imgview_dialog = None
        self.message_dialog = None
        self.picture_lock = dict()

        thread = Thread(target=self.start, args=(img_path,))
        thread.daemon = True
        thread.start()

    def start(self, img_path):
        img_file_type = self.commands.get_filetype(img_path)
        imagemagick_supported_formats = self.commands.imagemagick_supported_formats()

        exif_details = self.imagemagick_handler.read_exif(img_path)
        jpeg_formats = ['.jpeg', '.JPEG', '.jpg', '.JPG']
        need_rotation = False
        if 'Orientation' in exif_details.keys() and img_file_type in jpeg_formats:
            if exif_details['Orientation'] != '1':
                need_rotation = True

        if img_file_type in imagemagick_supported_formats or need_rotation:
            self.recognize_picture(img_path)
        else:
            self.show_picture('', False)

    def recognize_picture(self, img_path):
        img_name = os.path.basename(img_path)
        img_name = img_name.split('.')
        img_temp_name_png = f'{img_name[0]}.png'
        img_temp_name_jpg = f'{img_name[0]}.jpg'
        img_temp_path_png = os.path.join(self.temp_folder_path, img_temp_name_png)
        img_temp_path_jpg = os.path.join(self.temp_folder_path, img_temp_name_jpg)
        if os.path.exists(img_temp_path_png):
            self.show_picture(img_temp_path_png, True)
        elif os.path.exists(img_temp_path_jpg):
            self.show_picture(img_temp_path_jpg, True)
        else:
            self.picture_lock[img_path] = True
            resize_option = ''

            self.convert_picture(img_path, resize_option)

    def convert_picture(self, img_path, resize_option):
        img_name = os.path.basename(img_path)
        img_name = img_name.split('.')
        target_name = f'{img_name[0]}.jpg'

        target_path = os.path.join(self.temp_folder_path, target_name)

        convert_result = self.imagemagick_handler.convert_picture(img_path, target_path, resize_option, '')

        if convert_result:
            self.show_picture(target_path, True)
            self.picture_lock[img_path] = False

    def show_picture(self, img_temp_path, need_temp):
        if img_temp_path and not os.path.exists(img_temp_path):
            error = 'Sorry, there is an error when trying to open the file.\n' \
                    'The error may be caused by the following reasons:\n' \
                    '1. The format is not supported;\n' \
                    '2. The compression mode of the format is not supported.'
            self.show_picture_error_signal.emit(error)
        else:
            self.show_picture_result_signal.emit(img_temp_path, need_temp)
