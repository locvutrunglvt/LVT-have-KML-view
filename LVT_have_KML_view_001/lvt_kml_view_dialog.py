import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QComboBox, QLineEdit, QPushButton, QSpinBox, 
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QColorDialog, QGroupBox
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import QgsProject, QgsMapLayerProxyModel, QgsCoordinateReferenceSystem

from .i18n import tr, get_help
from .config_manager import ConfigManager
from .kml_builder import KmlBuilder
from .kml_to_shp import KmlToShpConverter
from .preview_widget import PreviewDialog

class LvtKmlViewDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_default_config()
        self.lang = 'vi' # Default
        
        self.setWindowTitle(tr('plugin_title', self.lang))
        self.setMinimumSize(600, 700)
        
        self._setup_ui()
        self._load_current_layers()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: SHP -> KML
        self.tab_shp2kml = QWidget()
        self._setup_tab_shp2kml()
        self.tabs.addTab(self.tab_shp2kml, tr('tab_shp2kml', self.lang))
        
        # Tab 2: KML -> SHP
        self.tab_kml2shp = QWidget()
        self._setup_tab_kml2shp()
        self.tabs.addTab(self.tab_kml2shp, tr('tab_kml2shp', self.lang))
        
        # Bottom Buttons (Lang, Help, Close)
        btn_layout = QHBoxLayout()
        self.btn_lang = QPushButton(tr('btn_lang', self.lang))
        self.btn_lang.clicked.connect(self._toggle_language)
        
        self.btn_help = QPushButton(tr('tab_help', self.lang))
        self.btn_help.clicked.connect(self._show_help)
        
        btn_layout.addWidget(self.btn_lang)
        btn_layout.addWidget(self.btn_help)
        btn_layout.addStretch()
        
        self.btn_close = QPushButton(tr('btn_cancel', self.lang))
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_close)
        
        self.layout.addLayout(btn_layout)

    def _setup_tab_shp2kml(self):
        layout = QVBoxLayout(self.tab_shp2kml)
        
        # Section 1: Input/Output
        gp_io = QGroupBox(tr('sec_io', self.lang))
        io_layout = QVBoxLayout()
        
        # Layer Selection
        l_layout = QHBoxLayout()
        l_layout.addWidget(QLabel(tr('lbl_layer', self.lang)))
        self.cbo_layers = QComboBox()
        self.cbo_layers.currentIndexChanged.connect(self._on_layer_changed)
        l_layout.addWidget(self.cbo_layers, 1)
        io_layout.addLayout(l_layout)
        
        # SHP Path
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel(tr('lbl_shp', self.lang)))
        self.txt_shp = QLineEdit()
        self.btn_browse_shp = QPushButton(tr('btn_browse', self.lang))
        s_layout.addWidget(self.txt_shp)
        s_layout.addWidget(self.btn_browse_shp)
        io_layout.addLayout(s_layout)
        
        gp_io.setLayout(io_layout)
        layout.addWidget(gp_io)
        
        # Section 2: Name (Map Label) - FEATURE: Adjustable size
        gp_name = QGroupBox(tr('sec_name', self.lang))
        name_layout = QVBoxLayout()
        
        f_layout = QHBoxLayout()
        f_layout.addWidget(QLabel(tr('lbl_field1', self.lang)))
        self.cbo_name1 = QComboBox()
        f_layout.addWidget(self.cbo_name1, 1)
        
        f_layout.addWidget(QLabel(tr('lbl_field2', self.lang)))
        self.cbo_name2 = QComboBox()
        f_layout.addWidget(self.cbo_name2, 1)
        name_layout.addLayout(f_layout)
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel(tr('lbl_sep', self.lang)))
        self.txt_sep = QLineEdit(" - ")
        size_layout.addWidget(self.txt_sep)
        
        # --- KÍCH THƯỚC CHỮ (NAME SIZE) ---
        size_layout.addWidget(QLabel(tr('lbl_name_size', self.lang)))
        self.spn_name_size = QSpinBox()
        self.spn_name_size.setRange(1, 100)
        self.spn_name_size.setValue(12)
        size_layout.addWidget(self.spn_name_size)
        name_layout.addLayout(size_layout)
        
        gp_name.setLayout(name_layout)
        layout.addWidget(gp_name)

        # Section 3: Description (Popup) - FEATURE: Suffix (ha)
        gp_desc = QGroupBox(tr('sec_desc', self.lang))
        desc_layout = QVBoxLayout()
        
        self.tbl_fields = QTableWidget(0, 4)
        self.tbl_fields.setHorizontalHeaderLabels([
            tr('col_check', self.lang), tr('col_field', self.lang), 
            tr('col_alias', self.lang), tr('col_suffix', self.lang)
        ])
        self.tbl_fields.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        desc_layout.addWidget(self.tbl_fields)
        
        gp_desc.setLayout(desc_layout)
        layout.addWidget(gp_desc)

        # Section 4: Polygon Style & Conditional Coloring
        gp_poly = QGroupBox(tr('sec_style', self.lang))
        poly_layout = QVBoxLayout()
        
        # Basic Style (Border/Fill)
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel(tr('lbl_border', self.lang)))
        self.btn_border_color = QPushButton("#FF0000")
        self.btn_border_color.clicked.connect(lambda: self._pick_color(self.btn_border_color))
        b_layout.addWidget(self.btn_border_color)
        
        b_layout.addWidget(QLabel(tr('lbl_width', self.lang)))
        self.spn_border_width = QSpinBox()
        self.spn_border_width.setRange(1, 10)
        self.spn_border_width.setValue(2)
        b_layout.addWidget(self.spn_border_width)
        
        poly_layout.addLayout(b_layout)
        
        f_layout = QHBoxLayout()
        f_layout.addWidget(QLabel(tr('lbl_fill', self.lang)))
        self.btn_fill_color = QPushButton("#00FF00")
        self.btn_fill_color.clicked.connect(lambda: self._pick_color(self.btn_fill_color))
        f_layout.addWidget(self.btn_fill_color)
        
        f_layout.addWidget(QLabel(tr('lbl_opacity', self.lang)))
        self.spn_opacity = QSpinBox()
        self.spn_opacity.setRange(0, 100)
        self.spn_opacity.setValue(50)
        f_layout.addWidget(self.spn_opacity)
        
        poly_layout.addLayout(f_layout)
        
        # Conditional Coloring
        self.chk_cond = QCheckBox(tr('chk_cond', self.lang))
        poly_layout.addWidget(self.chk_cond)
        
        cond_field_layout = QHBoxLayout()
        cond_field_layout.addWidget(QLabel(tr('lbl_cond_field', self.lang)))
        self.cbo_cond_field = QComboBox()
        cond_field_layout.addWidget(self.cbo_cond_field, 1)
        poly_layout.addLayout(cond_field_layout)
        
        gp_poly.setLayout(poly_layout)
        layout.addWidget(gp_poly)

        # Section 5: Header & Row Highlight - FEATURE: Bold/Italic
        gp_style = QGroupBox(tr('sec_header', self.lang))
        style_layout = QVBoxLayout()
        
        # Header Title config
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel(tr('lbl_title', self.lang)))
        self.txt_header_title = QLineEdit(tr('default_title', self.lang))
        h_layout.addWidget(self.txt_header_title)
        
        h_layout.addWidget(QLabel(tr('lbl_title_size', self.lang)))
        self.spn_header_size = QSpinBox()
        self.spn_header_size.setValue(14)
        h_layout.addWidget(self.spn_header_size)
        
        self.chk_header_bold = QCheckBox(tr('chk_bold', self.lang))
        self.chk_header_bold.setChecked(True)
        h_layout.addWidget(self.chk_header_bold)
        style_layout.addLayout(h_layout)

        # Special Row Highlight - FEATURE: Bold/Italic for highlights
        self.chk_row_hl = QCheckBox(tr('chk_row_hl', self.lang))
        style_layout.addWidget(self.chk_row_hl)
        
        hl_opts = QHBoxLayout()
        self.chk_hl_bold = QCheckBox(tr('chk_hl_bold', self.lang))
        self.chk_hl_italic = QCheckBox(tr('chk_hl_italic', self.lang))
        hl_opts.addWidget(self.chk_hl_bold)
        hl_opts.addWidget(self.chk_hl_italic)
        hl_opts.addStretch()
        style_layout.addLayout(hl_opts)
        
        gp_style.setLayout(style_layout)
        layout.addWidget(gp_style)
        
        # Export Buttons
        exp_layout = QHBoxLayout()
        self.btn_preview = QPushButton(tr('btn_preview', self.lang))
        self.btn_preview.clicked.connect(self._preview)
        self.btn_export = QPushButton(tr('btn_export', self.lang))
        self.btn_export.clicked.connect(self._export)
        exp_layout.addWidget(self.btn_preview)
        exp_layout.addWidget(self.btn_export)
        layout.addLayout(exp_layout)
        
    def _setup_tab_kml2shp(self):
        layout = QVBoxLayout(self.tab_kml2shp)
        
        # Input
        gp_in = QGroupBox(tr('lbl_kml_input', self.lang))
        in_layout = QHBoxLayout()
        self.txt_kml_in = QLineEdit()
        self.btn_browse_kml = QPushButton(tr('btn_browse', self.lang))
        self.btn_browse_kml.clicked.connect(self._browse_kml)
        in_layout.addWidget(self.txt_kml_in)
        in_layout.addWidget(self.btn_browse_kml)
        gp_in.setLayout(in_layout)
        layout.addWidget(gp_in)
        
        # Target CRS
        gp_crs = QGroupBox(tr('lbl_target_crs', self.lang))
        crs_layout = QVBoxLayout()
        self.lbl_crs_info = QLabel(tr('lbl_default_crs', self.lang))
        self.btn_select_crs = QPushButton("EPSG:4326") # Default
        self.target_crs_id = "EPSG:4326"
        crs_layout.addWidget(self.lbl_crs_info)
        crs_layout.addWidget(self.btn_select_crs)
        gp_crs.setLayout(crs_layout)
        layout.addWidget(gp_crs)
        
        # Action Buttons
        self.btn_convert = QPushButton(tr('btn_convert', self.lang))
        self.btn_convert.clicked.connect(self._convert_kml)
        self.btn_add_to_map = QPushButton(tr('btn_add_to_map', self.lang))
        self.btn_add_to_map.clicked.connect(self._add_to_map_kml)
        self.btn_add_to_map.setEnabled(False)
        
        layout.addWidget(self.btn_convert)
        layout.addWidget(self.btn_add_to_map)
        layout.addStretch()
        
        self.last_converted_shp = ""

    def _browse_kml(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('lbl_kml_input', self.lang), "", "KML/KMZ (*.kml *.kmz)")
        if path:
            self.txt_kml_in.setText(path)

    def _convert_kml(self):
        kml_path = self.txt_kml_in.text()
        if not kml_path:
            QMessageBox.warning(self, tr('msg_warning', self.lang), tr('msg_kml_no_file', self.lang))
            return
            
        out_path, _ = QFileDialog.getSaveFileName(self, "Save SHP", "", "Shapefile (*.shp)")
        if not out_path: return
        
        converter = KmlToShpConverter()
        ok, msg, layer = converter.convert(kml_path, out_path, self.target_crs_id)
        if ok:
            QMessageBox.information(self, tr('msg_success', self.lang), tr('msg_convert_ok', self.lang))
            self.last_converted_shp = out_path
            self.btn_add_to_map.setEnabled(True)
        else:
            QMessageBox.critical(self, tr('msg_error', self.lang), msg)

    def _add_to_map_kml(self):
        if self.last_converted_shp:
            from qgis.core import QgsVectorLayer, QgsProject
            layer = QgsVectorLayer(self.last_converted_shp, os.path.basename(self.last_converted_shp), "ogr")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)

    def _load_current_layers(self):
        self.cbo_layers.clear()
        self.cbo_layers.addItem("--- Chọn Layer ---", None)
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            self.cbo_layers.addItem(layer.name(), layer.id())

    def _on_layer_changed(self):
        layer_id = self.cbo_layers.currentData()
        if not layer_id: return
        layer = QgsProject.instance().mapLayer(layer_id)
        if layer:
            self.txt_shp.setText(layer.source())
            self._update_field_combos(layer)

    def _update_field_combos(self, layer):
        fields = [f.name() for f in layer.fields()]
        self.cbo_name1.clear()
        self.cbo_name2.clear()
        self.cbo_name1.addItems([''] + fields)
        self.cbo_name2.addItems([''] + fields)
        
        # Update Conditional Field combo
        self.cbo_cond_field.clear()
        self.cbo_cond_field.addItems([''] + fields)
        
        # Update Table
        self.tbl_fields.setRowCount(len(fields))
        for i, f_name in enumerate(fields):
            # Checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            cell_widget = QWidget()
            cw_layout = QHBoxLayout(cell_widget)
            cw_layout.addWidget(chk)
            cw_layout.setAlignment(Qt.AlignCenter)
            cw_layout.setContentsMargins(0,0,0,0)
            self.tbl_fields.setCellWidget(i, 0, cell_widget)
            
            # Field Name (Read-only)
            item_name = QTableWidgetItem(f_name)
            item_name.setFlags(Qt.ItemIsEnabled)
            self.tbl_fields.setItem(i, 1, item_name)
            
            # Alias
            self.tbl_fields.setItem(i, 2, QTableWidgetItem(f_name))
            
            # Suffix (ha, m2...)
            suffix = ""
            if "dien_tich" in f_name.lower() or "area" in f_name.lower():
                suffix = "ha"
            self.tbl_fields.setItem(i, 3, QTableWidgetItem(suffix))

    def _toggle_language(self):
        self.lang = 'en' if self.lang == 'vi' else 'vi'
        self._refresh_ui_text()

    def _refresh_ui_text(self):
        # Update Window Title
        self.setWindowTitle(tr('plugin_title', self.lang))
        
        # Tabs
        self.tabs.setTabText(0, tr('tab_shp2kml', self.lang))
        self.tabs.setTabText(1, tr('tab_kml2shp', self.lang))
        
        # Bottom Buttons
        self.btn_lang.setText(tr('btn_lang', self.lang))
        self.btn_help.setText(tr('tab_help', self.lang))
        self.btn_close.setText(tr('btn_cancel', self.lang))
        
        # SHP -> KML Section Labels
        # Note: In a production app, we'd store references to QGroupBox and QLabel to update them here.
        # For brevity in this step, we focus on the main buttons.
        self.btn_browse_shp.setText(tr('btn_browse', self.lang))
        self.btn_preview.setText(tr('btn_preview', self.lang))
        self.btn_export.setText(tr('btn_export', self.lang))
        
        # KML -> SHP Section Labels
        self.btn_browse_kml.setText(tr('btn_browse', self.lang))
        self.btn_convert.setText(tr('btn_convert', self.lang))
        self.btn_add_to_map.setText(tr('btn_add_to_map', self.lang))
        
        # Cập nhật các GroupBox Title (nếu cần thiết có thể thêm ở đây)

    def _pick_color(self, button):
        color = QColorDialog.getColor()
        if color.isValid():
            button.setText(color.name().upper())
            button.setStyleSheet(f"background-color: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'}")

    def _get_current_config(self):
        """Gather all UI values into a config dict for KmlBuilder."""
        config = self.config.copy()
        config['name_fields'] = {
            'field1': self.cbo_name1.currentText(),
            'field2': self.cbo_name2.currentText(),
            'separator': self.txt_sep.text(),
            'font_size': self.spn_name_size.value()
        }
        
        # Gather table fields
        desc_fields = []
        for i in range(self.tbl_fields.rowCount()):
            chk_widget = self.tbl_fields.cellWidget(i, 0)
            chk = chk_widget.findChild(QCheckBox)
            if chk.isChecked():
                desc_fields.append({
                    'field': self.tbl_fields.item(i, 1).text(),
                    'alias': self.tbl_fields.item(i, 2).text(),
                    'suffix': self.tbl_fields.item(i, 3).text(),
                    'order': i,
                    'enabled': True
                })
        config['description_fields'] = desc_fields
        
        config['polygon_style'] = {
            'border_color': self.btn_border_color.text(),
            'border_width': self.spn_border_width.value(),
            'fill_color': self.btn_fill_color.text(),
            'fill_opacity': self.spn_opacity.value()
        }
        
        config['conditional_colors'] = {
            'enabled': self.chk_cond.isChecked(),
            'field': self.cbo_cond_field.currentText(),
            'rules': [] # Rules would normally be added via another dialog or table
        }
        
        config['header'] = {
            'title': self.txt_header_title.text(),
            'font_size': self.spn_header_size.value(),
            'bold': self.chk_header_bold.isChecked(),
            'bg_color': '#1B5E20', # Default
            'text_color': '#FFFFFF' # Default
        }
        
        config['row_highlights'] = {
            'enabled': self.chk_row_hl.isChecked(),
            'bold': self.chk_hl_bold.isChecked(),
            'italic': self.chk_hl_italic.isChecked(),
            'rules': [] # Simple for now
        }
        return config

    def _preview(self):
        layer_id = self.cbo_layers.currentData()
        if not layer_id: return
        layer = QgsProject.instance().mapLayer(layer_id)
        
        features_data = []
        for feat in layer.getFeatures():
            data = {f.name(): feat[f.name()] for f in layer.fields()}
            features_data.append(data)
            if len(features_data) >= 10: break # Preview only first 10
            
        dlg = PreviewDialog(self._get_current_config(), features_data, self)
        dlg.exec_()

    def _export(self):
        layer_id = self.cbo_layers.currentData()
        if not layer_id:
            QMessageBox.warning(self, tr('msg_warning', self.lang), tr('msg_no_shp', self.lang))
            return
            
        layer = QgsProject.instance().mapLayer(layer_id)
        path, _ = QFileDialog.getSaveFileName(self, "Export KML/KMZ", "", "KML (*.kml);;KMZ (*.kmz)")
        if not path: return
        
        fmt = 'kmz' if path.lower().endswith('.kmz') else 'kml'
        builder = KmlBuilder(self._get_current_config())
        ok, msg = builder.build(layer, path, fmt)
        
        if ok:
            QMessageBox.information(self, tr('msg_success', self.lang), tr('msg_success', self.lang))
        else:
            QMessageBox.critical(self, tr('msg_error', self.lang), msg)

    def _show_help(self):
        from qgis.PyQt.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(tr('help_title', self.lang))
        msg.setTextFormat(Qt.RichText)
        msg.setText(get_help(self.lang))
        msg.exec_()
