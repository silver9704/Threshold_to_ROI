

import sys
from qgis.PyQt.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit,
                                 QDialogButtonBox, QGridLayout, QDoubleSpinBox)
from qgis.gui import QgsMapLayerComboBox, QgsRasterBandComboBox, QgsColorButton, QgsFileWidget
from qgis.core import (QgsMapLayerProxyModel, QgsRasterHistogram, QgsRasterLayer, QgsColorRampShader, QgsRasterShader,
                       QgsSingleBandPseudoColorRenderer, QgsProject, Qgis)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer
from qgis.PyQt.QtGui import QColor, QDoubleValidator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import numpy as np


class HistogramCanvas(FigureCanvasQTAgg):
    # Span signal
    span_changed = pyqtSignal(float, float)

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
        self.span = SpanSelector(self.ax, onselect=self.on_select, direction='horizontal', useblit=True,
                                 props=dict(alpha=0.5, facecolor=self.color_span), interactive=True,
                                 onmove_callback=self.on_move)

    # Internal methods
    def on_select(self, x_min, x_max):
        self.span_changed.emit(x_min, x_max)

    def on_move(self, x_min, x_max):
        self.span_changed.emit(x_min, x_max)

    # Public method
    def update_span(self, x_min, x_max):
        self.span.extents = (x_min, x_max)


class HistogramPlot(QDialog):
    def __init__(self, iface, tr, provider, band, min_value, max_value, color, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.tr = tr
        self.setWindowTitle(self.tr('Histogram'))
        # Get screem geometry
        screen_geometry = QApplication.desktop().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        x, y = int(screen_width * 0.1), int(screen_height * 0.3)
        # Set window geometry
        self.setGeometry(x, y, 450, 400)
        self.setMinimumSize(450, 400)
        # Attributes
        self.provider = provider
        self.band = band
        self.min_value = min_value
        self.max_value = max_value
        self.color = color
        self.preview_layer = None
        # Timer for debouncing
        self.update_timer = QTimer()
        self.update_timer.setInterval(180)
        # Create canvas
        self.create_canvas()

    def create_canvas(self):
        # Matplotlib canvas
        bins = int(np.ceil(np.sqrt(self.provider.xSize() * self.provider.ySize())))
        histogram = self.provider.histogram(self.band, bins)
        self.canvas = HistogramCanvas(frequency=histogram.histogramVector, bins=bins, x_min=self.min_value,
                                      x_max=self.max_value, color_span=self.color.name(), tr=self.tr)
        self.canvas.span_changed.connect(self.update_min_max)
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
        self.min_value_edit.textChanged.connect(self.update_canvas_span)
        max_value_label = QLabel(self.tr('Max. Value:'))
        max_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.max_value_edit = QLineEdit()
        self.max_value_edit.setValidator(validator)
        self.max_value_edit.setText(str(self.max_value))
        self.max_value_edit.textChanged.connect(self.update_canvas_span)

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

        self.update_canvas_span()

    # Internals methods
    def update_canvas_span(self):
        # Function that updates the canvas span
        try:
            x_min = float(self.min_value_edit.text())
            x_max = float(self.max_value_edit.text())
            self.canvas.update_span(x_min, x_max)
        except ValueError:
            pass  # Ignore invalid values in QLineEdit

        self.update_timer.start()

    def update_min_max(self, x_min, x_max):
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
        self.preview_layer = QgsRasterLayer(self.provider.dataSourceUri(), 'roi_preview')
        QgsProject.instance().addMapLayer(self.preview_layer)

        # Move the layer to the top
        root = QgsProject.instance().layerTreeRoot()
        layer_node = root.findLayer(self.preview_layer.id())
        root.insertChildNode(0, layer_node.clone())
        root.removeChildNode(layer_node)

        # Render settings
        self.fnc = QgsColorRampShader()
        self.fnc.setColorRampType(QgsColorRampShader.Discrete)
        self.fnc.setClassificationMode(QgsColorRampShader.Quantile)

        shader = QgsRasterShader()
        shader.setRasterShaderFunction(self.fnc)

        renderer = QgsSingleBandPseudoColorRenderer(self.preview_layer.dataProvider(), self.band, shader)
        self.preview_layer.setRenderer(renderer)

        # Update preview layer
        self.update_preview_layer()

        # connect new signal
        self.update_timer.timeout.connect(self.update_preview_layer)

    def update_preview_layer(self):
        # Function that updates the preview layer in real time
        x_min = max(float(self.min_value_edit.text()), self.min_value)
        x_max = min(float(self.max_value_edit.text()), self.max_value)

        # Preview layer color setting
        if x_min == self.min_value and x_max != self.max_value:
            color_list = [QgsColorRampShader.ColorRampItem(x_max, self.color),
                          QgsColorRampShader.ColorRampItem(np.inf, Qt.transparent)]

        elif x_min != self.min_value and x_max == self.max_value:
            color_list = [QgsColorRampShader.ColorRampItem(x_min, Qt.transparent),
                          QgsColorRampShader.ColorRampItem(np.inf, self.color)]

        elif x_min == self.min_value and x_max == self.max_value:
            color_list = [QgsColorRampShader.ColorRampItem(np.inf, self.color)]

        else:
            color_list = [QgsColorRampShader.ColorRampItem(x_min, Qt.transparent),
                          QgsColorRampShader.ColorRampItem(x_max,  self.color),
                          QgsColorRampShader.ColorRampItem(np.inf, Qt.transparent)]

        self.fnc.setColorRampItemList(color_list)
        self.preview_layer.triggerRepaint()

    def hide_preview_layer(self, visible):
        # Function that handles the visibility of the preview layer
        root = QgsProject.instance().layerTreeRoot()
        layer_node = root.findLayer(self.preview_layer.id())
        if layer_node is not None:
            layer_node.setItemVisibilityChecked(visible)

    def cleanup_preview_layer(self):
        # Function that removes the preview layer
        if self.preview_layer is not None:
            QgsProject.instance().removeMapLayer(self.preview_layer.id())
            self.preview_layer = None
            self.iface.mapCanvas().refresh()

    def accept(self):
        self.update_timer.stop()
        self.cleanup_preview_layer()
        super().accept()

    def reject(self):
        self.update_timer.stop()
        self.cleanup_preview_layer()
        super().reject()

    # Public methods
    def get_x_min(self):
        x_min = float(self.min_value_edit.text())
        return max(x_min, self.min_value)

    def get_x_max(self):
        x_max = float(self.max_value_edit.text())
        return min(x_max, self.max_value)
