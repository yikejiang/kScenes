import os
import sys
import hashlib
import shutil
import random
import string
import subprocess

from ksdatabase import BasicConfig, Database


class Commands:
    def __init__(self):
        super(Commands, self).__init__()
        self.basic_config = BasicConfig()
        self.database = Database()

    @staticmethod
    def get_app_folder_path():
        app_folder_path = os.path.dirname(sys.argv[0])
        return app_folder_path

    def get_app_parameter(self):
        app_parameter_image = str()
        app_parameter_info = str()

        if len(sys.argv) > 1:
            app_parameter_image = sys.argv[1]
            file_type = self.get_filetype(app_parameter_image)
            supported_formats = self.read_supported_formats()
            if file_type in supported_formats and os.path.exists(app_parameter_image):
                app_parameter_info = ''
            elif not os.path.exists(app_parameter_image):
                app_parameter_info = 'Not found'
            else:
                app_parameter_info = 'No support'

        return app_parameter_image, app_parameter_info

    @staticmethod
    def read_md5(file):
        with open(file, 'rb') as cache:
            md5_check = hashlib.md5()
            md5_check.update(cache.read())
            file_md5 = md5_check.hexdigest()
        return file_md5

    @staticmethod
    def create_random_name(prefix_name):
        random_name = string.ascii_letters + string.digits
        random_name = random.sample(random_name, 6)
        random_name = ''.join(random_name)
        random_name = f'{prefix_name}{random_name}'
        return random_name

    @staticmethod
    def create_duplicate_name(file_basename, folder_path):
        item_list = list()

        with os.scandir(folder_path) as temp:
            for item in temp:
                item_path = item.path
                item_basename = os.path.basename(item_path)
                item_list.append(item_basename)

        while True:
            if file_basename in item_list:
                file_basename = file_basename.split('.')
                file_basename = f'{file_basename[0]} (1).{file_basename[1]}'
            else:
                break

        return file_basename

    @staticmethod
    def get_filetype(file_path):
        basename = os.path.basename(file_path)
        if '.' not in basename:
            filetype = 'unknown'
        else:
            basename = basename.split('.')
            filetype = f'.{basename[-1]}'
        return filetype

    @staticmethod
    def get_filename(file_path):
        file_name_with_type = os.path.basename(file_path)
        file_name_with_type = file_name_with_type.split('.')
        file_name = file_name_with_type[0]
        return file_name

    @staticmethod
    def change_pathname(src_path):
        basename = os.path.basename(src_path)
        if os.path.isfile(src_path) and '.' in basename:
            temp = basename.split('.')
            changed = f'{temp[-2]}(1)'
            temp[-2] = changed
            basename = '.'.join(temp)
        else:
            basename = f'{basename}(1)'

        dirname = os.path.dirname(src_path)
        dst_path = os.path.join(dirname, basename)
        return dst_path

    @staticmethod
    def read_supported_formats():
        imagemagick_program_status, imagemagick_program_path = \
            ImageMagickHandler().check_imagemagick_available()

        if imagemagick_program_status:
            supported_formats = [
                '.bmp', '.BMP',
                '.gif', '.GIF',
                '.jpeg', '.JPEG',
                '.jpg', '.JPG',
                '.png', '.PNG',
                '.heic', '.HEIC',
                '.webp', '.WEBP',
                '.tiff', '.TIFF',
                '.tif', '.TIF',
                '.dds', '.DDS',
                '.dcm', '.DCM',
                '.xcf', '.XCF'
            ]
        else:
            supported_formats = [
                '.bmp', '.BMP',
                '.gif', '.GIF',
                '.jpeg', '.JPEG',
                '.jpg', '.JPG',
                '.png', '.PNG'
            ]

        return supported_formats

    @staticmethod
    def imagemagick_supported_formats():
        formats = [
            '.heic', '.HEIC',
            '.dcm', '.DCM',
            '.xcf', '.XCF',
            '.webp', '.WEBP',
            '.dds', '.DDS',
            '.tiff', '.TIFF',
            '.tif', '.TIF',
            'unknown'
        ]
        return formats

    @staticmethod
    def read_http_headers():
        http_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'
        }
        return http_headers

    @staticmethod
    def get_printable_page_resolution(page_size, density):
        if page_size == 'a4' and density == '72':
            page_width = '595'
            page_height = '842'
        elif page_size == 'a4' and density == '96':
            page_width = '794'
            page_height = '1123'
        elif page_size == 'a4' and density == '150':
            page_width = '1240'
            page_height = '1754'
        elif page_size == 'a4' and density == '300':
            page_width = '2480'
            page_height = '3508'
        else:
            page_width = ''
            page_height = ''

        return page_width, page_height

    def get_logo_path(self):
        app_folder_path = self.get_app_folder_path()
        logo_path = os.path.join(app_folder_path, 'logo.ico')
        return logo_path

    def read_pictures_folder_path(self):
        pictures_folder_path = self.database.read_setting('pictures_folder_path')
        if not os.path.exists(pictures_folder_path) and os.path.exists(self.basic_config.read_system_pictures_folder_path()):
                pictures_folder_path = self.basic_config.read_system_pictures_folder_path()
                self.save_pictures_folder_path(pictures_folder_path)

        return pictures_folder_path

    def save_pictures_folder_path(self, pictures_folder_path):
        self.database.save_setting('pictures_folder_path', pictures_folder_path)

    def read_cache_threads_number(self):
        default_threads_number = int(os.cpu_count() / 2)
        if default_threads_number == 0:
            default_threads_number = 1
        cache_threads_number = self.database.read_setting('cache_threads_number')
        if not cache_threads_number:
            cache_threads_number = default_threads_number
        return cache_threads_number

    def save_cache_threads_number(self, cache_threads_number):
        self.database.save_setting('cache_threads_number', cache_threads_number)

    def read_latest_geometry(self):
        latest_geometry = self.database.read_setting('latest_geometry')
        return latest_geometry

    def save_latest_geometry(self, latest_geometry):
        self.database.save_setting('latest_geometry', latest_geometry)

    def read_zoomed_size(self):
        zoomed_size = self.database.read_setting('zoomed_size')
        return zoomed_size

    def save_zoomed_size(self, zoomed_size):
        self.database.save_setting('zoomed_size', zoomed_size)

    def read_temp_folder_path(self):
        profile_folder_path = self.basic_config.read_profile_folder_path()
        temp_folder_path = os.path.join(profile_folder_path, 'temp')
        if os.path.exists(temp_folder_path) is False:
            os.mkdir(temp_folder_path)
        return temp_folder_path

    def remove_temp_folder(self):
        temp_folder_path = self.read_temp_folder_path()
        if os.path.exists(temp_folder_path):
            shutil.rmtree(temp_folder_path)
            return True
        else:
            return False

    def read_cache_folder_path(self):
        profile_folder_path = self.basic_config.read_profile_folder_path()
        cache_folder_path = os.path.join(profile_folder_path, 'cache')
        if os.path.exists(cache_folder_path) is False:
            os.mkdir(cache_folder_path)
        return cache_folder_path

    def add_picture_record(self, picture_path, picture_md5, creation_time):
        self.database.pictures_insert_record(picture_path, picture_md5, creation_time)

    def read_latest_pictures_data(self):
        pictures_data = self.database.read_latest_pictures_data()
        if pictures_data:
            pictures_data = list(zip(*pictures_data))
            pictures_path_data = pictures_data[1]
            pictures_md5_data = pictures_data[2]
            pictures_creation_time_data = pictures_data[3]
            pictures_cached_name_data = pictures_data[4]
        else:
            pictures_path_data = []
            pictures_md5_data = []
            pictures_creation_time_data = []
            pictures_cached_name_data = []
        return pictures_path_data, pictures_md5_data, pictures_creation_time_data, pictures_cached_name_data

    def read_pictures_data(self):
        pictures_data = self.database.read_pictures_data()
        if pictures_data:
            pictures_data = list(zip(*pictures_data))
            pictures_path_data = pictures_data[1]
            pictures_md5_data = pictures_data[2]
            pictures_creation_time_data = pictures_data[3]
            pictures_cached_name_data = pictures_data[4]
        else:
            pictures_path_data = []
            pictures_md5_data = []
            pictures_creation_time_data = []
            pictures_cached_name_data = []
        return pictures_path_data, pictures_md5_data, pictures_creation_time_data, pictures_cached_name_data

    def read_picture_record(self, picture_path):
        picture_record = self.database.pictures_read_record('picture_path', picture_path)
        return picture_record

    def read_picture_md5(self, picture_path):
        picture_record = self.database.pictures_read_record('picture_path', picture_path)
        picture_record = list(picture_record[0])
        picture_md5 = picture_record[2]
        return picture_md5

    def read_picture_creation_time(self, picture_path):
        picture_record = self.database.pictures_read_record('picture_path', picture_path)
        picture_record = list(picture_record[0])
        picture_creation_time = picture_record[3]
        return picture_creation_time

    def read_picture_cached_path(self, picture_path):
        picture_record = self.database.pictures_read_record('picture_path', picture_path)
        if not picture_record:
            picture_cached_path = ''
        else:
            picture_record = list(picture_record[0])
            picture_cached_name = picture_record[4]
            cache_folder_path = self.read_cache_folder_path()
            picture_cached_path = os.path.join(cache_folder_path, picture_cached_name)
        return picture_cached_path

    def save_picture_path(self, img_md5, img_path):
        self.database.pictures_update_record('picture_md5', img_md5, 'picture_path', img_path)

    def save_picture_md5(self, img_path, img_md5):
        self.database.pictures_update_record('picture_path', img_path, 'picture_md5', img_md5)

    def save_picture_cached_path(self, img_path, img_cache_name):
        self.database.pictures_update_record('picture_path', img_path, 'cached_name', img_cache_name)

    def remove_picture_record(self, picture_path):
        self.database.pictures_delete_record('picture_path', picture_path)

    def remove_picture_id_record(self, picture_id):
        self.database.pictures_delete_record('id', picture_id)

    def database_vacuum(self):
        self.database.database_vacuum()

    def check_reserved_cache_files(self):
        cache_folder_path = self.read_cache_folder_path()
        pictures_path_data, _, _, pictures_cached_name_data = self.read_latest_pictures_data()

        reserved_cache_files_list = list()
        n = 0

        for picture_cached_name in pictures_cached_name_data:
            picture_path = pictures_path_data[n]

            if os.path.exists(picture_path):
                picture_cached_path = os.path.join(cache_folder_path, picture_cached_name)
                reserved_cache_files_list.append(picture_cached_path)

            n = n + 1

        return reserved_cache_files_list


