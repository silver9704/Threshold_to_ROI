

def classFactory(iface):
    # Load the plugin to QGIS Interface
    from .threshold_ROI import ThresholdROIPlugin
    return ThresholdROIPlugin(iface)
