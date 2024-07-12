

import sys
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit,
                                 QDialogButtonBox, QGridLayout, QDoubleSpinBox)
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox, QgsColorButton, QgsFileWidget
from qgis.core import (QgsMapLayerProxyModel, QgsRasterHistogram, QgsRasterLayer, QgsColorRampShader, QgsRasterShader,
                       QgsSingleBandPseudoColorRenderer, QgsProject, Qgis)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QColor, QDoubleValidator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import numpy as np


class HistogramCanvas(FigureCanvasQTAgg):
    def __init__(self, frequency, bins, x_min, x_max, color_span, tr):
        self.frequency = frequency
        self.bins = bins
        self.x_min = x_min
        self.x_max = x_max
        self.color_span = color_span
        figure = Figure(facecolor='#D6D5D5', layout='tight')
        self.ax = figure.add_subplot(111)
        self.tr = tr
        super().__init__(figure)
        self.graph()

    def graph(self):
        # Variables
        x_axis = np.linspace(self.x_min, self.x_max, self.bins)

        # Plot
        self.ax.plot(x_axis, self.frequency, color='black', linewidth=1)
        self.ax.minorticks_on()
        self.ax.grid(which='major', linestyle='--')
        self.ax.set_axisbelow(True)
        self.ax.tick_params(axis='both', labelsize=8)
        self.ax.set_title(self.tr('Raster Histogram'), fontsize=10)
        self.ax.set_xlabel(self.tr('Pixel value'), fontsize=9)
        self.ax.set_ylabel(self.tr('Frequency'), fontsize=9)

        # Span selector
        self.span = SpanSelector(self.ax, self.on_select, direction='horizontal', useblit=True, interactive=True,
                                 props=dict(alpha=0.5, facecolor=self.color_span), onmove_callback=self.on_move)

    # Internal methods
    def on_select(self, x_min, x_max):
        self.parent().on_select(x_min, x_max)

    def on_move(self, x_min, x_max):
        self.parent().on_move(x_min, x_max)

    def span_update(self, x_min, x_max):
        self.span.extents = (x_min, x_max)


