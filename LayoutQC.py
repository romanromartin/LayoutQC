#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import glob
import io
import os
import sys
from functools import partial

import mysql.connector
from PIL import Image as ImagePil
from PIL import ImageCms, ImageDraw, TiffTags
from PIL import features
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Layout import Layout

# import libtiff

# If needed to show debag set to True
LayoutQC_DEBAG = False
style_OK = "color: #cdd6e6;  font-size: 22px; font-family: Arial; " \
           "background-color: rgba(55, 55, 68, 0.2); border: 1px solid; border-color: #516588; margin: 0px;"
style_title = "color: #6f81a0;  font-size: 22px; font-family: Arial; " \
              "background-color: rgba(55, 55, 68, 0.0);  "


class Preview(QGraphicsView):

    def wheelEvent(self, event):

        mouse = event.angleDelta().y()/120
        if mouse > 0:
            ex.zoomIn()
        elif mouse < 0:
            ex.zoomOut()


class LayOutQC(QMainWindow):

    def __init__(self):
        super().__init__()

        self.tables = [' ']
        self.pr = ''

        # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\STYLES IN CSS////////////////////////////////
        self.style_norm = "color: #cdd6e6;  font-size: 20px; font-family: Arial; background-color: rgba(55, 55, 68, " \
                          "0.4); margin-bottom: 13px; margin-top: 13px; border: 1px solid; border-color: #516588; "
        self.style_warning = "color: #cdd6e6;  font-size: 20px; font-family: Arial; background-color: rgba(55, 55, " \
                             "68, 0.4); margin-bottom: 13px; margin-top: 13px; border: 4px solid; border-color: " \
                             "#ff0000; "
        self.style_appFont_title = "color: #8fa3c4;  font-size: 18px; font-family: Arial;  margin-left: 20px; " \
                                   "margin-right: 20px; margin-bottom: 5px; margin-top: 5px;background-color: rgba(" \
                                   "55, 55, 68, 0.4); "
        self.style_appFont = "color: #8fa3c4;  font-size: 16px; font-family: Arial;  margin-bottom: 5px; margin-top: " \
                             "5px; text-align: center; "
        self.style_OK = "color: #cdd6e6;  font-size: 22px; font-family: Arial;"
        self.style_not_OK = "color: #ff0000;  font-size: 22px; font-family: Arial;"
        self.style_header = "color: #ffff00;  font-size: 16px; font-family: Arial;"

        self.initUI()

    def initUI(self):
        self.scene = QGraphicsScene()
        self.zoom = 0.1
        self.view = Preview(self.scene, self)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setTransform(QTransform().scale(self.zoom, self.zoom))
        self.view.setBackgroundBrush(QBrush(QColor(40, 40, 50)))
        self.setCentralWidget(self.view)
        self.LayOutLoaded = False
        # self.TT()

        openAction = QAction(QIcon('icons/open.png'), 'Открыть', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Открыть макет для проверки')
        openAction.triggered.connect(self.loadDialog)

        saveAction = QAction(QIcon('icons/save.png'), 'Сохранить', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Сохранить макет')
        saveAction.triggered.connect(self.saveDialog)

        closeAction = QAction(QIcon('icons/close.png'), 'Закрыть', self)
        closeAction.setShortcut('Ctrl+C')
        closeAction.setStatusTip('Закрыть макет')

        editAction = QAction(QIcon('icons/edit.png'), 'Редактировать', self)
        editAction.setShortcut('Ctrl+C')
        editAction.setStatusTip('Закрыть макет')

        mailAction = QAction(QIcon('icons/mail.png'), 'Почта', self)
        mailAction.setShortcut('Ctrl+C')
        mailAction.setStatusTip('Перейти к почте')

        exitAction = QAction(QIcon('icons/exit.png'), 'Выйти', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Закрыть приложение')
        exitAction.triggered.connect(self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self, shortcut="Ctrl+Z", enabled=True)
        self.zoomOutAct = QAction("Zoom &Out (25%)", self, shortcut="Ctrl+X", enabled=True)
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="A")

        icon1 = QIcon()
        icon1.addPixmap(QPixmap('icons/auto_TT.png'))
        icon1.addPixmap(QPixmap('icons/auto_TT_dis.png'), QIcon.Disabled)
        icon1.addPixmap(QPixmap('icons/auto_TT_cl.png'), QIcon.Active)
        self.AutoSelectTT_act = QAction(icon1, 'Автоподбор ТТ', self, shortcut="Ctrl+T", enabled=False,
                                        triggered=self.Auto_SelectTT)

        icon2 = QIcon()
        icon2.addPixmap(QPixmap('icons/check.png'))
        icon2.addPixmap(QPixmap('icons/check_dis.png'), QIcon.Disabled)
        icon2.addPixmap(QPixmap('icons/check_cl.png'), QIcon.Active)
        self.CheckTT_act = QAction(icon2, 'Автоподбор ТТ', self, shortcut="Ctrl+R", enabled=False,
                                   triggered=self.CheckLayOut)

        icon3 = QIcon()
        icon3.addPixmap(QPixmap('icons/top.png'))
        icon3.addPixmap(QPixmap('icons/top_dis.png'), QIcon.Disabled)
        icon3.addPixmap(QPixmap('icons/top_cl.png'), QIcon.Active)
        self.TopZone_act = QAction(icon3, 'Автоподбор ТТ', self, shortcut="Ctrl+Y", enabled=False,
                                   triggered=self.ShowVipZone)

        self.icon4 = QIcon()
        self.icon4.addPixmap(QPixmap('icons/show_input.png'))
        self.icon4.addPixmap(QPixmap('icons/show_input_dis.png'), QIcon.Disabled)
        self.icon4.addPixmap(QPixmap('icons/show_input_cl.png'), QIcon.Active)
        self.Show_input_act = QAction(self.icon4, 'Автоподбор ТТ', self, shortcut="Ctrl+I", enabled=False,
                                      triggered=self.ShowInputPrw)

        self.statusBar()

        but_tool = QPushButton()
        but_tool.setIcon(QIcon('icons/close.png'))
        but_tool.setIconSize(QSize(40, 40))

        self.dism_iconX = QLabel()
        self.dism_iconX.setPixmap(QPixmap('icons/dism_x.png'))
        self.dism_iconX.setToolTip('Ширина макета в мм')
        self.dismX = QLabel()
        self.dismX.setText('      ')
        self.dismX.setStyleSheet(self.style_norm)

        self.dism_iconY = QLabel()
        self.dism_iconY.setPixmap(QPixmap('icons/dism_y.png'))
        self.dism_iconY.setToolTip('Высота макета в мм')
        self.dismY = QLabel()
        self.dismY.setText('      ')
        self.dismY.setStyleSheet(self.style_norm)

        self.res_icon = QLabel()
        self.res_icon.setPixmap(QPixmap('icons/dpi.png'))
        self.res_icon.setToolTip(
            'Разрешение макета в dpi.\n Если исходник макета в ppcm, макет будет отконвертирован в dpi автоматически')
        self.resToolbar = QLabel()
        self.resToolbar.setText('      ')
        self.resToolbar.setStyleSheet(self.style_norm)

        self.mode_icon = QLabel()
        self.mode_icon.setPixmap(QPixmap('icons/mode.png'))
        self.mode_icon.setToolTip('Цветовой режим макета')
        self.modeToolbar = QLabel()
        self.modeToolbar.setText('      ')
        self.modeToolbar.setStyleSheet(self.style_norm)

        self.icc_icon = QLabel()
        self.icc_icon.setPixmap(QPixmap('icons/icc.png'))
        self.icc_icon.setToolTip('Цветовой профиль макета')
        self.iccToolbar = QLabel()
        self.iccToolbar.setText('      ')
        self.iccToolbar.setStyleSheet(self.style_norm)

        self.comboLabel_title = QLabel('ТЕХ ТРЕБОВАНИЯ')
        self.comboLabel_title.setStyleSheet(self.style_appFont_title)
        self.comboLabel_tables = QLabel('Раздел')
        self.comboLabel_tables.setStyleSheet(self.style_appFont)
        self.comboTT_tables = QComboBox()
        self.comboTT_tables.addItems(self.tables)
        self.comboTT_tables.activated[str].connect(self.tables_Activated)
        self.comboLabel2 = QLabel('Локация')
        self.comboLabel2.setStyleSheet(self.style_appFont)
        self.comboTT_location = QComboBox()
        self.comboTT_location.addItems([' '])
        self.comboTT_location.activated[str].connect(self.location_Activated)
        self.comboLabel3 = QLabel('Название ТТ')
        self.comboLabel3.setStyleSheet(self.style_appFont)
        self.comboTT_name = QComboBox()
        self.comboTT_name.addItems([' '])
        self.comboTT_name.activated[str].connect(self.name_Activated)
        self.comboLabelCode = QLabel('Код ТТ')
        self.comboLabelCode.setStyleSheet(self.style_appFont)
        self.comboTT_code = QComboBox()
        self.comboTT_code.addItems([' '])
        self.comboTT_code.activated[str].connect(self.code_Activated)
        self.TT_dismentions = QLabel('')
        self.TT_dismentions.setStyleSheet(self.style_appFont)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('Файл')
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(editAction)
        fileMenu.addAction(closeAction)
        fileMenu.addAction(exitAction)

        checkMenu = menubar.addMenu('Проверить')
        editMenu = menubar.addMenu('Редактировать')
        mailMenu = menubar.addMenu('Почта')
        mailMenu.addAction(mailAction)
        viewMenu = menubar.addMenu('Вид')
        viewMenu.addAction(self.zoomInAct)
        viewMenu.addAction(self.zoomOutAct)

        toolbar = self.addToolBar('TopToolbar')
        toolbar.setIconSize(QSize(40, 40))
        toolbar.addAction(openAction)
        toolbar.addAction(saveAction)
        toolbar.addAction(closeAction)
        toolbar.addAction(editAction)
        toolbar.addAction(mailAction)
        toolbar.addAction(exitAction)
        toolbar.addSeparator()
        toolbar.addWidget(self.dism_iconX)
        toolbar.addWidget(self.dismX)
        toolbar.addWidget(self.dism_iconY)
        toolbar.addWidget(self.dismY)
        toolbar.addWidget(self.res_icon)
        toolbar.addWidget(self.resToolbar)
        toolbar.addWidget(self.mode_icon)
        toolbar.addWidget(self.modeToolbar)
        toolbar.addWidget(self.icc_icon)
        toolbar.addWidget(self.iccToolbar)

        self.toolbarTT = self.addToolBar('TT_Toolbar')
        self.addToolBar(Qt.RightToolBarArea, self.toolbarTT)
        # self.toolbarTT.setStyleSheet(self.style_appFont)
        self.toolbarTT.setIconSize(QSize(200, 40))
        self.toolbarTT.addWidget(self.comboLabel_title)
        self.toolbarTT.addWidget(self.comboLabel_tables)
        self.toolbarTT.addWidget(self.comboTT_tables)
        self.toolbarTT.addWidget(self.comboLabel2)
        self.toolbarTT.addWidget(self.comboTT_location)
        self.toolbarTT.addWidget(self.comboLabel3)
        self.toolbarTT.addWidget(self.comboTT_name)
        self.toolbarTT.addWidget(self.comboLabelCode)
        self.toolbarTT.addWidget(self.comboTT_code)
        self.toolbarTT.addWidget(self.TT_dismentions)
        self.toolbarTT.addAction(self.AutoSelectTT_act)
        self.toolbarTT.addAction(self.CheckTT_act)
        self.toolbarTT.addAction(self.TopZone_act)
        self.toolbarTT.addAction(self.Show_input_act)

        self.desktop = QApplication.desktop()
        self.setGeometry(0, 0, self.desktop.width() - 5, self.desktop.height() - 80)
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.setWindowTitle('LayOutQC')
        self.show()

    def zoomIn(self):
        if self.zoom <=30:
            self.zoom *= 1.05
            self.updateView()

    def zoomOut(self):
        if self.zoom >= 0.05:
            self.zoom /= 1.05
            self.updateView()

    def updateView(self):
        self.view.setTransform(QTransform().scale(self.zoom, self.zoom))
    # \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\END UI\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

    def loadDialog(self):
        home_folder = os.listdir('D:/')
        if not 'LayOutQC' in home_folder:
            os.mkdir('D:/LayOutQC/')
        if not '--INCOMING--' in home_folder:
            os.mkdir('D:/--INCOMING--/')
        self.load_name = QFileDialog.getOpenFileName(self, 'Open file', 'D:/LayOutQC/', "TIF files (*.tif)")[0]
        self.FileName = self.load_name.split("/")[-1]
        self.PathName = self.load_name[:len(self.load_name) - len(self.FileName)]
        if self.FileName:
            self.im = ImagePil.open(self.load_name)
            self.LayOutLoaded = True
            self.prw_name = 'temp/input_temp.png'
            self.comboTT_tables.setCurrentText(' ')
            self.comboTT_location.clear()
            self.comboTT_location.addItems([' '])
            self.comboTT_name.clear()
            self.comboTT_name.addItems([' '])
            self.comboTT_code.clear()
            self.comboTT_code.addItems([' '])
            self.TT_dismentions.setText('')
            self.CheckTT_act.setEnabled(False)
            self.Show_input_act.setIcon(self.icon4)
            self.Show_input_act.setEnabled(False)
            self.TopZone_act.setEnabled(False)
            files = glob.glob('temp/*')
            for f in files:
                os.remove(f)

            # Runing Layout Module
            self.layout = Layout(self.im)
            self.layout._DEBAG(LayoutQC_DEBAG)

            #  set Layout info into Toolbar
            self.modeToolbar.setStyleSheet(self.layout.layout_mode_status())
            self.iccToolbar.setStyleSheet(self.layout.layout_profile_status())

            self.modeToolbar.setText(self.layout.image.mode)
            self.resToolbar.setText(str(self.layout.resolution))
            self.dismX.setText(str(self.layout.width_layout) + 'mm')
            self.dismY.setText(str(self.layout.height_layout) + 'mm')
            self.iccToolbar.setText(self.layout.layout_profile_name())

            # make $ showing preview
            self.layout.make_prw(self.prw_name, LayoutQC_DEBAG=LayoutQC_DEBAG)


            # self.im222=QPixmap(self.prw_name)


            # self.scaleFactor = 1.0
            # show_x = self.desktop.width() - 270
            # show_y = show_x / self.im.size[0] * self.im.size[1]
            # if show_y > self.desktop.height() - 200:
            #     show_y = self.desktop.height() - 200
            #     show_x = show_y / self.im.size[1] * self.im.size[0]

            width_central_widget = self.desktop.width() - 222
            height_central_widget = self.desktop.width() - 178
            if self.im.size[0] > self.im.size[1]:
                self.zoom = width_central_widget / self.im.size[0]
            else:
                self.zoom = height_central_widget / self.im.size[1]

            self.scene.clear()
            self.scene.addPixmap(QPixmap(self.prw_name))
            self.updateView()

            print(self.desktop.width())
            print(self.desktop.height())


            self.AutoSelectTT_act.setEnabled(True)
            self.tables = self.layout.layout_db_tabeles
            self.comboTT_tables.addItems(self.tables)
            self.name_Layout()

    def name_Layout(self):
        self.completer_list = []
        self.name_and_folder = self.FileName.split('.')[0]
        self.suget = ''
        for n in os.listdir('D:/LayOutQC/'):
            if not os.path.isfile('D:/LayOutQC/' + n):
                self.completer_list.append(n)
        self.popup(700, 50, 'Название макета')
        grid = QGridLayout()
        klientTitle = QLabel('Клиент')
        klientTitle.setStyleSheet(style_title)
        sugetTitle = QLabel('Сюжет')
        sugetTitle.setStyleSheet(style_title)
        klientInput = QLineEdit(self.name_and_folder)
        completer = QCompleter(self.completer_list)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        klientInput.setCompleter(completer)
        klientInput.textChanged[str].connect(self.klient_name)
        klientInput.setStyleSheet(style_OK)
        sugetInput = QLineEdit()
        sugetInput.textChanged[str].connect(self.suget_name)
        sugetInput.setStyleSheet(style_OK)
        grid.addWidget(klientTitle, 0, 0)
        grid.addWidget(sugetTitle, 1, 0)
        grid.addWidget(klientInput, 0, 1)
        grid.addWidget(sugetInput, 1, 1)
        self.layoutPop_old.insertLayout(0, grid)
        self.add_butOK(connect=self.make_Folder, text='Закрыть')
        self.add_butClose()
        self.path = self.PathName
        self.popUpModal.show()

    def klient_name(self, name_):
        self.name_and_folder = name_

    def suget_name(self, name_):
        self.suget = name_



    def make_Folder(self):
        # if self.name_and_folder != None or ' ':
        #     self.name_Layout()
        self.layout.makeFolder(self.name_and_folder, self.suget)




    def saveDialog(self):
        self.klient_suget = self.name_and_folder + '_' + self.suget
        self.signature = self.layout.makeSignature()
        self.comment = self.layout.makeComment()
        self.popup(900, 50, "Код ТТ")
        grid = QGridLayout()
        klientTitle = QLabel('Название')
        klientTitle.setStyleSheet(style_title)
        sugetTitle = QLabel('Подпись')
        sugetTitle.setStyleSheet(style_title)
        comentTitle = QLabel('Коментарий')
        comentTitle.setStyleSheet(style_title)
        nameInput = QLineEdit(self.klient_suget)
        nameInput.setStyleSheet(style_OK)
        nameInput.textChanged[str].connect(self.ks)

        signatureInput = QLineEdit(self.signature)
        signatureInput.setStyleSheet(style_OK)
        signatureInput.textChanged[str].connect(self.sig)

        commentInput = QLineEdit( self.comment)
        commentInput.setStyleSheet(style_OK)
        commentInput.textChanged[str].connect(self.com)

        person = QLabel('FRA')
        person.setStyleSheet(style_title)
        grid.addWidget(klientTitle, 0, 0)
        grid.addWidget(sugetTitle, 0, 1)
        grid.addWidget(comentTitle, 0, 2)
        grid.addWidget(nameInput, 1, 0)
        grid.addWidget(signatureInput, 1, 1)
        grid.addWidget(commentInput, 1, 2)
        grid.addWidget(person, 1, 3)
        self.layoutPop_old.insertLayout(0, grid)

        self.add_butOK(connect=self.save_)
        self.add_butClose()
        self.popUpModal.show()

    def ks(self, name_):
        self.klient_suget = name_

    def sig(self, name_):
        self.signature = name_

    def com(self, name_):
        self.comment = name_
    def save_(self):
        self.layout.saveLayout(self.klient_suget + self.signature + self.comment,  self.load_name, self.PathName)

    # ====================================================================================


        # ======================================  TT DATABASE  ==============================================

        # |||||||||||||||||||||||||||||||||||||||||||||||QUERY FOR A LOCATION||||||||||||||||||||||||||||||||||

    def tables_Activated(self, text_tables):
        self.comboTT_location.clear()
        self.comboTT_location.addItems([' '])
        self.comboTT_name.clear()
        self.comboTT_name.addItems([' '])
        self.comboTT_code.clear()
        self.comboTT_code.addItems([' '])
        self.TT_dismentions.setText('')
        locations = self.layout.table_Activated(text_tables)
        self.comboTT_location.addItems(locations)
        self.Show_input_act.setEnabled(False)

    # ||||||||||||||||||||||||||||||||||||||||||||||||||QUERY FOR A NAME TT|||||||||||||||||||||||||||||||||||||||

    def location_Activated(self, text_location):
        self.comboTT_name.clear()
        self.comboTT_name.addItems([' '])
        self.comboTT_code.clear()
        self.comboTT_code.addItems([' '])
        self.TT_dismentions.setText('')
        name = self.layout.location_Activated(text_location)
        self.comboTT_name.addItems(name)
        self.Show_input_act.setEnabled(False)

    # |||||||||||||||||||||||||||||||||||||QUERY FOR A CODE TT|||||||||||||||||||||||||||||||||||||||||||||
    def name_Activated(self, text_name):
        self.comboTT_code.clear()
        self.comboTT_code.addItems([' '])
        self.TT_dismentions.setText('')
        self.codes = self.layout.name_Activated(text_name)
        self.comboTT_code.addItems(self.codes)
        if text_name != ' ':
            if self.LayOutLoaded:
                self.TT_dismentions.setText(self.layout.layout_db.tt_value())
                self.CheckTT_act.setEnabled(True)
                # self.TopZone_act.setEnabled(True)
        self.Show_input_act.setEnabled(False)
        if LayoutQC_DEBAG:
            print('Name ', text_name, ' activated')

    def code_Activated(self, text_code):
        if text_code == 'выбрать несколько конструкций':
            self.PopUpCode()
        if LayoutQC_DEBAG:
            print('Code ', text_code, ' activated')
        self.Show_input_act.setEnabled(False)

    def ButtonClicked(self):
        checked_list = []
        for i in range(self.table_autoselectedTT.rowCount()):
            if self.table_autoselectedTT.cellWidget(i, 0).findChild(type(QCheckBox())).isChecked():
                checked_list.append(self.table_autoselectedTT.item(i, 1).text())
        ch = [str(checked_list).replace("', '", ",")[2:-2]]
        self.comboTT_code.clear()
        self.comboTT_code.addItems(ch + ['выбрать несколько конструкций'] + self.codes[:-1])
        self.code_Activated(ch[0])

    # ||||||||||||||||||||||||||||||||||||||||||||||||||||FUNC TO SHOW POPUP CODE|||||||||||||||||||||||||||||||
    def PopUpCode(self):
        self.popup(200, 400, "Код ТТ")
        self.table_autoselectedTT = QTableWidget(len(self.codes[:-1]), 2, self)
        self.table_autoselectedTT.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_autoselectedTT.setStyleSheet(
            "background-color: rgba(55, 55, 68, 0.1); color: #8fa3c4;  font-size: 16px; font-family: Arial;  "
            "margin-bottom: 5px; margin-top: 5px; text-align: center;")
        self.table_autoselectedTT.horizontalHeader().hide()
        self.table_autoselectedTT.verticalHeader().hide()
        self.table_autoselectedTT.setShowGrid(False)
        row = 0
        for name_row in self.codes[:-1]:
            widget = QWidget()
            checkbox = QCheckBox()
            checkbox.setCheckState(Qt.Unchecked)
            layoutH = QHBoxLayout(widget)
            layoutH.addWidget(checkbox)
            layoutH.setAlignment(Qt.AlignCenter)
            layoutH.setContentsMargins(0, 0, 0, 0)
            self.table_autoselectedTT.setCellWidget(row, 0, widget)
            self.table_autoselectedTT.setItem(row, 1, QTableWidgetItem(name_row))
            row += 1
        self.layoutPop_old.insertWidget(0, self.table_autoselectedTT)
        self.add_butOK(connect=self.ButtonClicked)
        self.add_butClose()
        self.popUpModal.show()

    def popup(self, x_w, y_h, name_pop):
        self.popUpModal = QWidget(ex, Qt.Tool)
        self.popUpModal.setWindowTitle(name_pop)
        self.popUpModal.setGeometry(self.desktop.width() / 2 - x_w / 2, self.desktop.height() / 2 - y_h / 2, x_w, y_h)
        self.popUpModal.setWindowModality(Qt.WindowModal)
        self.popUpModal.setAttribute(Qt.WA_DeleteOnClose, True)
        palle = self.popUpModal.palette()
        palle.setBrush(QPalette.Window, QBrush(QPixmap("bg_workspace_tools.png")))
        self.popUpModal.setPalette(palle)
        self.layoutPop_old = QVBoxLayout(self)
        self.layout_but = QHBoxLayout()
        self.layoutPop_old.addLayout(self.layout_but)
        self.popUpModal.setLayout(self.layoutPop_old)

    def Auto_SelectTT(self):
        self.autoselect_result = self.layout.Auto_SelectTT() \
                                 + [
                                     '---------------------------------------Похожие ТТ---------------------------------------'] \
                                 + self.layout.Auto_SelectTT_warning()

        self.popup(800, 400, "Выберите ТТ")
        self.table_autoselectedTT = QTableWidget(len(self.autoselect_result), 1, self)
        self.table_autoselectedTT.setStyleSheet(
            "background-color: rgba(55, 55, 68, 0.1); color: #8fa3c4;  font-size: 16px; "
            "font-family: Arial;  text-align: center;")
        self.table_autoselectedTT.setShowGrid(False)
        self.table_autoselectedTT.verticalHeader().hide()
        self.table_autoselectedTT.horizontalHeader().hide()
        self.table_autoselectedTT.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        row = 0
        for name_row in self.autoselect_result:
            if name_row == '---------------------------------------Похожие ТТ---------------------------------------':
                m = str(name_row)
            else:
                m = str(name_row).replace("', '", ", ")[2:-2]
            self.table_autoselectedTT.setItem(row, 0, QTableWidgetItem(m))
            row += 1
        header_no_TT = QLabel('Нет подходящих ТТ').setStyleSheet(self.style_not_OK)
        if self.autoselect_result:
            self.layoutPop_old.insertWidget(0, self.table_autoselectedTT)
        else:
            self.layoutPop_old.insertWidget(0, header_no_TT, alignment=Qt.AlignCenter)
        self.table_autoselectedTT.clicked.connect(self.AutoSelectChecked)
        self.add_butClose()
        self.popUpModal.show()

    def AutoSelectChecked(self):
        choosed_TT = []
        for n in self.table_autoselectedTT.selectedItems():
            choosed_TT = self.autoselect_result[n.row()]
        if choosed_TT != '---------------------------------------Похожие ТТ---------------------------------------':
            text_tables = choosed_TT[0]
            self.comboTT_tables.setCurrentText(text_tables)
            self.tables_Activated(text_tables)
            text_location = choosed_TT[1]
            self.comboTT_location.setCurrentText(text_location)
            self.location_Activated(text_location)
            text_name = choosed_TT[2]
            self.comboTT_name.setCurrentText(text_name)
            self.name_Activated(text_name)
            self.comboTT_code.setCurrentText(choosed_TT[3])
            self.popUpModal.close()
            self.CheckTT_act.setEnabled(True)
            self.Show_input_act.setEnabled(False)

    # ----------------------------------------------CHECKING!!!!!!!!!!!! _______
    def CheckLayOut(self):
        self.fin_temp = 'temp/out.tif'
        self.layout.CheckLayOut_func()

        checkpop = []
        CheckResult = QLabel(self.layout.CheckResult)
        CheckResult.setStyleSheet(self.style_OK)
        self.dismX.setStyleSheet(self.style_norm)
        self.dismY.setStyleSheet(self.style_norm)
        self.dismX.setText(str(self.layout.width_layout) + 'mm')
        self.dismY.setText(str(self.layout.height_layout) + 'mm')
        checkpop.append(CheckResult)
        if self.layout.CheckResult != 'Ширина и высота по ТТ ОК':
            CheckResult.setStyleSheet(self.style_not_OK)
            Check_edit_dimentions = QPushButton('Подогнать под размеры в ТТ')
            Check_edit_dimentions.clicked.connect(self.fit_dimensions)
            checkpop.append(Check_edit_dimentions)
            if self.layout.CheckResult == 'Ширина не по ТТ, а высота по ТТ ОК':
                self.dismX.setStyleSheet(self.style_warning)
            elif self.layout.CheckResult == 'Ширина по ТТ ОК, а высота не по ТТ':
                self.dismY.setStyleSheet(self.style_warning)
            else:
                self.dismX.setStyleSheet(self.style_warning)
                self.dismY.setStyleSheet(self.style_warning)

        CheckResult_DPI = QLabel(self.layout.CheckResult_DPI)
        CheckResult_DPI.setStyleSheet(self.style_OK)
        checkpop.append(CheckResult_DPI)
        if self.layout.CheckResult_DPI != 'Разрешение по ТТ ОК':
            CheckResult_DPI.setStyleSheet(self.style_not_OK)
            self.resToolbar.setStyleSheet(self.style_warning)

        CheckResult_mode = QLabel(self.layout.CheckResult_mode)
        CheckResult_mode.setStyleSheet(self.style_OK)
        checkpop.append(CheckResult_mode)
        self.modeToolbar.setText(self.layout.image.mode)
        self.modeToolbar.setStyleSheet(self.style_norm)
        if self.layout.CheckResult_mode != 'Цветовой режим CMYK OK':
            CheckResult_mode.setStyleSheet(self.style_not_OK)
            Check_edit_mode = QPushButton('Конвертировать в CMYK')
            Check_edit_mode.clicked.connect(self.convert_Mode)
            checkpop.append(Check_edit_mode)
            self.modeToolbar.setStyleSheet(self.style_warning)

        CheckResult_ICC = QLabel(self.layout.CheckResult_ICC)
        CheckResult_ICC.setStyleSheet(self.style_OK)
        checkpop.append(CheckResult_ICC)
        self.iccToolbar.setText(self.layout.layout_profile_name())
        self.iccToolbar.setStyleSheet(self.layout.layout_profile_status())

        if self.layout.CheckResult_ICC != 'Цветовой профиль Euroscale Coated v2 ОК':
            CheckResult_ICC.setStyleSheet(self.style_not_OK)
            if self.layout.CheckResult_mode == 'Цветовой режим CMYK OK' \
                    and CheckResult_ICC != 'Цветовой профиль Euroscale Coated v2 ОК':
                Check_edit_ICC_Euro = QPushButton('Изменить цветовой профиль на Euroscale Coated v2')
                Check_edit_ICC_Euro.clicked.connect(self.assign_Icc)
                checkpop.append(Check_edit_ICC_Euro)

            self.iccToolbar.setStyleSheet(self.style_warning)
        Check_edit_ICC = QPushButton('Выбрать другой цветовой профиль')
        Check_edit_ICC.clicked.connect(self.assign_AnotherICC)
        checkpop.append(Check_edit_ICC)

        self.popup(500, 230, "Результат проверки")
        n = 0
        for v in checkpop:
            self.layoutPop_old.insertWidget(n, v)
            n += 1
        if self.layout.CheckResult == 'Ширина и высота по ТТ ОК' and self.layout.image.mode == 'CMYK':
            self.add_butOK(self.ShowVipZone, 'Показать зону значимых элементов')
            self.TopZone_act.setEnabled(True)
        self.add_butClose()
        self.popUpModal.show()
        self.prw_name = self.layout.prw_name
        self.scene.clear()
        self.scene.addPixmap(QPixmap(self.prw_name))
        self.Show_input_act.setEnabled(True)

    def fit_dimensions(self):
        self.popUpModal.close()
        self.layout.FitDimensions()
        self.CheckLayOut()

    def convert_Mode(self):
        self.popUpModal.close()
        self.layout.ConvertMode_and_Icc()
        self.CheckLayOut()

    def assign_Icc(self):
        self.popUpModal.close()
        self.layout.Assign_Icc()
        self.CheckLayOut()

    def assign_AnotherICC(self):
        self.popUpModal.close()
        self.popup(500, 230, "Результат проверки")
        listdir = [f for f in os.listdir('icc/CMYK/')]
        n = 0
        for v in listdir:
            icc_but = QPushButton(v.split('.')[0])
            icc_but.setStyleSheet(style_OK)
            icc_but.clicked.connect(partial(self.Selected_ICC, v))
            self.layoutPop_old.insertWidget(n, icc_but)
            n += 1
        self.add_butClose()
        self.popUpModal.show()

    def Selected_ICC(self, icc):
        self.popUpModal.close()
        profile = ImageCms.getOpenProfile('icc/CMYK/' + icc)
        self.layout.Assign_Icc(profile)
        self.CheckLayOut()

    def ShowInputPrw(self):
        if self.prw_name == 'temp/convert_ICC_temp.png':
            self.prw_name = 'temp/input_temp.png'
            self.Show_input_act.setIcon(QIcon('icons/show_input_cl.png'))
            self.TopZone_act.setEnabled(False)
            self.CheckTT_act.setEnabled(False)
            self.AutoSelectTT_act.setEnabled(False)
        else:
            self.prw_name = 'temp/convert_ICC_temp.png'
            self.Show_input_act.setIcon(QIcon('icons/show_input.png'))
            self.TopZone_act.setEnabled(True)
            self.CheckTT_act.setEnabled(True)
            self.AutoSelectTT_act.setEnabled(True)
        self.scene.clear()
        self.scene.addPixmap(QPixmap(self.prw_name))

    def ShowVipZone(self):
        if not os.path.exists('temp/vip_temp.png'):
            self.layout.make_VIP_zone()
        if self.prw_name == 'temp/convert_ICC_temp.png' or self.prw_name == 'temp/input_temp.png':
            self.pr = self.prw_name
            self.prw_name = 'temp/vip_temp.png'
            self.CheckTT_act.setEnabled(False)
            self.AutoSelectTT_act.setEnabled(False)
            self.Show_input_act.setEnabled(False)
        elif self.prw_name == 'temp/vip_temp.png':
            self.prw_name = self.pr
            self.CheckTT_act.setEnabled(True)
            self.AutoSelectTT_act.setEnabled(True)
            self.Show_input_act.setEnabled(True)
        self.scene.clear()
        self.scene.addPixmap(QPixmap(self.prw_name))

    def add_butClose(self):
        self.butClose = QPushButton('Отмена')
        self.butClose.clicked.connect(self.popUpModal.close)
        self.layout_but.addWidget(self.butClose)

    def add_butOK(self, connect=None, text='OK'):
        self.butOK = QPushButton(text)
        if connect:
            self.butOK.clicked.connect(connect)
        self.butOK.clicked.connect(self.popUpModal.close)
        self.layout_but.addWidget(self.butOK)

    def CheckResult(self):
        print('checked')

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LayOutQC()
    palleteBGapp = ex.palette()
    palleteBGapp.setBrush(QPalette.Window, QBrush(QPixmap("bg_workspace_tools.png")))
    ex.setPalette(palleteBGapp)

    sys.exit(app.exec_())
