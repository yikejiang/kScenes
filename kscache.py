import os
from queue import Queue as queue_Queue
from threading import Thread
from multiprocessing import Process, Queue

from kshandler import Commands, ImageMagickHandler
from ksscan import MultiprocessingFolderScan


class SiftChanges:
    def __init__(self):
        super(SiftChanges, self).__init__()

    def start_read_database(
            self, top_folder, pictures_data_dict, pictures_path_data,
            database_list_signal, cache_folder_path, rebuild_cache_list_signal
    ):
        process = Process(
            target=self.read_database, args=(
                top_folder, pictures_data_dict, pictures_path_data,
                database_list_signal, cache_folder_path, rebuild_cache_list_signal
            )
        )
        process.daemon = True
        process.start()

    def start_check_non_existent_list(self, img_list, database_list, non_existent_list_signal):
        process = Process(
            target=self.check_non_existent_list, args=(img_list, database_list, non_existent_list_signal)
        )
        process.daemon = True
        process.start()

    def start_check_existent_list(self, img_list, database_list, existent_list_signal):
        process = Process(
            target=self.check_existent_list, args=(img_list, database_list, existent_list_signal)
        )
        process.daemon = True
        process.start()

    def read_database(
            self, top_folder, pictures_data_dict, pictures_path_data,
            database_list_signal, cache_folder_path, rebuild_cache_list_signal
    ):
        database_list = list()

        for picture_path in pictures_path_data:
            if top_folder in picture_path:
                database_list.append(picture_path)

        database_list_signal.put(database_list)

        self.check_cache_folder(pictures_data_dict, database_list, cache_folder_path, rebuild_cache_list_signal)

    @staticmethod
    def check_non_existent_list(img_list, database_list, non_existent_list_signal):
        non_existent_list = list()
        for item in database_list:
            if item not in img_list:
                non_existent_list.append(item)

        non_existent_list_signal.put(non_existent_list)

    @staticmethod
    def check_existent_list(img_list, database_list, existent_list_signal):
        existent_list = list()
        for item in img_list:
            if item not in database_list:
                existent_list.append(item)

        existent_list_signal.put(existent_list)

    @staticmethod
    def check_cache_folder(pictures_data_dict, database_list, cache_folder_path, rebuild_cache_list_signal):
        rebuild_cache_list = list()
        cache_file_name_list = list()
        with os.scandir(cache_folder_path) as temp:
            for item in temp:
                cache_file_name = item.name
                cache_file_name_list.append(cache_file_name)

        for picture_path in database_list:
            if pictures_data_dict[picture_path] not in cache_file_name_list:
                rebuild_cache_list.append(picture_path)

        rebuild_cache_list_signal.put(rebuild_cache_list)


