

import sys
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialogButtonBox,
                                 QGridLayout, QPushButton, QGroupBox)
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox, QgsColorButton, QgsFileWidget
from qgis.core import QgsMapLayerProxyModel
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QDoubleValidator
import numpy as np


class ThresholdRoiGui(QDialog):

    def __init__(self, tr):
        super().__init__()
        self.tr = tr
        self.setWindowTitle(self.tr('Threshold to ROI'))
        # Get screem geometry
        screem_geometry = QApplication.desktop().availableGeometry()
        screem_width = screem_geometry.width()
        screem_height = screem_geometry.height()
        x, y = int(screem_width * 0.15), int(screem_height * 0.2)
        # Set windown geometry
        self.setGeometry(x, y, 400, 220)
        self.setFixedSize(400, 220)
        # Set default color
        self.default_color = QColor(255, 0, 0)

    def setupUi(self):
        # Main layout
        layout = QVBoxLayout()

        # Raster layer
        raster_layer_label = QLabel(self.tr('Raster layer:'))
        raster_layer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.raster_layer_cbox = QgsMapLayerComboBox()
        self.raster_layer_cbox.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.raster_layer_cbox.layerChanged.connect(self.updateBand)
        self.raster_layer_cbox.layerChanged.connect(self.clean_min_max)

        # Raster band
        raster_band_label = QLabel(self.tr('Band:'))
        raster_band_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.raster_band_cbox = QgsRasterBandComboBox()
        self.raster_band_cbox.setFixedWidth(80)
        self.raster_band_cbox.setLayer(self.raster_layer_cbox.currentLayer())
        self.raster_band_cbox.bandChanged.connect(self.clean_min_max)

        # Output ROI
        output_label = QLabel(self.tr('Output raster:'))
        output_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.output_file = QgsFileWidget()
        self.output_file.setFilter(self.tr('GeoTIFF files (*.tif)'))
        self.output_file.setStorageMode(QgsFileWidget.SaveFile)

        # ROI color
        roi_color_label = QLabel(self.tr('Color:'))
        roi_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.roi_color_button = QgsColorButton()
        self.roi_color_button.setFixedWidth(80)
        self.roi_color_button.setColor(self.default_color)

        # Grid layout
        grid_layout = QGridLayout()
        grid_layout.addWidget(raster_layer_label, 0, 0)
        grid_layout.addWidget(self.raster_layer_cbox, 0, 1, 1, 4)
        grid_layout.addWidget(raster_band_label, 0, 5)
        grid_layout.addWidget(self.raster_band_cbox, 0, 6)
        grid_layout.addWidget(output_label, 1, 0)
        grid_layout.addWidget(self.output_file, 1, 1, 1, 4)
        grid_layout.addWidget(roi_color_label, 1, 5)
        grid_layout.addWidget(self.roi_color_button, 1, 6)

        # Threshold
        self.histogram_button = QPushButton(self.tr('Histogram'))
        self.histogram_button.setFixedWidth(100)

        # Min_Max
        min_label = QLabel(self.tr('Min. value:'))
        self.min_edit = QLineEdit()
        self.min_edit.setReadOnly(True)
        max_label = QLabel(self.tr('Max. Value:'))
        self.max_edit = QLineEdit()
        self.max_edit.setReadOnly(True)

        # Min_Max Layout
        min_max_layout = QHBoxLayout()
        min_max_layout.addWidget(min_label)
        min_max_layout.addWidget(self.min_edit)
        min_max_layout.addWidget(max_label)
        min_max_layout.addWidget(self.max_edit)

        # Group Box
        group_layout = QVBoxLayout()
        group_layout.addWidget(self.histogram_button)
        group_layout.addLayout(min_max_layout)
        group_box = QGroupBox(self.tr('Threshold'))
        group_box.setLayout(group_layout)

        # buttons
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttons_box = QDialogButtonBox(buttons)
        buttons_box.accepted.connect(self.accept)
        buttons_box.rejected.connect(self.reject)

        # Layout setting
        layout.addLayout(grid_layout)
        layout.addSpacing(10)
        layout.addWidget(group_box)
        layout.addSpacing(10)
        layout.addWidget(buttons_box)
        self.setLayout(layout)

    # Internal methods
    def updateBand(self):
        self.raster_band_cbox.setLayer(self.raster_layer_cbox.currentLayer())

    def clean_min_max(self):
        self.min_edit.clear()
        self.max_edit.clear()

    # Public methods
    def getLayer(self):
        return self.raster_layer_cbox.currentLayer()

    def getBand(self):
        return self.raster_band_cbox.currentBand()

    def getFilePath(self):
        return self.output_file.filePath()

    def getColor(self):
        return self.roi_color_button.color()

    def getXMin(self):
        return self.min_edit.text()

    def getXMax(self):
        return self.max_edit.text()
