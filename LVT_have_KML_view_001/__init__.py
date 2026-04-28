# LVT have KML view - QGIS Plugin
# Version: _001
# Author: LVT (Lộc Vũ Trung)
# Description: Convert Shapefile to KML/KMZ with rich HTML popup for Google Earth Mobile


def classFactory(iface):
    """Load LvtKmlView class from file lvt_kml_view."""
    from .lvt_kml_view import LvtKmlView
    return LvtKmlView(iface)