class ImageMagickHandler:
    def __init__(self):
        super(ImageMagickHandler, self).__init__()
        self.commands = Commands()

    def read_imagemagick_folder_path(self):
        if os.name == 'nt':
            app_folder_path = self.commands.get_app_folder_path()
            imagemagick_folder_path = os.path.join(app_folder_path, 'ImageMagick')
        elif sys.platform == 'darwin':
            imagemagick_folder_path = '/opt/local/bin'
        else:
            imagemagick_folder_path = '/usr/bin'
        return imagemagick_folder_path

    def check_imagemagick_available(self):
        imagemagick_folder_path = self.read_imagemagick_folder_path()
        if os.name == 'nt':
            imagemagick_program_path = os.path.join(imagemagick_folder_path, 'magick.exe')
        elif sys.platform == 'darwin' or sys.platform == 'linux':
            imagemagick_program_path = os.path.join(imagemagick_folder_path, 'convert')
        else:
            imagemagick_program_path = os.path.join(imagemagick_folder_path, 'magick')

        if not os.path.exists(imagemagick_program_path):
            return False, imagemagick_program_path
        else:
            return True, imagemagick_program_path

    @staticmethod
    def hide_console_status():
        if os.name == 'nt':
            hide_console = subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW)
        else:
            hide_console = None
        return hide_console

    def read_exif(self, img_path):
        _, imagemagick_program_path = self.check_imagemagick_available()

        if sys.platform == 'darwin' or sys.platform == 'linux':
            imagemagick_folder_path = self.read_imagemagick_folder_path()
            imagemagick_identify_path = os.path.join(imagemagick_folder_path, 'identify')
            commands = f'{imagemagick_identify_path},-format,%[date:*]%[exif:*],{img_path}'
        else:
            commands = f'{imagemagick_program_path},identify,-format,%[date:*]%[exif:*],{img_path}'

        commands = commands.split(',')

        hide_console = self.hide_console_status()
        identify_process = subprocess.Popen(commands, stdout=subprocess.PIPE, startupinfo=hide_console)
        exif_info = identify_process.stdout.readlines()

        identify_process.communicate()

        exif_details = dict()
        for item in exif_info:
            item = item.decode('utf-8')
            item = item.strip('\r\n')
            if item.startswith('exif:thumbnail:'):
                item = item[15:]
            elif item.startswith('date:') or item.startswith('exif:'):
                item = item[5:]

            item = item.split('=')
            if item[0] != 'MakerNote' and item[0] != 'PrintImageMatching':
                exif_details[item[0]] = item[1]

        return exif_details

    def read_exif_creation_time(self, img_path):
        _, imagemagick_program_path = self.check_imagemagick_available()

        if sys.platform == 'darwin' or sys.platform == 'linux':
            imagemagick_folder_path = self.read_imagemagick_folder_path()
            imagemagick_identify_path = os.path.join(imagemagick_folder_path, 'identify')
            commands = f'{imagemagick_identify_path},-format,%[date:*]%[exif:*],{img_path}'
        else:
            commands = f'{imagemagick_program_path},identify,-format,%[date:*]%[exif:*],{img_path}'

        commands = commands.split(',')

        hide_console = self.hide_console_status()
        identify_process = subprocess.Popen(commands, stdout=subprocess.PIPE, startupinfo=hide_console)
        exif_info = identify_process.stdout.readlines()
        creation_time = str()
        for line in exif_info:
            line = line.decode('utf-8')
            if 'DateTimeOriginal' in line:
                line = line.strip('\r\n')
                line = line.split('=')
                creation_time = line[1]
                creation_time = creation_time.split(' ')
                creation_ymd = creation_time[0]
                creation_hms = creation_time[1]
                creation_ymd = creation_ymd.split(':')
                creation_ymd = f'{creation_ymd[0]}-{creation_ymd[1]}-{creation_ymd[2]}'
                creation_time = f'{creation_ymd} {creation_hms}'
            else:
                if 'date:create' in line:
                    line = line.strip('\r\n')
                    line = line.split('=')
                    creation_time = line[1]
                    if '+' in creation_time:
                        creation_time = creation_time.split('+')
                        creation_time = creation_time[0]
                        if 'T' in creation_time:
                            creation_time = creation_time.split('T')
                            creation_time = f'{creation_time[0]} {creation_time[1]}'

        identify_process.communicate()

        return creation_time

    def convert_picture(self, img_path, target_path, resize_option, img_quality):
        _, imagemagick_program_path = self.check_imagemagick_available()

        rotation_option = '-auto-orient'

        if not resize_option:
            resize_parameter = ''
        else:
            resize_parameter = f',-resize,{resize_option}'

        target_filetype = self.commands.get_filetype(target_path)
        if not img_quality:
            img_quality_parameter = ''
        else:
            if target_filetype == '.webp':
                img_quality_parameter = f',-quality,{img_quality},-define,webp:lossless=false'
            else:
                img_quality_parameter = f',-quality,{img_quality}'

        commands = f'{imagemagick_program_path},{img_path},{rotation_option}{resize_parameter}{img_quality_parameter},{target_path}'
        commands = commands.split(',')
        hide_console = self.hide_console_status()
        convert_process = subprocess.Popen(commands, startupinfo=hide_console)
        convert_process.communicate()

        if convert_process.returncode == 0:
            return True
        else:
            return False

    def clip_picture(self, img_path, target_path, width, height, begin_x, begin_y):
        _, imagemagick_program_path = self.check_imagemagick_available()

        rotation_option = '-auto-orient'

        crop_option = f',-crop,{width}x{height}+{begin_x}+{begin_y}'

        commands = f'{imagemagick_program_path},{img_path},{rotation_option}{crop_option},{target_path}'
        commands = commands.split(',')
        hide_console = self.hide_console_status()
        clip_process = subprocess.Popen(commands, startupinfo=hide_console)
        clip_process.communicate()

        if clip_process.returncode == 0:
            return True
        else:
            return False

    def convert_bulk_files(self, target_folder_path, file_list, file_format, resize_option, img_quality):
        for file in file_list:
            file_name = self.commands.get_filename(file)
            file_name_with_type = f'{file_name}.{file_format}'
            target_file_path = os.path.join(target_folder_path, file_name_with_type)

            convert_file = self.convert_picture(file, target_file_path, resize_option, img_quality)

            if convert_file:
                return file, True
            else:
                return file, False

    def create_specific_page_image(self, img_path, page_size, background_colour, density):
        _, imagemagick_program_path = self.check_imagemagick_available()

        temp_folder_path = self.commands.read_temp_folder_path()
        pdf_temp_folder_path = os.path.join(temp_folder_path, 'pdf_temp')
        if os.path.exists(pdf_temp_folder_path) is False:
            os.mkdir(pdf_temp_folder_path)

        page_width, page_height = self.commands.get_printable_page_resolution(page_size, density)

        if page_width:
            size_parameter = f',-size,{page_width}x{page_height}'
        else:
            size_parameter = ''

        if not background_colour:
            background_parameter = ''
        else:
            background_parameter = f',canvas:{background_colour}'

        if not density:
            density_parameter = ''
        else:
            density_parameter = f',-density,{density}'

        file_name = self.commands.get_filename(img_path)
        temp_page_img_path = os.path.join(pdf_temp_folder_path, f'{file_name}_page.jpg')

        commands = f'{imagemagick_program_path}{size_parameter}{density_parameter}{background_parameter},-quality,100,{temp_page_img_path}'
        commands = commands.split(',')
        hide_console = self.hide_console_status()
        convert_process = subprocess.Popen(commands, startupinfo=hide_console)
        convert_process.communicate()

        if convert_process.returncode == 0:
            return temp_page_img_path, page_width
        else:
            return False

    def insert_image_to_page(self, img_path, img_original_resolution, page_size, layout, background_colour, density):
        _, imagemagick_program_path = self.check_imagemagick_available()

        temp_folder_path = self.commands.read_temp_folder_path()
        pdf_temp_folder_path = os.path.join(temp_folder_path, 'pdf_temp')
        if os.path.exists(pdf_temp_folder_path) is False:
            os.mkdir(pdf_temp_folder_path)

        if not density:
            density_parameter = ''
        else:
            density_parameter = f',-density,{density}'

        if layout == 'top':
            gravity_parameter = f',-gravity,North'
        elif layout == 'center':
            gravity_parameter = f',-gravity,Center'
        elif layout == 'bottom':
            gravity_parameter = f',-gravity,South'
        else:
            gravity_parameter = ''

        file_name = self.commands.get_filename(img_path)
        temp_img_path = os.path.join(pdf_temp_folder_path, f'{file_name}_temp.jpg')
        temp_page_path = os.path.join(pdf_temp_folder_path, f'{file_name}_on_a_page.jpg')

        specific_page_image_path, page_width = self.create_specific_page_image(img_path, page_size, background_colour, density)

        img_original_resolution = img_original_resolution.split('x')
        img_original_width = int(img_original_resolution[0])
        img_original_height = int(img_original_resolution[1])

        page_width, page_height = self.commands.get_printable_page_resolution(page_size, density)

        if page_height:
            temp_img_height = img_original_height / img_original_width * int(page_width)
            if temp_img_height > int(page_height):
                temp_img_width = img_original_width / img_original_height * int(page_height)
                create_temp_img = self.convert_picture(img_path, temp_img_path, temp_img_width, '100')
            else:
                create_temp_img = self.convert_picture(img_path, temp_img_path, page_width, '100')

            if create_temp_img:
                commands = (f'{imagemagick_program_path},composite,{temp_img_path},'
                            f'{specific_page_image_path}{gravity_parameter}{density_parameter},'
                            f'-colorspace,sRGB,{temp_page_path}')

                commands = commands.split(',')
                hide_console = self.hide_console_status()
                convert_process = subprocess.Popen(commands, startupinfo=hide_console)
                convert_process.communicate()

                if convert_process.returncode == 0:
                    return temp_page_path
                else:
                    return False
            else:
                return False

        else:
            create_temp_img = self.convert_picture(img_path, temp_img_path, '', '100')
            if create_temp_img:
                return temp_img_path
            else:
                return False

    def create_pdf(self, file_with_resolution_list, target_path, page_size, layout, background_colour, density, img_quality):
        _, imagemagick_program_path = self.check_imagemagick_available()

        temp_folder_path = self.commands.read_temp_folder_path()
        pdf_temp_folder_path = os.path.join(temp_folder_path, 'pdf_temp')
        if os.path.exists(pdf_temp_folder_path) is False:
            os.mkdir(pdf_temp_folder_path)

        img_path_list = list(zip(*file_with_resolution_list))[0]
        img_resolution_list = list(zip(*file_with_resolution_list))[1]

        temp_page_list = list()
        page_index = 0

        for img in img_path_list:
            img_original_resolution = img_resolution_list[page_index]

            temp_page_path = self.insert_image_to_page(img, img_original_resolution, page_size, layout,
                                                       background_colour, density)
            if temp_page_path:
                temp_page_list.append(temp_page_path)

            page_index = page_index + 1

        temp_pages = ','.join(temp_page_list)

        if page_size:
            if not density:
                density_parameter = ''
            else:
                density_parameter = f',-density,{density}'

            if not background_colour:
                background_parameter = ''
            else:
                background_parameter = f',-background,{background_colour}'

            page_parameter = f',-page,{page_size}'
        else:
            density_parameter = ''
            background_parameter = ''
            page_parameter = ''

        if img_quality:
            img_quality_parameter = f',-quality,{img_quality}'
        else:
            img_quality_parameter = ''

        commands = f'{imagemagick_program_path},{temp_pages}{density_parameter}{background_parameter}{page_parameter}{img_quality_parameter},{target_path}'

        commands = commands.split(',')
        hide_console = self.hide_console_status()
        convert_process = subprocess.Popen(commands, startupinfo=hide_console)
        convert_process.communicate()

        if convert_process.returncode == 0:
            if os.path.exists(pdf_temp_folder_path):
                shutil.rmtree(pdf_temp_folder_path)
            return True
        else:
            if os.path.exists(pdf_temp_folder_path):
                shutil.rmtree(pdf_temp_folder_path)
            return False