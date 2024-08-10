import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QTableWidget, QLabel, QLineEdit,
                               QPushButton, QComboBox, QSlider, QApplication, QListWidget, QListWidgetItem)

from kshandler import Commands


class MessageDialog(QDialog):
    def __init__(self, message):
        super(MessageDialog, self).__init__()
        self.commands = Commands()
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        screen = QApplication.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()

        x = int((self.screen_width - 350) / 2)
        y = int((self.screen_height - 90) / 2)

        self.setGeometry(x, y, 350, 90)

        self.setWindowTitle('Notice')

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel()
        layout.addWidget(label)
        label.setText(message)


class YesNoDialog(QDialog):
    option_signal = Signal(str)

    def __init__(self, img_path):
        super(YesNoDialog, self).__init__()
        self.commands = Commands()
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.option = str()

        screen = QApplication.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()
        x = int((self.screen_width - 350) / 2)
        y = int((self.screen_height - 90) / 2)
        self.setGeometry(x, y, 350, 90)

        self.setWindowTitle('Confirmation')

        dialog_layout = QVBoxLayout()
        self.setLayout(dialog_layout)

        dialog_label = QLabel()
        dialog_layout.addWidget(dialog_label)
        dialog_label.setText(
            f'The file {os.path.basename(img_path)} will be deleted instantly\n'
            f'from your disk once you press "Yes". Are you sure?')

        dialog_buttons_layout = QHBoxLayout()
        dialog_buttons_layout.setAlignment(Qt.AlignHCenter)
        dialog_layout.addLayout(dialog_buttons_layout)

        dialog_yes_button = QPushButton('Yes')
        dialog_yes_button.setFixedSize(80, 25)
        dialog_buttons_layout.addWidget(dialog_yes_button)
        dialog_yes_button.clicked.connect(lambda: self.select_option('Yes'))

        dialog_no_button = QPushButton('No')
        dialog_no_button.setFixedSize(80, 25)
        dialog_buttons_layout.addWidget(dialog_no_button)
        dialog_no_button.clicked.connect(lambda: self.select_option('No'))

    def select_option(self, option):
        if option == 'Yes':
            self.option = option
        elif option == 'No':
            self.option = option

        self.option_signal.emit(option)
        self.close()


class ExifDialog(QDialog):
    def __init__(self, exif_details):
        super(ExifDialog, self).__init__()
        self.commands = Commands()
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        screen = QApplication.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()
        x = int((self.screen_width - 500) / 2)
        y = int((self.screen_height - 600) / 2)
        self.setGeometry(x, y, 500, 600)

        self.setWindowTitle('Details of Exif')

        dialog_layout = QVBoxLayout()
        self.setLayout(dialog_layout)

        exif_table = QTableWidget()
        dialog_layout.addWidget(exif_table)

        exif_table.setColumnCount(2)
        exif_table.setHorizontalHeaderLabels(['Tag', 'Value'])
        exif_table.setColumnWidth(0, 170)
        exif_table.setColumnWidth(1, 280)
        exif_table.verticalHeader().setHidden(True)
        exif_table.setShowGrid(False)
        exif_table.setRowCount(len(exif_details))

        tag_name = dict()
        tag_value = dict()
        n = 0
        for tag, value in exif_details.items():
            tag_name[n] = QLabel(tag)
            tag_value[n] = QLabel(value)

            tag_name[n].setMargin(5)
            tag_value[n].setMargin(5)

            exif_table.setCellWidget(n, 0, tag_name[n])
            exif_table.setCellWidget(n, 1, tag_value[n])

            n = n + 1