class HandlePicturesChanges:
    def __init__(self):
        super(HandlePicturesChanges, self).__init__()
        self.commands = Commands()

        self.cache_folder_path = self.commands.read_cache_folder_path()

        self.non_existent_list = list()
        self.handled_img_list = list()
        self.cached_img_list = list()

        self.existent_list_number = int()
        self.handle_list_number = int()

        self.threads_number = int(self.commands.read_cache_threads_number())

        self.resize_option = str()

    def start(
            self,
            folder_path, scanned_files_number_signal,
            cache_status_signal, pictures_changes_signal,
            cached_progress_signal, cached_files_number_signal
    ):
        resize_option = 'x250'
        self.resize_option = resize_option

        thread = Thread(
            target=self.scan_folder, args=(
                folder_path, scanned_files_number_signal,
                cache_status_signal, pictures_changes_signal,
                cached_progress_signal, cached_files_number_signal
            )
        )
        thread.daemon = True
        thread.start()

    def scan_folder(
            self,
            folder_path, scanned_files_number_signal,
            cache_status_signal, pictures_changes_signal,
            cached_progress_signal, cached_files_number_signal
    ):
        filetypes = self.commands.read_supported_formats()
        scan_result_signal = queue_Queue()

        multiprocessing_folder_scan = MultiprocessingFolderScan()
        multiprocessing_folder_scan.prepare(
            folder_path, filetypes, self.threads_number, scan_result_signal, ''
        )

        database_list_signal = Queue()
        rebuild_cache_list_signal = Queue()
        pictures_path_data, _, _, pictures_cached_name_data = self.commands.read_pictures_data()

        pictures_data_dict = dict(zip(pictures_path_data, pictures_cached_name_data))

        sift_changes = SiftChanges()
        sift_changes.start_read_database(
            folder_path, pictures_data_dict, pictures_path_data,
            database_list_signal, self.cache_folder_path, rebuild_cache_list_signal
        )

        scan_result = scan_result_signal.get()

        if cache_status_signal == '' and pictures_changes_signal == '' and cached_progress_signal == '' \
                and cached_files_number_signal == '':
            scanned_files_number_signal.put(scan_result)
            return

        scanned_files_list = scan_result[0]
        scanned_files_number = scan_result[1]

        scanned_files_number_signal.put(scanned_files_number)

        database_list = database_list_signal.get()
        non_existent_list_signal = Queue()
        existent_list_signal = Queue()
        sift_changes.start_check_non_existent_list(scanned_files_list, database_list, non_existent_list_signal)
        sift_changes.start_check_existent_list(scanned_files_list, database_list, existent_list_signal)

        non_existent_list = non_existent_list_signal.get()
        existent_list = existent_list_signal.get()
        rebuild_cache_list = rebuild_cache_list_signal.get()

        if not non_existent_list and not existent_list and not rebuild_cache_list:
            cache_status_signal.put('None')
            pictures_changes_signal.put('No change')
        elif non_existent_list and not existent_list and not rebuild_cache_list:
            cache_status_signal.put('None')
            self.existent_list_number = 0
            self.non_existent_list = non_existent_list
            self.clean(pictures_changes_signal)
        else:
            cache_status_signal.put('Need')

            self.existent_list_number = len(existent_list)
            self.non_existent_list = non_existent_list

            temp_list = existent_list + rebuild_cache_list
            handle_list = list()
            for item in temp_list:
                if item not in handle_list:
                    handle_list.append(item)

            self.initialize_threads(
                handle_list, rebuild_cache_list,
                cached_progress_signal, cached_files_number_signal, pictures_changes_signal
            )

    def initialize_threads(
            self,
            handle_list, rebuild_cache_list,
            cached_progress_signal, cached_files_number_signal, pictures_changes_signal
    ):
        self.handle_list_number = len(handle_list)

        if self.handle_list_number < self.threads_number:
            self.threads_number = self.handle_list_number

        average_img_number = int(self.handle_list_number / self.threads_number)

        pending_list = dict()

        for n in range(self.threads_number):
            start = n * average_img_number
            stop = start + average_img_number

            if n == self.threads_number - 1:
                pending_list[n] = handle_list[start:]
            else:
                pending_list[n] = handle_list[start:stop]

        thread = dict()
        for n in range(self.threads_number):
            thread[n] = Thread(
                target=self.cache_thread, args=(
                    pending_list[n], rebuild_cache_list,
                    cached_progress_signal, cached_files_number_signal, pictures_changes_signal
                )
            )
            thread[n].daemon = True
            thread[n].start()

    def cache_thread(
            self,
            pending_list, rebuild_cache_list,
            cached_progress_signal, cached_files_number_signal, pictures_changes_signal
    ):
        cachepictures_progress_signal = queue_Queue()
        cachepictures_result_signal = queue_Queue()

        cachepictures_thread = CachePictures()

        cachepictures_thread.start_cache(
            pending_list, self.resize_option, rebuild_cache_list,
            cachepictures_progress_signal, cachepictures_result_signal
        )

        while True:
            img_path = cachepictures_progress_signal.get()
            if img_path == 'The list has been handled.':
                cached_pictures_list = cachepictures_result_signal.get()
                self.cache_result(
                    cached_pictures_list, cached_files_number_signal, pictures_changes_signal, cached_progress_signal
                )
                break
            else:
                self.cache_progress(img_path, cached_progress_signal)

    def cache_progress(self, img_path, cached_progress_signal):
        self.handled_img_list.append(img_path)
        handled_percents = int((len(self.handled_img_list) / self.handle_list_number) * 100)

        cached_progress_list = list()
        cached_progress_list.append(img_path)
        cached_progress_list.append(handled_percents)
        cached_progress_signal.put(cached_progress_list)

    def cache_result(
        self, cached_pictures_list, cached_files_number_signal, pictures_changes_signal, cached_progress_signal
    ):
        if len(self.cached_img_list) < self.threads_number:
            self.cached_img_list.append(cached_pictures_list)

        if len(self.cached_img_list) == self.threads_number:
            cached_img_list = sum(self.cached_img_list, [])
            cached_img_number = len(cached_img_list)

            cached_progress_signal.put('stopped')
            cached_files_number_signal.put(cached_img_number)

            self.clean(pictures_changes_signal)

    def clean(self, pictures_changes_signal):
        moved_list = list()
        removed_list = list()
        for item in self.non_existent_list:
            picture_cached_path = self.commands.read_picture_cached_path(item)
            if not picture_cached_path:
                moved_list.append(item)
            else:
                reserved_cache_files_list = self.commands.check_reserved_cache_files()

                if picture_cached_path not in reserved_cache_files_list:
                    if os.path.exists(picture_cached_path):
                        os.remove(picture_cached_path)

                removed_list.append(item)

                self.commands.remove_picture_record(item)

        removed_number = len(removed_list)
        moved_number = len(moved_list)
        added_number = self.existent_list_number - moved_number

        pictures_changes_list = list()
        pictures_changes_list.append(removed_number)
        pictures_changes_list.append(moved_number)
        pictures_changes_list.append(added_number)

        pictures_changes_signal.put(pictures_changes_list)


