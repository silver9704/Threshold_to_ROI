

import os
from .gui.main import ThresholdRoiGui
from .gui.histogram import HistogramPlot
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.QtCore import Qt
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.core import QgsRasterLayer, QgsProject, Qgis, QgsPalettedRasterRenderer, QgsPresetSchemeColorRamp
from qgis import processing


class ThresholdRoiDialog(ThresholdRoiGui):
    def __init__(self, iface, tr, parent=None):
        self.iface = iface
        self.tr = tr
        super().__init__(tr=tr, parent=parent)
        # Connecting the histogram button to the histogram dialog
        self.histogram_button.clicked.connect(self.histogram)
        # Current settings of the main dialog window
        self.layer = self.getLayer()
        self.band = self.getBand()
        self.color = self.getColor()
        # Provider attributes
        self.provider = self.layer.dataProvider()
        self.min_value = self.provider.bandStatistics(self.band).minimumValue
        self.max_value = self.provider.bandStatistics(self.band).maximumValue
        # Connect signals
        self.raster_layer_cbox.layerChanged.connect(self.update_layer)
        self.raster_band_cbox.bandChanged.connect(self.update_band)
        self.roi_color_button.colorChanged.connect(self.update_color)

    def histogram(self):
        # Checking the validity of the raster layer
        histogram = self.provider.histogram(self.band).histogramVector

        if not histogram:
            self.iface.messageBar().pushMessage(self.tr('Error'), self.tr('The select layer is invalid.'),
                                                level=Qgis.Critical)
            return

        # Show raster histogram window
        self.histogram_window = HistogramPlot(iface=self.iface, tr=self.tr, provider=self.provider, band=self.band,
                                              min_value=self.min_value, max_value=self.max_value, color=self.color,
                                              parent=self)
        self.histogram_window.accepted.connect(self.set_min_max)
        self.histogram_window.show()

    # Slots
    def set_min_max(self):
        # Add selected threshold values
        self.min_edit.setText(str(self.histogram_window.get_x_min()))
        self.max_edit.setText(str(self.histogram_window.get_x_max()))

    def clean_min_max(self):
        # Clean min and max lineedit
        self.min_edit.clear()
        self.max_edit.clear()

    def update_layer(self):
        # Update layer
        self.layer = self.getLayer()
        self.raster_band_cbox.setLayer(self.layer)
        self.update_band()

    def update_band(self):
        # Update band
        self.raster_band_cbox.setLayer(self.layer)
        self.band = self.getBand()
        self.clean_min_max()
        self.update_provider()

    def update_provider(self):
        # Update provider attributes
        self.provider = self.layer.dataProvider()
        self.min_value = self.provider.bandStatistics(self.band).minimumValue
        self.max_value = self.provider.bandStatistics(self.band).maximumValue

    def update_color(self):
        # Update color
        self.color = self.getColor()

    def get_table(self, x_min, x_max):
        # Table calculation function
        if x_min == self.min_value and x_max != self.max_value:
            table = [self.min_value, x_max, 1,
                     x_max, self.max_value, 0]
        elif x_min != self.min_value and x_max == self.max_value:
            table = [self.min_value, x_min, 0,
                     x_min, self.max_value, 1]
        elif x_min == self.min_value and x_max == self.max_value:
            table = [self.min_value, self.max_value, 1]
        else:
            table = [self.min_value, x_min, 0,
                     x_min, x_max, 1,
                     x_max, self.max_value, 0]

        return table

    # Public functions
    def valid_path(self):
        # Output path verification function
        path = self.getFilePath()
        if not path:
            return False
        if not os.path.splitext(path)[1].lower() == '.tif':
            return False
        if not os.path.isdir(os.path.dirname(path)):
            return False
        return True

    def valid_min_max(self):
        # x_min and x_max verification function
        x_min = self.getXMin()
        x_max = self.getXMax()

        if not x_min or not x_max:
            return False

        return True

    def clear_content(self):
        # Value reset function
        self.output_file.setFilePath('')
        self.clean_min_max()

    def calculate(self):
        # Min and Max values
        x_min, x_max = float(self.getXMin()), float(self.getXMax())

        # Output data types
        data_types = {'Byte': 0, 'Int16': 1, 'UInt16': 2, 'Int32': 3, 'UInt32': 4, 'Float32': 5, 'Float64': 6,
                      'CInt16': 7, 'CInt32': 8, 'CFloat32': 9, 'CFloat64': 10}

        # Processing algorithm
        table = self.get_table(x_min=x_min, x_max=x_max)
        no_data = self.provider.sourceNoDataValue(self.band)
        data_type = str(self.provider.dataType(self.band)).split('.')[1]
        output_file_path = self.getFilePath()

        processing.run('native:reclassifybytable',
                       {'INPUT_RASTER': self.layer,
                        'RASTER_BAND': self.band,
                        'TABLE': table,
                        'NO_DATA': no_data,
                        'RANGE_BOUNDARIES': 2,
                        'NODATA_FOR_MISSING': True,
                        'DATA_TYPE': data_types[data_type],
                        'OUTPUT': output_file_path})

        # Create output layer
        output_name = os.path.splitext(os.path.basename(output_file_path))[0]
        output_layer = QgsRasterLayer(output_file_path, output_name)

        if not output_layer.isValid():
            self.iface.messageBar().pushMessage(self.tr('Error'), self.tr('The output layer was invalid.'),
                                                level=Qgis.Critical)
        else:
            # Add result to project
            classes = [
                QgsPalettedRasterRenderer.Class(0, Qt.transparent),
                QgsPalettedRasterRenderer.Class(1, self.color)
            ]
            renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1, classes)
            output_layer.setRenderer(renderer)
            QgsProject().instance().addMapLayer(output_layer)
