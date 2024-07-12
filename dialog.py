

import os
from .gui.main import ThresholdRoiGui
from .gui.histogram import HistogramPlot
from qgis.PyQt.QtWidgets import QDialog
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.core import QgsRasterLayer, QgsProject, Qgis, QgsPalettedRasterRenderer, QgsPresetSchemeColorRamp
from qgis import processing


class ThresholdRoiDialog(ThresholdRoiGui):
    def __init__(self, iface, tr):
        self.iface = iface
        self.tr = tr
        super(ThresholdRoiDialog, self).__init__(tr=self.tr)
        # Main dialog window configuration
        self.setupUi()
        # Connecting the histogram button to the histogram dialog
        self.histogram_button.clicked.connect(self.histogram)

    def histogram(self):
        # Current settings of the main dialog window
        self.layer = self.getLayer()
        self.band = self.getBand()
        self.color = self.getColor()

        # Checking the validity of the raster layer
        histogram = self.layer.dataProvider().histogram(self.band).histogramVector
        if not histogram:
            self.iface.messageBar().pushMessage(self.tr('Error'), self.tr('The select layer is invalid.'),
                                                level=Qgis.Critical)
            return

        # Show raster histogram dialog window
        inputs = HistogramPlot(iface=self.iface, tr=self.tr, layer=self.layer, band=self.band, color=self.color)
        result = inputs.exec_()

        if not result:
            return

        # Add selected threshold values
        self.min_edit.setText(str(inputs.get_x_min()))
        self.max_edit.setText(str(inputs.get_x_max()))

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

        # Data provider
        provider = self.layer.dataProvider()

        # Min and Max values
        x_min, x_max = float(self.getXMin()), float(self.getXMax())

        # Output data types
        data_types = {'Byte': 0, 'Int16': 1, 'UInt16': 2, 'Int32': 3, 'UInt32': 4, 'Float32': 5, 'Float64': 6,
                      'CInt16': 7, 'CInt32': 8, 'CFloat32': 9, 'CFloat64': 10}

        # Processing algorithm
        table = [x_min, x_max, 1]
        no_data = provider.sourceNoDataValue(self.band)
        data_type = str(provider.dataType(self.band)).split('.')[1]
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
            color_ramp = QgsPresetSchemeColorRamp([self.color])
            classes = QgsPalettedRasterRenderer.classDataFromRaster(output_layer.dataProvider(), 1, color_ramp)
            renderer = QgsPalettedRasterRenderer(output_layer.dataProvider(), 1, classes)
            output_layer.setRenderer(renderer)
            QgsProject().instance().addMapLayer(output_layer)
