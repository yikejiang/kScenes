import os
import shutil
from queue import Queue as queue_Queue
from threading import Thread
from PySide6.QtCore import Signal, QObject, Qt, QRect
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPen, QPainter

from kshandler import Commands, ImageMagickHandler
from ksscan import MultiprocessingFolderScan
from kscache import HandlePicturesChanges


class PictureLabel(QLabel):
    mouse_left_click_signal = Signal(object)
    mouse_right_click_signal = Signal(object)
    mouse_double_click_signal = Signal(object)
    mouse_enter_signal = Signal(object)
    mouse_leave_signal = Signal()

    def __init__(self):
        super(PictureLabel, self).__init__()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_left_click_signal.emit(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_right_click_signal.emit(event)

    def mouseDoubleClickEvent(self, event):
        self.mouse_double_click_signal.emit(event)

    def enterEvent(self, event):
        self.mouse_enter_signal.emit(event)

    def leaveEvent(self, event):
        self.mouse_leave_signal.emit()


class ViewerPictureLabel(QLabel):
    mouse_left_click_signal = Signal(object)
    mouse_right_click_signal = Signal(object)
    mouse_painter_signal = Signal(int, int, int, int)

    def __init__(self):
        super(ViewerPictureLabel, self).__init__()

        self.pen = QPen()
        self.pen.setColor(Qt.gray)
        self.pen.setWidth(1)
        self.pen.setStyle(Qt.DashLine)

        self.current_rect = QRect()
        self.mouse_begin_position = None
        self.mouse_left_pressed = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_left_click_signal.emit(event)

        if event.button() == Qt.LeftButton:
            self.mouse_left_pressed = True
            self.mouse_begin_position = event.pos()

    def mouseMoveEvent(self, event):
        if self.mouse_left_pressed:
            begin_x, begin_y = self.mouse_begin_position.x(), self.mouse_begin_position.y()
            current_x, current_y = event.pos().x(), event.pos().y()
            width, height = current_x - begin_x, current_y - begin_y
            self.current_rect = QRect(begin_x, begin_y, width, height)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_right_click_signal.emit(event)

        if event.button() == Qt.LeftButton:
            if self.current_rect:
                width = abs(self.current_rect.width())
                height = abs(self.current_rect.height())

                if self.current_rect.width() > 0:
                    begin_x = self.current_rect.x()
                else:
                    begin_x = self.current_rect.x() + self.current_rect.width()

                if self.current_rect.height() > 0:
                    begin_y = self.current_rect.y()
                else:
                    begin_y = self.current_rect.y() + self.current_rect.height()

                if width > 1 and height > 1:
                    self.mouse_painter_signal.emit(width, height, begin_x, begin_y)

            self.current_rect = QRect()
            self.mouse_left_pressed = False

    def paintEvent(self, event):
        super(ViewerPictureLabel, self).paintEvent(event)
        if self.mouse_left_pressed:
            painter = QPainter(self)
            painter.setPen(self.pen)
            painter.drawRect(self.current_rect)


class SaveAs(QObject):
    save_as_result_signal = Signal()

    def __init__(self, img_path, target_path, resize_option, img_quality):
        super(SaveAs, self).__init__()
        self.imagemagick_handler = ImageMagickHandler()

        thread = Thread(target=self.save_as, args=(img_path, target_path, resize_option, img_quality))
        thread.daemon = True
        thread.start()

    def save_as(self, src_path, target_path, resize_option, img_quality):
        imagemagick_program_status, imagemagick_program_path = \
            self.imagemagick_handler.check_imagemagick_available()
        if imagemagick_program_status:
            save_as_result = self.imagemagick_handler.convert_picture(src_path, target_path, resize_option, img_quality)

            if save_as_result:
                self.save_as_result_signal.emit()


class ExportPDF(QObject):
    export_pdf_result_signal = Signal()

    def __init__(self, file_with_resolution_list, target_path, page_size_value, page_layout_value,
                 background_colour_value, density_value, img_quality_value):
        super(ExportPDF, self).__init__()
        self.imagemagick_handler = ImageMagickHandler()

        thread = Thread(target=self.export_pdf, args=(file_with_resolution_list, target_path, page_size_value,
                                                      page_layout_value, background_colour_value, density_value,
                                                      img_quality_value))
        thread.daemon = True
        thread.start()

    def export_pdf(self, file_with_resolution_list, target_path, page_size_value, page_layout_value,
                   background_colour_value, density_value, img_quality_value):
        imagemagick_program_status, imagemagick_program_path = \
            self.imagemagick_handler.check_imagemagick_available()

        if imagemagick_program_status:
            export_pdf_result = self.imagemagick_handler.create_pdf(file_with_resolution_list,
                                                                                target_path, page_size_value,
                                                                                page_layout_value,
                                                                                background_colour_value,
                                                                                density_value, img_quality_value)
            if export_pdf_result:
                self.export_pdf_result_signal.emit()



class ImageMagickClip(QObject):
    clip_result_signal = Signal(str)

    def __init__(self, src_path, target_path, resize_option, width, height, begin_x, begin_y):
        super(ImageMagickClip, self).__init__()
        self.imagemagick_handler = ImageMagickHandler()

        thread = Thread(
            target=self.imagemagick_clip, args=(src_path, target_path, resize_option, width, height, begin_x, begin_y)
        )
        thread.daemon = True
        thread.start()

    def imagemagick_clip(self, src_path, target_path, resize_option, width, height, begin_x, begin_y):
        convert_result = self.imagemagick_handler.convert_picture(src_path, target_path, resize_option, '')
        if convert_result:
            clip_result = self.imagemagick_handler.clip_picture(
                target_path, target_path, width, height, begin_x, begin_y
            )
            if clip_result:
                self.clip_result_signal.emit(target_path)


class OpenFolder(QObject):
    scan_result_signal = Signal(int)
    open_folder_signal = Signal()

    def __init__(self, folder_path):
        super(OpenFolder, self).__init__()

        thread = Thread(target=self.scan_folder, args=(folder_path,))
        thread.daemon = True
        thread.start()

    def scan_folder(self, folder_path):
        scanned_files_number_signal = queue_Queue()
        cache_status_signal = queue_Queue()
        pictures_changes_signal = queue_Queue()
        cached_progress_signal = queue_Queue()
        cached_files_number_signal = queue_Queue()

        handle_pictures_changes = HandlePicturesChanges()
        handle_pictures_changes.start(
            folder_path, scanned_files_number_signal,
            cache_status_signal, pictures_changes_signal,
            cached_progress_signal, cached_files_number_signal)

        scanned_files_number = scanned_files_number_signal.get()
        self.scan_result_signal.emit(scanned_files_number)

        cache_status = cache_status_signal.get()

        if cache_status == 'None':
            self.open_folder_signal.emit()
        elif cache_status == 'Need':
            cached_files_number = cached_files_number_signal.get()
            self.open_folder_signal.emit()


class ReadSubdirectories(QObject):
    subdirectories_dict_signal = Signal(dict)
    subdirectories_signal = Signal(list)

    def __init__(self, folder_path):
        super(ReadSubdirectories, self).__init__()
        self.commands = Commands()
        self.subdirectories_dict = dict()

        thread = Thread(target=self.scan_subdirectories_thread, args=(folder_path,))
        thread.daemon = True
        thread.start()

    def scan_subdirectories_thread(self, folder_path):
        filetypes = self.commands.read_supported_formats()
        threads_number = int(self.commands.read_cache_threads_number())
        images_included_subdirectories_signal = queue_Queue()

        multiprocessing_folder_scan = MultiprocessingFolderScan()
        multiprocessing_folder_scan.prepare(
            folder_path, filetypes, threads_number, '', images_included_subdirectories_signal
        )

        images_included_subdirectories_path_list = images_included_subdirectories_signal.get()

        images_included_subdirectories_name_list = list()
        for subdirectory_path in images_included_subdirectories_path_list:
            subdirectory_name = os.path.basename(subdirectory_path)
            images_included_subdirectories_name_list.append(subdirectory_name)

        self.subdirectories_dict = dict(
            zip(images_included_subdirectories_name_list, images_included_subdirectories_path_list)
        )
        images_included_subdirectories_name_list.sort()

        self.subdirectories_dict_signal.emit(self.subdirectories_dict)
        self.subdirectories_signal.emit(images_included_subdirectories_name_list)


class ImportImages(QObject):
    imported_number_signal = Signal(int, int)
    import_finish_signal = Signal(int, str)

    def __init__(self, folder_path):
        super(ImportImages, self).__init__()

        self.commands = Commands()
        self.imagemagick_handler = ImageMagickHandler()
        self.pictures_folder_path = self.commands.read_pictures_folder_path()

        thread = Thread(target=self.scan_folder_thread, args=(folder_path,))
        thread.daemon = True
        thread.start()

    def scan_folder_thread(self, folder_path):
        scanned_files_number_signal = queue_Queue()

        handle_pictures_changes = HandlePicturesChanges()
        handle_pictures_changes.start(folder_path, scanned_files_number_signal, '', '', '', '')

        scan_result = scanned_files_number_signal.get()
        scanned_files_list = scan_result[0]
        scanned_files_number = scan_result[1]

        imported_number = 0

        for image in scanned_files_list:
            image_creation_time = self.imagemagick_handler.read_exif_creation_time(image)
            image_creation_time = image_creation_time.split(' ')
            image_creation_date = image_creation_time[0]
            image_creation_date_folder = os.path.join(self.pictures_folder_path, image_creation_date)
            if not os.path.exists(image_creation_date_folder) or not os.path.isdir(image_creation_date_folder):
                os.mkdir(image_creation_date_folder)

            import_image_path = os.path.join(image_creation_date_folder, os.path.basename(image))
            if not os.path.exists(import_image_path):
                shutil.copyfile(image, import_image_path)
                imported_number = imported_number + 1
                self.imported_number_signal.emit(scanned_files_number, imported_number)
            else:
                image_md5 = self.commands.read_md5(image)
                exist_image_md5 = self.commands.read_md5(import_image_path)
                if image_md5 != exist_image_md5:
                    file_basename = self.commands.create_duplicate_name(
                        os.path.basename(image), image_creation_date_folder
                    )
                    import_image_path = os.path.join(image_creation_date_folder, file_basename)
                    shutil.copyfile(image, import_image_path)
                    imported_number = imported_number + 1
                    self.imported_number_signal.emit(scanned_files_number, imported_number)

        self.import_finish_signal.emit(imported_number, 'Done')


class SettingsScanFolder(QObject):
    scan_result_signal = Signal(int)
    nochange_signal = Signal()
    pictures_changes_result_signal = Signal(int, int, int)
    cachepictures_progress_signal = Signal(str, int)
    cachepictures_result_signal = Signal(int)

    def __init__(self, folder_path):
        super(SettingsScanFolder, self).__init__()
        thread = Thread(target=self.scan_folder_thread, args=(folder_path,))
        thread.daemon = True
        thread.start()

    def scan_folder_thread(self, folder_path):
        scanned_files_number_signal = queue_Queue()
        cache_status_signal = queue_Queue()
        pictures_changes_signal = queue_Queue()
        cached_progress_signal = queue_Queue()
        cached_files_number_signal = queue_Queue()

        handle_pictures_changes = HandlePicturesChanges()
        handle_pictures_changes.start(
            folder_path, scanned_files_number_signal,
            cache_status_signal, pictures_changes_signal,
            cached_progress_signal, cached_files_number_signal
        )

        scanned_files_number = scanned_files_number_signal.get()
        self.scan_result_signal.emit(scanned_files_number)

        cache_status = cache_status_signal.get()

        if cache_status == 'None':
            pictures_changes = pictures_changes_signal.get()
            if pictures_changes == 'No change':
                self.nochange_signal.emit()
            else:
                removed_number = pictures_changes[0]
                moved_number = pictures_changes[1]
                added_number = pictures_changes[2]
                self.pictures_changes_result_signal.emit(removed_number, moved_number, added_number)

        if cache_status == 'Need':
            while True:
                cached_progress_list = cached_progress_signal.get()
                if cached_progress_list == 'stopped':
                    break

                img_path = cached_progress_list[0]
                handled_percents = cached_progress_list[1]
                self.cachepictures_progress_signal.emit(img_path, handled_percents)
                if handled_percents == 100:
                    break

            cached_files_number = cached_files_number_signal.get()
            self.cachepictures_result_signal.emit(cached_files_number)

            pictures_changes = pictures_changes_signal.get()
            removed_number = pictures_changes[0]
            moved_number = pictures_changes[1]
            added_number = pictures_changes[2]
            self.pictures_changes_result_signal.emit(removed_number, moved_number, added_number)


class CleanDatabaseAndCache(QObject):
    clean_database_and_cache_result_signal = Signal(int, int, int, int)

    def __init__(self):
        super(CleanDatabaseAndCache, self).__init__()

        thread = Thread(target=self.clean_database_and_cache_thread)
        thread.daemon = True
        thread.start()

    def clean_database_and_cache_thread(self):
        removed_records_number_signal = queue_Queue()
        removed_files_number_signal = queue_Queue()
        database_records_number_signal = queue_Queue()
        cache_folder_files_number_signal = queue_Queue()

        tools = Tools()
        tools.clean_database_and_cache(
            removed_records_number_signal, removed_files_number_signal,
            database_records_number_signal, cache_folder_files_number_signal
        )
        removed_records_number = removed_records_number_signal.get()
        removed_files_number = removed_files_number_signal.get()
        database_records_number = database_records_number_signal.get()
        cache_folder_files_number = cache_folder_files_number_signal.get()

        self.clean_database_and_cache_result_signal.emit(removed_records_number, removed_files_number,
                                                         database_records_number, cache_folder_files_number)


class Tools:
    def __init__(self):
        super(Tools, self).__init__()
        self.commands = Commands()

        self.cache_folder_path = self.commands.read_cache_folder_path()

    def clean_database_and_cache(
            self,
            removed_records_number_signal, removed_files_number_signal,
            database_records_number_signal, cache_folder_files_number_signal
    ):
        pictures_folder_path = self.commands.read_pictures_folder_path()
        pictures_path_data, _, _, _ = self.commands.read_pictures_data()

        removed_records_list = list()
        for picture_path in pictures_path_data:
            picture_record = self.commands.read_picture_record(picture_path)
            if len(picture_record) > 1:
                del picture_record[0]
                for record in picture_record:
                    picture_id = record[0]
                    self.commands.remove_picture_id_record(picture_id)
                    removed_records_list.append(record)

        for picture_path in pictures_path_data:
            if pictures_folder_path not in picture_path:
                self.commands.remove_picture_record(picture_path)
                removed_records_list.append(picture_path)

        removed_records_number = len(removed_records_list)

        _, _, _, pictures_cached_name_data = self.commands.read_pictures_data()

        pictures_cached_path_list = list()
        for picture_cached_name in pictures_cached_name_data:
            if picture_cached_name:
                picture_cached_path = os.path.join(self.cache_folder_path, picture_cached_name)
                pictures_cached_path_list.append(picture_cached_path)

        removed_files_list = list()
        with os.scandir(self.cache_folder_path) as cache:
            for item in cache:
                item_path = item.path
                if os.path.isfile(item_path):
                    if item_path not in pictures_cached_path_list:
                        os.remove(item_path)
                        removed_files_list.append(item_path)

        removed_files_number = len(removed_files_list)

        self.commands.database_vacuum()

        pictures_path_data, _, _, _ = self.commands.read_pictures_data()
        database_records_number = len(pictures_path_data)

        cache_folder_files_list = list()
        with os.scandir(self.cache_folder_path) as cache:
            for item in cache:
                item_path = item.path
                if os.path.isfile(item_path):
                    cache_folder_files_list.append(item_path)

        cache_folder_files_number = len(cache_folder_files_list)

        removed_records_number_signal.put(removed_records_number)
        removed_files_number_signal.put(removed_files_number)
        database_records_number_signal.put(database_records_number)
        cache_folder_files_number_signal.put(cache_folder_files_number)