class CachePictures:
    def __init__(self):
        super(CachePictures, self).__init__()
        self.commands = Commands()
        self.imagemagick_handler = ImageMagickHandler()

        self.cache_folder_path = self.commands.read_cache_folder_path()

        self.temp_folder_path = self.commands.read_temp_folder_path()
        self.stop_caching_signal = os.path.join(self.temp_folder_path, 'stop_caching_signal')

    def start_cache(
            self,
            img_list, resize_option, rebuild_cache_list,
            cachepictures_progress_signal, cachepictures_result_signal
    ):
        thread = Thread(
            target=self.cache, args=(
                img_list, resize_option, rebuild_cache_list,
                cachepictures_progress_signal, cachepictures_result_signal
            )
        )
        thread.daemon = True
        thread.start()

    def cache(
            self,
            img_list, resize_option, rebuild_cache_list,
            cachepictures_progress_signal, cachepictures_result_signal):
        updated_pictures_path_list = list()
        updated_pictures_md5_list = list()
        added_pictures_list = list()
        cached_img_list = list()

        pictures_path_data, pictures_md5_data, _, _ = self.commands.read_pictures_data()

        for img_path in img_list:
            if os.path.exists(self.stop_caching_signal):
                break

            img_md5 = self.commands.read_md5(img_path)
            img_file_type = self.commands.get_filetype(img_path)
            imagemagick_supported_formats = self.commands.imagemagick_supported_formats()

            if img_path in pictures_path_data and img_md5 not in pictures_md5_data:
                # Need to update md5 and create cache
                self.commands.save_picture_md5(img_path, img_md5)
                updated_pictures_md5_list.append(img_path)
                img_status = 'Need to create cache'

            elif img_path not in pictures_path_data and img_md5 in pictures_md5_data:
                img_status = 'Need to add path'
                creation_time = self.imagemagick_handler.read_exif_creation_time(img_path)
                self.commands.add_picture_record(img_path, img_md5, creation_time)
                added_pictures_list.append(img_path)
                img_status = 'Need to create cache'

            elif img_path not in pictures_path_data and img_md5 not in pictures_md5_data:
                # Need to add record and create cache
                creation_time = self.imagemagick_handler.read_exif_creation_time(img_path)
                self.commands.add_picture_record(img_path, img_md5, creation_time)
                added_pictures_list.append(img_path)
                img_status = 'Need to create cache'

            else:
                img_status = 'No change'

            img_cache_name = f'{img_md5}.jpg'

            img_cache_path = os.path.join(self.cache_folder_path, img_cache_name)

            if img_status != 'Need to create cache' and img_path in rebuild_cache_list:
                img_status = 'Need to create cache'

            if img_status == 'Need to create cache':
                if not os.path.exists(img_cache_path):
                    img_cache_result = self.imagemagick_handler.convert_picture(
                        img_path, img_cache_path, resize_option, ''
                    )
                    if img_cache_result:
                        cached_img_list.append(img_path)

                self.commands.save_picture_cached_path(img_path, img_cache_name)

            cachepictures_progress_signal.put(img_path)

        cachepictures_progress_signal.put('The list has been handled.')
        cachepictures_result_signal.put(cached_img_list)