class HistogramPlot(QDialog):
    def __init__(self, iface, tr, layer, band, color):
        super().__init__()
        self.iface = iface
        self.tr = tr
        self.setWindowTitle(self.tr('Histogram'))
        self.setFixedHeight(400)
        self.setFixedWidth(450)
        self.layer = layer
        self.band = band
        self.color = color
        self.preview_layer = None
        self.create_canvas()

    def create_canvas(self):
        # Matplotlib canvas
        provider = self.layer.dataProvider()
        bins = int(np.ceil(np.sqrt(provider.xSize() * provider.ySize())))
        histogram = provider.histogram(self.band, bins)
        self.min_value = provider.bandStatistics(self.band).minimumValue
        self.max_value = provider.bandStatistics(self.band).maximumValue
        self.canvas = HistogramCanvas(frequency=histogram.histogramVector, bins=bins, x_min=self.min_value,
                                      x_max=self.max_value, color_span=self.color.name(), tr=self.tr)
        self.setupUI()

    def setupUI(self):
        # Main layout
        layout = QVBoxLayout()

        # Min-Max widgets
        validator = QDoubleValidator()
        min_value_label = QLabel(self.tr('Min. Value:'))
        min_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.min_value_edit = QLineEdit()
        self.min_value_edit.setValidator(validator)
        self.min_value_edit.setText(str(self.min_value))
        self.min_value_edit.textChanged.connect(self.canvas_span_update)
        max_value_label = QLabel(self.tr('Max. Value:'))
        max_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.max_value_edit = QLineEdit()
        self.max_value_edit.setValidator(validator)
        self.max_value_edit.setText(str(self.max_value))
        self.max_value_edit.textChanged.connect(self.canvas_span_update)

        # Min-Max layout
        min_max_layout = QHBoxLayout()
        min_max_layout.addWidget(min_value_label)
        min_max_layout.addWidget(self.min_value_edit)
        min_max_layout.addWidget(max_value_label)
        min_max_layout.addWidget(self.max_value_edit)

        # Preview and buttons
        self.preview_checkbox = QCheckBox(self.tr('Preview'))
        self.preview_checkbox.setChecked(False)
        self.preview_checkbox.clicked.connect(self.handle_preview_checkbox)
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttons_box = QDialogButtonBox(buttons)
        buttons_box.accepted.connect(self.accept)
        buttons_box.rejected.connect(self.reject)

        # Lower layout
        lower_layout = QHBoxLayout()
        lower_layout.addWidget(self.preview_checkbox)
        lower_layout.addWidget(buttons_box)

        # Setting
        layout.addLayout(min_max_layout)
        layout.addWidget(self.canvas)
        layout.addLayout(lower_layout)
        self.setLayout(layout)

        self.canvas_span_update()

    # Internals methods
    def canvas_span_update(self):
        # Function that updates the canvas span
        try:
            x_min = float(self.min_value_edit.text())
            x_max = float(self.max_value_edit.text())
            self.canvas.span_update(x_min, x_max)
        except ValueError:
            pass  # Ignore invalid values in QLineEdit

    def on_select(self, x_min, x_max):
        # Function that updates the text edit
        self.min_value_edit.setText(str(x_min))
        self.max_value_edit.setText(str(x_max))

    def on_move(self, x_min, x_max):
        # Function that updates the text edit
        self.min_value_edit.setText(str(x_min))
        self.max_value_edit.setText(str(x_max))

    def handle_preview_checkbox(self):
        if self.preview_layer is None:
            # Create the preview layer for the first time
            self.create_preview_layer()
        else:
            # Hide or show the preview layer if it already exists
            if self.preview_checkbox.isChecked():
                self.hide_preview_layer(True)
            else:
                self.hide_preview_layer(False)

    def create_preview_layer(self):
        self.preview_layer = QgsRasterLayer(self.layer.source(), 'roi_preview')
        QgsProject.instance().addMapLayer(self.preview_layer)

        # Move the layer to the top
        root = QgsProject.instance().layerTreeRoot()
        layer_node = root.findLayer(self.preview_layer.id())
        root.insertChildNode(0, layer_node.clone())
        root.removeChildNode(layer_node)

        # connect new signals
        self.min_value_edit.textChanged.connect(self.update_preview_layer)
        self.max_value_edit.textChanged.connect(self.update_preview_layer)

        self.update_preview_layer()

    def hide_preview_layer(self, visible):
        # Function that handles the visibility of the preview layer
        root = QgsProject.instance().layerTreeRoot()
        layer_node = root.findLayer(self.preview_layer.id())
        if layer_node is not None:
            layer_node.setItemVisibilityChecked(visible)

    def update_preview_layer(self):
        # Function that updates the preview layer in real time
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Discrete)
        fnc.setClassificationMode(QgsColorRampShader.Quantile)

        x1 = float(self.min_value_edit.text())
        x2 = float(self.max_value_edit.text())
        color_list = self.color_list(x1, x2)

        fnc.setColorRampItemList(color_list)

        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)

        renderer = QgsSingleBandPseudoColorRenderer(self.preview_layer.dataProvider(), self.band, shader)

        self.preview_layer.setRenderer(renderer)
        self.preview_layer.triggerRepaint()

    def color_list(self, x1, x2):
        # Preview layer color setting function
        x_min = max(x1, self.min_value)
        x_max = min(x2, self.max_value)

        if x_min == self.min_value and x_max != self.max_value:
            list_ = [QgsColorRampShader.ColorRampItem(x_max, self.color),
                     QgsColorRampShader.ColorRampItem(np.inf, Qt.transparent)]

        elif x_min != self.min_value and x_max == self.max_value:
            list_ = [QgsColorRampShader.ColorRampItem(x_min, Qt.transparent),
                     QgsColorRampShader.ColorRampItem(np.inf, self.color)]

        elif x_min == self.min_value and x_max == self.max_value:
            list_ = [QgsColorRampShader.ColorRampItem(np.inf, self.color)]

        else:
            list_ = [QgsColorRampShader.ColorRampItem(x_min, Qt.transparent),
                     QgsColorRampShader.ColorRampItem(x_max,  self.color),
                     QgsColorRampShader.ColorRampItem(np.inf, Qt.transparent)]

        return list_

    def cleanup_preview_layer(self):
        # Function that removes the preview layer
        if self.preview_layer is not None:
            QgsProject.instance().removeMapLayer(self.preview_layer.id())
            self.iface.mapCanvas().refresh()

    def accept(self):
        self.cleanup_preview_layer()
        super().accept()

    def reject(self):
        self.cleanup_preview_layer()
        super().reject()

    # Public methods
    def get_x_min(self):
        x_min = float(self.min_value_edit.text())
        return max(x_min, self.min_value)

    def get_x_max(self):
        x_max = float(self.max_value_edit.text())
        return min(x_max, self.max_value)
