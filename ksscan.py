import os
from threading import Thread
from queue import Queue as queue_Queue
from multiprocessing import Process, Queue


class MultiprocessingFolderScan:
    def __init__(self):
        super(MultiprocessingFolderScan, self).__init__()

    def prepare(
            self, folder_path, filetypes, threads_number,
            total_result_signal, images_included_subdirectories_signal
    ):
        subdirectories_path_list = list()
        other_files_list = list()

        with os.scandir(folder_path) as temp:
            for item in temp:
                item_path = item.path
                if os.path.isdir(item_path):
                    subdirectories_path_list.append(item_path)
                elif os.path.isfile(item_path):
                    other_files_list.append(item_path)

        thread = Thread(
            target=self.handle_folder,
            args=(
                subdirectories_path_list, other_files_list, threads_number, filetypes,
                total_result_signal, images_included_subdirectories_signal
            )
        )
        thread.daemon = True
        thread.start()

    def handle_folder(
            self,
            subdirectories_list, other_files_list, threads_number, filetypes,
            total_result_signal, images_included_subdirectories_signal
    ):
        scanned_files_list = list()
        subdirectories_list_number = len(subdirectories_list)

        if subdirectories_list_number == 0:
            if images_included_subdirectories_signal:
                images_included_subdirectories_signal.put([])

        if subdirectories_list_number > 0:
            if subdirectories_list_number < threads_number:
                threads_number = subdirectories_list_number

            average_subdirectories_number = int(subdirectories_list_number / threads_number)

            pending_folders_list = dict()

            for n in range(threads_number):
                start = n * average_subdirectories_number
                stop = start + average_subdirectories_number

                if n == threads_number - 1:
                    pending_folders_list[n] = subdirectories_list[start:]
                else:
                    pending_folders_list[n] = subdirectories_list[start:stop]

            process = dict()
            scan_result_signal = dict()
            images_included_folders_signal = dict()
            folders_scanned_files_list = dict()
            images_included_folders_list = dict()

            images_included_subdirectories_result = list()

            for n in range(threads_number):
                scan_result_signal[n] = Queue()
                images_included_folders_signal[n] = Queue()
                process[n] = Process(
                    target=self.scan_process,
                    args=(pending_folders_list[n], filetypes, scan_result_signal[n], images_included_folders_signal[n])
                )
                process[n].daemon = True
                process[n].start()

            for n in range(threads_number):
                folders_scanned_files_list[n] = scan_result_signal[n].get()
                scanned_files_list = scanned_files_list + folders_scanned_files_list[n]
                images_included_folders_list[n] = images_included_folders_signal[n].get()
                images_included_subdirectories_result = \
                    images_included_subdirectories_result + images_included_folders_list[n]

            if images_included_subdirectories_signal:
                images_included_subdirectories_signal.put(images_included_subdirectories_result)

        other_scanned_files_list = self.scan_other_files(other_files_list, filetypes)
        scanned_files_list = scanned_files_list + other_scanned_files_list
        scanned_files_number = len(scanned_files_list)
        scan_result = list()
        scan_result.append(scanned_files_list)
        scan_result.append(scanned_files_number)
        if total_result_signal:
            total_result_signal.put(scan_result)

    @staticmethod
    def scan_process(pending_folders_list_part, filetypes, scan_result_signal, images_included_folders_signal):
        folders_scanned_files_list = list()
        images_included_folders_list = list()
        for folder in pending_folders_list_part:
            folder_result_signal = queue_Queue()
            scan_folder = ScanFolder()
            scan_folder.start(folder, filetypes, folder_result_signal)
            folder_result = folder_result_signal.get()
            scanned_files_list = folder_result[1]
            folders_scanned_files_list = folders_scanned_files_list + scanned_files_list
            scanned_files_number = len(scanned_files_list)
            if scanned_files_number > 0:
                images_included_folders_list.append(folder)

        scan_result_signal.put(folders_scanned_files_list)
        images_included_folders_signal.put(images_included_folders_list)

    def scan_other_files(self, files_list, filetypes):
        scanned_files_list = list()
        for file_path in files_list:
            if filetypes:
                filetype = self.get_filetype(file_path)
                if filetype in filetypes:
                    scanned_files_list.append(file_path)
            else:
                scanned_files_list.append(file_path)

        return scanned_files_list

    @staticmethod
    def get_filetype(file_path):
        basename = os.path.basename(file_path)
        if '.' not in basename:
            filetype = 'unknown'
        else:
            basename = basename.split('.')
            filetype = f'.{basename[-1]}'
        return filetype


class ScanFolder:
    def __init__(self):
        super(ScanFolder, self).__init__()
        self.top_folder = str()
        self.items_list = list()
        self.scanned_folders_list = list()
        self.scanned_files_list = list()
        self.forbidden_folders_list = list()

    def start(self, folder, filetypes, folder_result_signal):
        self.top_folder = folder

        thread = Thread(target=self.scan, args=(folder, filetypes))
        thread.daemon = True
        thread.start()

        thread.join()

        scanfolder_result = list()
        scanfolder_result.append(self.top_folder)
        scanfolder_result.append(self.scanned_files_list)

        folder_result_signal.put(scanfolder_result)

        self.top_folder = ''
        self.items_list = []
        self.scanned_folders_list = []
        self.scanned_files_list = []
        self.forbidden_folders_list = []

    def scan(self, folder, filetypes):
        folder = os.path.normpath(folder)
        pending_scan_list = list()
        try:
            with os.scandir(folder) as temp:
                for item in temp:
                    item_path = item.path
                    item_path = os.path.normpath(item_path)
                    self.items_list.append(item_path)

                    if os.path.isfile(item_path):
                        if filetypes:
                            filetype = self.get_filetype(item_path)
                            if filetype in filetypes:
                                self.scanned_files_list.append(item_path)
                        else:
                            self.scanned_files_list.append(item_path)

                    elif os.path.isdir(item_path):
                        pending_scan_list.append(item_path)

        except PermissionError:
            self.forbidden_folders_list.append(folder)
        else:
            self.scanned_folders_list.append(folder)
        finally:
            for folder in pending_scan_list:
                self.scan(folder, filetypes)

    @staticmethod
    def get_filetype(file_path):
        basename = os.path.basename(file_path)
        if '.' not in basename:
            filetype = 'unknown'
        else:
            basename = basename.split('.')
            filetype = f'.{basename[-1]}'
        return filetype
