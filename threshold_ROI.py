# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThresholdROI
                                 A QGIS plugin
 This plugin allows you to create an ROI (Region of Interest) with selected
 threshold values from the histogram of a raster layer.
                              -------------------
        begin                : 2024-07-11
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Silver Piedra
        email                : silverpiedraherrera@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QLocale, QLibraryInfo
from qgis.core import QgsProject
import os

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .dialog import ThresholdRoiDialog


class ThresholdROIPlugin:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Threshold_to_ROI_{}.qm'.format(locale)
        )
        if os.path.exists(locale_path):
            # Plugin translator
            self.plugin_translator = QTranslator()
            self.plugin_translator.load(locale_path)
            QCoreApplication.installTranslator(self.plugin_translator)
        # Default translator
        self.translator = QTranslator()
        self.translator.load("qtbase_" + QLocale.system().name(),
                             QLibraryInfo.location(QLibraryInfo.TranslationsPath))
        QCoreApplication.installTranslator(self.translator)

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('ThresholdROIPlugin', message)

    def initGui(self):
        # create action that will start plugin configuration
        icon_path = ":/plugins/Threshold_to_ROI/icon/icon.png"
        self.action = QAction(QIcon(icon_path),
                              "Threshold to ROI",
                              self.iface.mainWindow())
        self.action.setObjectName("ThresholdToROI")
        self.action.setWhatsThis(self.tr("Threshold To ROI Plugin"))
        self.action.setStatusTip(self.tr("Plugin for create ROI (Region of Interest) using threshold values."))
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&ThresholdToROI", self.action)

        self.first_start = True

    def unload(self):
        self.iface.removePluginMenu("&ThresholdToROI", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.window = ThresholdRoiDialog(iface=self.iface, tr=self.tr)
        else:
            self.window.clear_content()

        while True:
            result = self.window.exec_()

            if not result:
                break

            # Handling invalid parameters
            valid_path = self.window.valid_path()
            valid_min_max = self.window.valid_min_max()

            if not valid_path:
                QMessageBox.warning(self.window, self.tr('Warning'), self.tr('Please select an valid output path.'),
                                    buttons=QMessageBox.Ok)
                continue

            if not valid_min_max:
                QMessageBox.warning(self.window, self.tr('Warning'),
                                    self.tr('Please select the minimum and maximum values.'),
                                    buttons=QMessageBox.Ok)
                continue

            # Calculation execution
            self.window.calculate()
            break
