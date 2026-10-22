# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DoYouWantToSaveDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 117)
        self.SaveButton = QPushButton(Dialog)
        self.SaveButton.setObjectName(u"SaveButton")
        self.SaveButton.setGeometry(QRect(11, 78, 93, 28))
        self.CancelButton = QPushButton(Dialog)
        self.CancelButton.setObjectName(u"CancelButton")
        self.CancelButton.setGeometry(QRect(296, 78, 93, 28))
        self.DontSaveButton = QPushButton(Dialog)
        self.DontSaveButton.setObjectName(u"DontSaveButton")
        self.DontSaveButton.setGeometry(QRect(155, 78, 93, 28))
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(80, 10, 240, 60))

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.SaveButton.setText(QCoreApplication.translate("Dialog", u"Save", None))
        self.CancelButton.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
        self.DontSaveButton.setText(QCoreApplication.translate("Dialog", u"Don't Save", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Do you want to save the current project?", None))
    # retranslateUi

