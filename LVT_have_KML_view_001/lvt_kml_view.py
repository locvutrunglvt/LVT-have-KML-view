"""LVT have KML view - Main Plugin Class.

Registers the plugin with QGIS and manages toolbar/menu integration.
"""

import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from .lvt_kml_view_dialog import LvtKmlViewDialog


class LvtKmlView:
    """QGIS Plugin: SHP to KML/KMZ with HTML popup."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dlg = None

    def initGui(self):
        """Called when plugin is loaded in QGIS."""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        if not os.path.exists(icon_path):
            icon = QIcon()
        else:
            icon = QIcon(icon_path)

        self.action = QAction(icon, 'LVT have KML view', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu('LVT have KML view', self.action)

    def unload(self):
        """Called when plugin is unloaded."""
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu('LVT have KML view', self.action)

    def run(self):
        """Open the plugin dialog."""
        self.dlg = LvtKmlViewDialog(self.iface, self.iface.mainWindow())
        self.dlg.exec_()