class SaveSizeDialog(QDialog):
    option_signal = Signal(str, str, str)

    def __init__(self, current_size, full_size):
        super(SaveSizeDialog, self).__init__()
        self.commands = Commands()
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.option = str()
        self.value = str()
        self.current_size = current_size
        self.full_size = full_size

        screen = QApplication.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()
        x = int((self.screen_width - 350) / 2)
        y = int((self.screen_height - 90) / 2)
        self.setGeometry(x, y, 350, 90)

        self.setWindowTitle('Please give a size')

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.layout)

        self.dialog_label = QLabel()
        self.layout.addWidget(self.dialog_label)
        self.dialog_label.setText(
            'For resizing a picture, you may give width or height, and\n'
            'the picture will be resized at a correct aspect ratio.'
        )

        self.full_size_layout = QHBoxLayout()
        self.layout.addLayout(self.full_size_layout)
        self.dialog_button_full_size = QRadioButton()
        self.full_size_layout.addWidget(self.dialog_button_full_size)
        if full_size:
            self.dialog_button_full_size.setText(f'Full size ({full_size})')
        else:
            self.dialog_button_full_size.setText(f'Full size')

        self.dialog_button_full_size.clicked.connect(lambda: self.hide_entry(full_size))

        if current_size != full_size:
            self.current_size_layout = QHBoxLayout()
            self.layout.addLayout(self.current_size_layout)
            self.dialog_button_current_size = QRadioButton()
            self.current_size_layout.addWidget(self.dialog_button_current_size)
            self.dialog_button_current_size.setText(f'Current size ({current_size})')
            self.dialog_button_current_size.clicked.connect(lambda: self.hide_entry(current_size))

        self.custom_width_layout = QHBoxLayout()
        self.custom_width_layout.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(self.custom_width_layout)

        self.custom_width_button = QRadioButton()
        self.custom_width_button.setFixedWidth(108)
        self.custom_width_layout.addWidget(self.custom_width_button)
        self.custom_width_button.setText('Custom width')
        self.custom_width_button.clicked.connect(lambda: self.custom_width('Custom width'))

        self.custom_width_entry = QLineEdit()
        self.custom_width_layout.addWidget(self.custom_width_entry)
        self.custom_width_entry.hide()
        self.custom_width_entry.setFixedWidth(60)

        self.custom_height_layout = QHBoxLayout()
        self.custom_height_layout.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(self.custom_height_layout)

        self.custom_height_button = QRadioButton()
        self.custom_height_button.setFixedWidth(108)
        self.custom_height_layout.addWidget(self.custom_height_button)
        self.custom_height_button.setText('Custom height')
        self.custom_height_button.clicked.connect(lambda: self.custom_height('Custom height'))

        self.custom_height_entry = QLineEdit()
        self.custom_height_layout.addWidget(self.custom_height_entry)
        self.custom_height_entry.hide()
        self.custom_height_entry.setFixedWidth(60)

        self.custom_format_layout = QHBoxLayout()
        self.custom_format_layout.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(self.custom_format_layout)

        self.custom_format_label = QLabel()
        self.custom_format_label.setText('Format: ')
        self.custom_format_label.setFixedWidth(50)
        self.custom_format_layout.addWidget(self.custom_format_label)

        self.custom_format_option = QComboBox()
        self.custom_format_option.setFixedWidth(100)
        self.custom_format_option.addItems(['PNG (.png)', 'JPEG (.jpg)', 'WebP (.webp)', 'GIF (.gif)'])
        self.custom_format_layout.addWidget(self.custom_format_option)
        self.custom_format_option.currentTextChanged.connect(self.custom_format)

        self.custom_quality_layout = QHBoxLayout()
        self.custom_quality_layout.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(self.custom_quality_layout)

        self.custom_quality_label = QLabel()
        self.custom_quality_label.setText('Quality (1-100): ')
        self.custom_quality_label.setFixedWidth(100)
        self.custom_quality_layout.addWidget(self.custom_quality_label)
        self.custom_quality_label.hide()

        self.custom_quality_chooser = QSlider()
        self.custom_quality_chooser.setOrientation(Qt.Horizontal)
        self.custom_quality_chooser.setFixedWidth(200)
        self.custom_quality_chooser.setMinimum(1)
        self.custom_quality_chooser.setMaximum(100)
        self.custom_quality_chooser.setSingleStep(1)
        self.custom_quality_chooser.setValue(100)
        self.custom_quality_layout.addWidget(self.custom_quality_chooser)
        self.custom_quality_chooser.hide()
        self.custom_quality_chooser.sliderReleased.connect(self.custom_quality)

        self.custom_quality_value = QLabel()
        self.custom_quality_value.setFixedWidth(20)
        self.custom_quality_value.setText('100')
        self.custom_quality_layout.addWidget(self.custom_quality_value)
        self.custom_quality_value.hide()

        self.bottom_layout = QHBoxLayout()
        self.layout.addLayout(self.bottom_layout)
        dialog_exit_button = QPushButton('OK')
        dialog_exit_button.setFixedSize(80, 25)
        self.bottom_layout.addWidget(dialog_exit_button)
        dialog_exit_button.setDefault(True)
        dialog_exit_button.clicked.connect(self.close_dialog)

    def hide_entry(self, option):
        self.option = option
        self.custom_width_entry.hide()
        self.custom_height_entry.hide()

    def custom_width(self, option):
        self.option = option
        self.custom_height_entry.hide()
        self.custom_width_entry.show()

    def custom_height(self, option):
        self.option = option
        self.custom_width_entry.hide()
        self.custom_height_entry.show()

    def custom_format(self, custom_format):
        if custom_format == 'JPEG (.jpg)' or custom_format == 'WebP (.webp)':
            self.custom_quality_label.show()
            self.custom_quality_chooser.show()
            self.custom_quality_value.show()
        else:
            self.custom_quality_label.hide()
            self.custom_quality_chooser.hide()
            self.custom_quality_value.hide()

    def custom_quality(self):
        self.custom_quality_value.setText(str(self.custom_quality_chooser.value()))

    def close_dialog(self):
        if self.option == self.full_size:
            self.value = self.full_size
        elif self.option == self.current_size:
            self.value = self.current_size
        elif self.option == 'Custom width' and self.custom_width_entry.text():
            self.value = str(self.custom_width_entry.text())
        elif self.option == 'Custom height' and self.custom_height_entry.text():
            self.value = f'x{self.custom_height_entry.text()}'
        else:
            return

        img_quality = str(self.custom_quality_chooser.value())

        img_format = self.custom_format_option.currentText()
        if img_format != 'JPEG (.jpg)' and img_format != 'WebP (.webp)':
            img_quality = ''

        self.option_signal.emit(self.value, img_quality, img_format)
        self.close()


