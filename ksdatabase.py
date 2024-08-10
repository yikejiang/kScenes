import os
import sys
import sqlite3


class BasicConfig:
    def __init__(self):
        super(BasicConfig, self).__init__()

    @staticmethod
    def read_profile_folder_path():
        if os.name == 'nt':
            profile_path = os.path.join(os.environ['LOCALAPPDATA'], 'kScenes')
        elif sys.platform == 'darwin':
            profile_path = os.path.join(os.environ['HOME'], '.kScenes')
        else:
            profile_path = os.path.join(os.environ['HOME'], '.config/kScenes')

        profile_path = os.path.normpath(profile_path)

        if os.path.exists(profile_path) is False:
            os.mkdir(profile_path)

        return profile_path

    @staticmethod
    def read_system_pictures_folder_path():
        if os.name == 'nt':
            default_pictures_path = os.path.join(os.environ['homedrive'], os.environ['homepath'], 'Pictures')
        else:
            default_pictures_path = os.path.join(os.environ['HOME'], 'Pictures')

        default_pictures_path = os.path.normpath(default_pictures_path)
        return default_pictures_path


class Database:
    def __init__(self):
        super(Database, self).__init__()

        self.basicconfig = BasicConfig()
        self.db = None
        self.db_cursor = None

        self.profile_folder_path = self.basicconfig.read_profile_folder_path()
        self.system_pictures_folder_path = self.basicconfig.read_system_pictures_folder_path()

        self.initialize_db()

    def initialize_db(self):
        self.open_db()

        self.db_cursor.execute(
            'CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY AUTOINCREMENT, item, value)'
        )
        self.initialize_setting('pictures_folder_path', self.system_pictures_folder_path)
        self.initialize_setting('latest_geometry', '')
        self.initialize_setting('zoomed_size', '')
        self.initialize_setting('cache_threads_number', '')

        self.db_cursor.execute(
            'CREATE TABLE IF NOT EXISTS pictures'
            '(id INTEGER PRIMARY KEY AUTOINCREMENT,'
            'picture_path UNIQUE, picture_md5, creation_time, cached_name)'
        )

        # self.add_column_if_notfound('pictures', 'cached_path')

        self.close_db()

    def open_db(self):
        db_path = os.path.join(self.profile_folder_path, 'ksdata.db')
        self.db = sqlite3.connect(db_path)
        self.db_cursor = self.db.cursor()

    def close_db(self):
        self.db.commit()
        self.db.close()

    def initialize_setting(self, item, value):
        self.db_cursor.execute('SELECT item FROM settings')
        table_data = self.db_cursor.fetchall()
        table_data = list(zip(*table_data))
        if table_data:
            items = list(table_data[0])
            if item in items:
                return

        db_command = 'INSERT INTO settings (item, value) VALUES (?, ?)'
        self.db_cursor.execute(db_command, (item, value))

    def add_column_if_notfound(self, table, column):
        try:
            self.db_cursor.execute(f'SELECT {column} FROM {table}')
        except sqlite3.OperationalError:
            self.db_cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column}')

    def read_setting(self, item):
        self.open_db()
        self.db_cursor.execute('SELECT * FROM settings WHERE item = ?', (item,))
        temp = self.db_cursor.fetchall()
        temp = list(temp[0])
        value = temp[2]
        self.close_db()
        return value

    def save_setting(self, item, value):
        self.open_db()
        self.db_cursor.execute('UPDATE settings SET value = ? WHERE item = ?', (value, item))
        self.close_db()

    def reset_pictures_table(self):
        self.open_db()
        self.db_cursor.execute(f'DROP TABLE pictures')
        self.db_cursor.execute(
            'CREATE TABLE IF NOT EXISTS pictures'
            '(id INTEGER PRIMARY KEY AUTOINCREMENT,'
            'picture_path UNIQUE, picture_md5, creation_time, cached_name)'
        )
        self.close_db()

    def read_pictures_data(self):
        self.open_db()
        db_command = 'SELECT * FROM pictures'
        self.db_cursor.execute(db_command)
        pictures_data = self.db_cursor.fetchall()
        self.close_db()
        return pictures_data

    def read_latest_pictures_data(self):
        self.open_db()
        db_command = 'SELECT * FROM pictures ORDER BY creation_time DESC'
        self.db_cursor.execute(db_command)
        pictures_data = self.db_cursor.fetchall()
        self.close_db()
        return pictures_data

    def pictures_read_record(self, query_column, query_column_value):
        self.open_db()
        db_command = f'SELECT * FROM pictures WHERE {query_column} = ?'
        self.db_cursor.execute(db_command, (query_column_value,))
        picture_record = self.db_cursor.fetchall()
        self.close_db()
        return picture_record

    def pictures_insert_record(self, picture_path, picture_md5, creation_time):
        self.open_db()
        db_command = 'INSERT OR REPLACE INTO pictures (picture_path, picture_md5, creation_time) VALUES (?, ?, ?)'
        self.db_cursor.execute(
            db_command, (picture_path, picture_md5, creation_time)
        )
        self.close_db()

    def pictures_update_record(self, query_column, query_column_value, target_column, target_column_value):
        self.open_db()
        db_command = f'UPDATE pictures SET {target_column} = ? WHERE {query_column} = ?'
        self.db_cursor.execute(db_command, (target_column_value, query_column_value))
        self.close_db()

    def pictures_delete_record(self, query_column, query_column_value):
        self.open_db()
        db_command = f'DELETE FROM pictures WHERE {query_column} = ?'
        self.db_cursor.execute(db_command, (query_column_value,))
        self.close_db()

    def database_vacuum(self):
        self.open_db()
        self.db_cursor.execute('VACUUM')
        self.close_db()