class MakePDFDialog(QDialog):
    option_signal = Signal(list, str, str, str, str, str)

    def __init__(self):
        super(MakePDFDialog, self).__init__()
        self.commands = Commands()
        if os.name == 'nt':
            logo_path = self.commands.get_logo_path()
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))

        self.img_list = list()
        self.file_with_resolution_list = list()

        self.page_size_value = ''
        self.page_layout_value = 'top'
        self.background_colour_value = 'white'
        self.density_value = '72'
        self.img_quality_value = '100'

        screen = QApplication.primaryScreen()
        self.screen_width = screen.availableSize().width()
        self.screen_height = screen.availableSize().height()
        x = int((self.screen_width - 500) / 2)
        y = int((self.screen_height - 600) / 2)
        self.setGeometry(x, y, 500, 600)

        self.setWindowTitle('Make PDF Document')

        self.dialog_layout = QVBoxLayout()
        self.setLayout(self.dialog_layout)

        self.img_list_table = QListWidget()
        self.dialog_layout.addWidget(self.img_list_table)

        self.page_size_layout = QHBoxLayout()
        self.page_size_layout.setAlignment(Qt.AlignLeft)
        self.dialog_layout.addLayout(self.page_size_layout)

        self.page_size_label = QLabel('Page Size')
        self.page_size_layout.addWidget(self.page_size_label)

        self.page_size = QComboBox()
        self.page_size_layout.addWidget(self.page_size)

        self.page_size.setFixedWidth(100)
        self.page_size.addItems(['Image size', 'A4 page'])

        self.page_size.currentTextChanged.connect(self.page_size_chooser)

        self.page_layout_layout = QHBoxLayout()
        self.page_layout_layout.setAlignment(Qt.AlignLeft)
        self.dialog_layout.addLayout(self.page_layout_layout)

        self.page_layout_label = QLabel('Layout')
        self.page_layout_layout.addWidget(self.page_layout_label)

        self.page_layout = QComboBox()
        self.page_layout_layout.addWidget(self.page_layout)

        self.page_layout.setFixedWidth(100)
        self.page_layout.addItems(['Top', 'Center', 'Bottom'])

        self.page_layout.currentTextChanged.connect(self.page_layout_chooser)

        self.background_colour_layout = QHBoxLayout()
        self.background_colour_layout.setAlignment(Qt.AlignLeft)
        self.dialog_layout.addLayout(self.background_colour_layout)

        self.background_colour_label = QLabel('Background')
        self.background_colour_layout.addWidget(self.background_colour_label)

        self.background_colour = QComboBox()
        self.background_colour_layout.addWidget(self.background_colour)

        self.background_colour.setFixedWidth(100)
        self.background_colour.addItems(['White', 'Grey', 'Black', 'Blue', 'Red'])

        self.background_colour.currentTextChanged.connect(self.background_colour_chooser)

        self.density_layout = QHBoxLayout()
        self.density_layout.setAlignment(Qt.AlignLeft)
        self.dialog_layout.addLayout(self.density_layout)

        self.density_label = QLabel('Density')
        self.density_layout.addWidget(self.density_label)

        self.density = QComboBox()
        self.density_layout.addWidget(self.density)

        self.density.setFixedWidth(100)
        self.density.addItems(['72', '96', '150', '300'])

        self.density.currentTextChanged.connect(self.density_chooser)

        self.img_quality_layout = QHBoxLayout()
        self.img_quality_layout.setAlignment(Qt.AlignLeft)
        self.dialog_layout.addLayout(self.img_quality_layout)

        self.img_quality_label = QLabel('Image Quality (1 - 100): ')
        self.img_quality_label.setFixedWidth(150)
        self.img_quality_layout.addWidget(self.img_quality_label)

        self.img_quality = QSlider()
        self.img_quality_layout.addWidget(self.img_quality)

        self.img_quality.setOrientation(Qt.Horizontal)
        self.img_quality.setFixedWidth(200)
        self.img_quality.setMinimum(1)
        self.img_quality.setMaximum(100)
        self.img_quality.setSingleStep(1)
        self.img_quality.setValue(100)

        self.img_quality.sliderReleased.connect(self.img_quality_chooser)

        self.img_quality_option_label = QLabel()
        self.img_quality_option_label.setFixedWidth(20)
        self.img_quality_option_label.setText('100')
        self.img_quality_layout.addWidget(self.img_quality_option_label)

        self.bottom_layout = QHBoxLayout()
        self.dialog_layout.addLayout(self.bottom_layout)
        
        self.dialog_exit_button = QPushButton('OK')
        self.dialog_exit_button.setFixedSize(80, 25)

        self.bottom_layout.addWidget(self.dialog_exit_button)
        self.dialog_exit_button.setDefault(True)

        self.dialog_exit_button.clicked.connect(self.close_dialog)

    def add_picture(self, img_path):
        image = QPixmap(img_path)

        img_width = image.width()
        img_height = image.height()
        img_resolution = f'{img_width}x{img_height}'
        img_with_resolution = (img_path, img_resolution)

        if img_path not in self.img_list:
            img_item = QListWidgetItem(img_path)
            self.img_list_table.addItem(img_item)

            self.img_list.append(img_path)
            self.file_with_resolution_list.append(img_with_resolution)

    def page_size_chooser(self, option):
        if option == 'Image size':
            self.page_size_value = ''
        elif option == 'A4 page':
            self.page_size_value = 'a4'

    def page_layout_chooser(self, option):
        if option == 'Top':
            self.page_layout_value = 'top'
        elif option == 'Center':
            self.page_layout_value = 'center'
        elif option == 'Bottom':
            self.page_layout_value = 'bottom'

    def background_colour_chooser(self, option):
        if option == 'White':
            self.background_colour_value = 'white'
        elif option == 'Grey':
            self.background_colour_value = 'gray'
        elif option == 'Black':
            self.background_colour_value = 'black'
        elif option == 'Blue':
            self.background_colour_value = 'blue'
        elif option == 'Red':
            self.background_colour_value = 'red'

    def density_chooser(self, option):
        if option == '72':
            self.density_value = '72'
        elif option == '96':
            self.density_value = '96'
        elif option == '150':
            self.density_value = '150'
        elif option == '300':
            self.density_value = '300'

    def img_quality_chooser(self):
        self.img_quality_value = str(self.img_quality.value())
        self.img_quality_option_label.setText(str(self.img_quality.value()))

    def close_dialog(self):
        self.option_signal.emit(self.file_with_resolution_list, self.page_size_value, self.page_layout_value,
                                self.background_colour_value, self.density_value, self.img_quality_value)
        self.close()