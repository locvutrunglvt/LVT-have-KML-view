import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QComboBox, QLineEdit, QPushButton, QSpinBox, 
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QColorDialog, QGroupBox, QTextEdit
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
        
        self.setMinimumSize(600, 750)
        self._setup_ui()
        self._load_current_layers()
        self._refresh_ui_text()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Top Bar: Language & Help
        top_layout = QHBoxLayout()
        self.btn_lang = QPushButton()
        self.btn_lang.setFixedWidth(120)
        self.btn_lang.clicked.connect(self._toggle_language)
        
        self.btn_help = QPushButton()
        self.btn_help.clicked.connect(self._show_help)
        
        top_layout.addWidget(self.btn_lang)
        top_layout.addWidget(self.btn_help)
        top_layout.addStretch()
        self.layout.addLayout(top_layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: SHP -> KML
        self.tab_shp2kml = QWidget()
        self._setup_tab_shp2kml()
        self.tabs.addTab(self.tab_shp2kml, "")
        
        # Tab 2: KML -> SHP
        self.tab_kml2shp = QWidget()
        self._setup_tab_kml2shp()
        self.tabs.addTab(self.tab_kml2shp, "")
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton()
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        self.layout.addLayout(btn_layout)

    def _setup_tab_shp2kml(self):
        layout = QVBoxLayout(self.tab_shp2kml)
        
        # Section 1: IO
        self.gp_io = QGroupBox()
        io_layout = QVBoxLayout()
        
        l_layout = QHBoxLayout()
        l_layout.addWidget(QLabel("Layer:"))
        self.cbo_layers = QComboBox()
        self.cbo_layers.currentIndexChanged.connect(self._on_layer_changed)
        l_layout.addWidget(self.cbo_layers, 1)
        io_layout.addLayout(l_layout)
        
        s_layout = QHBoxLayout()
        s_layout.addWidget(QLabel("SHP:"))
        self.txt_shp = QLineEdit()
        self.btn_browse_shp = QPushButton("...")
        self.btn_browse_shp.clicked.connect(self._browse_shp)
        s_layout.addWidget(self.txt_shp)
        s_layout.addWidget(self.btn_browse_shp)
        io_layout.addLayout(s_layout)
        
        self.gp_io.setLayout(io_layout)
        layout.addWidget(self.gp_io)
        
        # Section 2: Name
        self.gp_name = QGroupBox()
        name_layout = QVBoxLayout()
        
        f_layout = QHBoxLayout()
        f_layout.addWidget(QLabel("F1:"))
        self.cbo_name1 = QComboBox()
        f_layout.addWidget(self.cbo_name1, 1)
        f_layout.addWidget(QLabel("F2:"))
        self.cbo_name2 = QComboBox()
        f_layout.addWidget(self.cbo_name2, 1)
        name_layout.addLayout(f_layout)
        
        sz_layout = QHBoxLayout()
        sz_layout.addWidget(QLabel("Sep:"))
        self.txt_sep = QLineEdit(" - ")
        sz_layout.addWidget(self.txt_sep)
        sz_layout.addWidget(QLabel("Size:"))
        self.spn_name_size = QSpinBox()
        self.spn_name_size.setRange(1, 100)
        self.spn_name_size.setValue(12)
        sz_layout.addWidget(self.spn_name_size)
        name_layout.addLayout(sz_layout)
        
        self.gp_name.setLayout(name_layout)
        layout.addWidget(self.gp_name)

        # Section 3: Description Fields
        self.gp_desc = QGroupBox()
        desc_layout = QVBoxLayout()
        self.tbl_fields = QTableWidget(0, 4)
        self.tbl_fields.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        desc_layout.addWidget(self.tbl_fields)
        self.gp_desc.setLayout(desc_layout)
        layout.addWidget(self.gp_desc)

        # Section 4: Polygon Style
        self.gp_poly = QGroupBox()
        poly_layout = QVBoxLayout()
        
        b_layout = QHBoxLayout()
        b_layout.addWidget(QLabel("Border:"))
        self.btn_border_color = QPushButton("#FF0000")
        self.btn_border_color.clicked.connect(lambda: self._pick_color(self.btn_border_color))
        b_layout.addWidget(self.btn_border_color)
        b_layout.addWidget(QLabel("Width:"))
        self.spn_border_width = QSpinBox()
        self.spn_border_width.setRange(1, 10)
        self.spn_border_width.setValue(2)
        b_layout.addWidget(self.spn_border_width)
        poly_layout.addLayout(b_layout)
        
        f_layout = QHBoxLayout()
        f_layout.addWidget(QLabel("Fill:"))
        self.btn_fill_color = QPushButton("#00FF00")
        self.btn_fill_color.clicked.connect(lambda: self._pick_color(self.btn_fill_color))
        f_layout.addWidget(self.btn_fill_color)
        f_layout.addWidget(QLabel("Opacity:"))
        self.spn_opacity = QSpinBox()
        self.spn_opacity.setRange(0, 100)
        self.spn_opacity.setValue(50)
        f_layout.addWidget(self.spn_opacity)
        poly_layout.addLayout(f_layout)
        
        # Advanced Rules Section 4
        self.chk_cond = QCheckBox()
        poly_layout.addWidget(self.chk_cond)
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel("Field:"))
        self.cbo_cond_field = QComboBox()
        c_layout.addWidget(self.cbo_cond_field, 1)
        self.cbo_operator = QComboBox()
        self.cbo_operator.addItems(["=", ">", "<"])
        c_layout.addWidget(self.cbo_operator)
        self.txt_cond_val = QLineEdit()
        c_layout.addWidget(self.txt_cond_val)
        poly_layout.addLayout(c_layout)
        
        self.gp_poly.setLayout(poly_layout)
        layout.addWidget(self.gp_poly)

        # Section 5: Header & Row Highlight
        self.gp_style_row = QGroupBox()
        style_layout = QVBoxLayout()
        
        # Header config
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Title:"))
        self.txt_header_title = QLineEdit("Thông tin")
        h_layout.addWidget(self.txt_header_title, 1)
        h_layout.addWidget(QLabel("Size:"))
        self.spn_header_size = QSpinBox()
        self.spn_header_size.setValue(14)
        h_layout.addWidget(self.spn_header_size)
        self.chk_header_bold = QCheckBox("Bold")
        self.chk_header_bold.setChecked(True)
        h_layout.addWidget(self.chk_header_bold)
        style_layout.addLayout(h_layout)
        
        # Row Highlight Rules Section 5
        self.chk_row_hl_enable = QCheckBox()
        style_layout.addWidget(self.chk_row_hl_enable)
        
        r_layout = QHBoxLayout()
        r_layout.addWidget(QLabel("Field:"))
        self.cbo_row_field = QComboBox()
        r_layout.addWidget(self.cbo_row_field, 1)
        self.cbo_row_op = QComboBox()
        self.cbo_row_op.addItems(["=", ">", "<"])
        r_layout.addWidget(self.cbo_row_op)
        self.txt_row_val = QLineEdit()
        r_layout.addWidget(self.txt_row_val)
        style_layout.addLayout(r_layout)
        
        opts_layout = QHBoxLayout()
        self.chk_hl_bold = QCheckBox("Bold")
        self.chk_hl_bold.setChecked(True)
        self.chk_hl_italic = QCheckBox("Italic")
        opts_layout.addWidget(self.chk_hl_bold)
        opts_layout.addWidget(self.chk_hl_italic)
        opts_layout.addStretch()
        style_layout.addLayout(opts_layout)
        
        self.gp_style_row.setLayout(style_layout)
        layout.addWidget(self.gp_style_row)
        
        # Action Buttons
        act_layout = QHBoxLayout()
        self.btn_preview = QPushButton()
        self.btn_preview.clicked.connect(self._preview)
        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self._export)
        act_layout.addWidget(self.btn_preview)
        act_layout.addWidget(self.btn_export)
        layout.addLayout(act_layout)

    def _setup_tab_kml2shp(self):
        layout = QVBoxLayout(self.tab_kml2shp)
        
        # Input KML
        in_layout = QHBoxLayout()
        in_layout.addWidget(QLabel("KML/KMZ:"))
        self.txt_kml_input = QLineEdit()
        self.btn_browse_kml = QPushButton("...")
        self.btn_browse_kml.clicked.connect(self._browse_kml)
        in_layout.addWidget(self.txt_kml_input)
        in_layout.addWidget(self.btn_browse_kml)
        layout.addLayout(in_layout)
        
        # Target CRS
        crs_layout = QHBoxLayout()
        crs_layout.addWidget(QLabel("Target CRS:"))
        self.txt_target_crs = QLineEdit("EPSG:4326")
        crs_layout.addWidget(self.txt_target_crs)
        layout.addLayout(crs_layout)
        
        # Actions
        btn_layout = QHBoxLayout()
        self.btn_convert = QPushButton()
        self.btn_convert.clicked.connect(self._convert_kml)
        self.btn_add_to_map = QPushButton()
        self.btn_add_to_map.clicked.connect(self._add_to_map)
        btn_layout.addWidget(self.btn_convert)
        btn_layout.addWidget(self.btn_add_to_map)
        layout.addLayout(btn_layout)
        
        layout.addStretch()

    def _refresh_ui_text(self):
        self.setWindowTitle(tr('plugin_title', self.lang))
        self.btn_lang.setText(tr('btn_lang', self.lang))
        self.btn_help.setText(tr('tab_help', self.lang))
        self.btn_close.setText(tr('btn_cancel', self.lang))
        
        self.tabs.setTabText(0, tr('tab_shp2kml', self.lang))
        self.tabs.setTabText(1, tr('tab_kml2shp', self.lang))
        
        # GroupBoxes
        self.gp_io.setTitle(tr('sec_io', self.lang))
        self.gp_name.setTitle(tr('sec_name', self.lang))
        self.gp_desc.setTitle(tr('sec_desc', self.lang))
        self.gp_poly.setTitle(tr('sec_style', self.lang))
        self.gp_style_row.setTitle(tr('sec_style_row', self.lang))
        
        # Table Headers
        self.tbl_fields.setHorizontalHeaderLabels([
            tr('col_check', self.lang), tr('col_field', self.lang), 
            tr('col_alias', self.lang), tr('col_suffix', self.lang)
        ])
        
        # Specific labels/checkboxes
        self.chk_cond.setText(tr('chk_cond', self.lang))
        self.chk_row_hl_enable.setText(tr('chk_row_hl_enable', self.lang))
        self.chk_header_bold.setText(tr('chk_bold', self.lang))
        self.chk_hl_bold.setText(tr('chk_hl_bold', self.lang))
        self.chk_hl_italic.setText(tr('chk_hl_italic', self.lang))
        
        # Buttons
        self.btn_preview.setText(tr('btn_preview', self.lang))
        self.btn_export.setText(tr('btn_export', self.lang))
        self.btn_convert.setText(tr('btn_convert', self.lang))
        self.btn_add_to_map.setText(tr('btn_add_to_map', self.lang))

    def _toggle_language(self):
        self.lang = 'en' if self.lang == 'vi' else 'vi'
        self._refresh_ui_text()

    def _show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(tr('help_title', self.lang))
        dlg.setMinimumSize(650, 600)
        ly = QVBoxLayout(dlg)
        
        browser = QTextEdit()
        browser.setReadOnly(True)
        
        # Embed author image
        img_path = os.path.join(self.plugin_dir, 'author.png')
        img_url = f"file:///{img_path.replace('\\', '/')}"
        
        author_html = f"""
        <hr>
        <div style="background:#f4f4f4; padding:20px; border-radius:10px; text-align:center; font-family:sans-serif">
            <img src="{img_url}" width="450" style="border:3px solid #fff; box-shadow:0 2px 5px rgba(0,0,0,0.2); border-radius:8px">
            <h2 style="color:#1B5E20; margin:10px 0">Lộc Vũ Trung</h2>
            <p style="font-size:16px; font-weight:bold; color:#333">Chuyên gia Công nghệ GIS & Lâm nghiệp</p>
            <div style="text-align:left; display:inline-block; margin-top:15px; border-top:1px solid #ccc; padding-top:15px; width:80%">
                <p><b>📱 Zalo:</b> 0913 191 178</p>
                <p><b>🌐 Website:</b> <a href="http://locvutrung.lvtcenter.it.com">locvutrung.lvtcenter.it.com</a></p>
                <p><b>🎬 YouTube:</b> <a href="http://youtube.com/@locvutrung">@locvutrung</a></p>
            </div>
            <p style="font-size:12px; color:#666; margin-top:20px"><i>LVT Map Layout v2.0 — Giải pháp bản đồ chuyên nghiệp.</i></p>
        </div>
        """
        browser.setHtml(get_help(self.lang) + author_html)
        ly.addWidget(browser)
        
        btn = QPushButton("OK")
        btn.clicked.connect(dlg.accept)
        ly.addWidget(btn)
        dlg.exec_()

    def _on_layer_changed(self):
        layer_name = self.cbo_layers.currentText()
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if layers:
            layer = layers[0]
            self.txt_shp.setText(layer.source())
            self._update_fields(layer)

    def _update_fields(self, layer):
        fnames = [f.name() for f in layer.fields()]
        self.cbo_name1.clear(); self.cbo_name1.addItems(fnames)
        self.cbo_name2.clear(); self.cbo_name2.addItems(fnames)
        self.cbo_cond_field.clear(); self.cbo_cond_field.addItems(fnames)
        self.cbo_row_field.clear(); self.cbo_row_field.addItems(fnames)
        
        self.tbl_fields.setRowCount(0)
        for i, name in enumerate(fnames):
            self.tbl_fields.insertRow(i)
            chk = QCheckBox(); chk.setChecked(True)
            self.tbl_fields.setCellWidget(i, 0, chk)
            self.tbl_fields.setItem(i, 1, QTableWidgetItem(name))
            self.tbl_fields.setItem(i, 2, QTableWidgetItem(name))
            suffix = ""
            if "dien_tich" in name.lower() or "area" in name.lower():
                suffix = "ha"
            self.tbl_fields.setItem(i, 3, QTableWidgetItem(suffix))

    def _load_current_layers(self):
        self.cbo_layers.clear()
        for layer in QgsProject.instance().mapLayers().values():
            self.cbo_layers.addItem(layer.name())

    def _browse_shp(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Shapefile", "", "Shapefiles (*.shp)")
        if path:
            self.txt_shp.setText(path)
            from qgis.core import QgsVectorLayer
            layer = QgsVectorLayer(path, "temp", "ogr")
            if layer.isValid():
                self._update_fields(layer)

    def _browse_kml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open KML/KMZ", "", "KML/KMZ (*.kml *.kmz)")
        if path:
            self.txt_kml_input.setText(path)

    def _pick_color(self, btn):
        color = QColorDialog.getColor()
        if color.isValid():
            btn.setText(color.name())
            btn.setStyleSheet(f"background-color: {color.name()}")

    def _get_current_config(self):
        desc_fields = []
        for i in range(self.tbl_fields.rowCount()):
            chk = self.tbl_fields.cellWidget(i, 0)
            if chk and chk.isChecked():
                desc_fields.append({
                    'field': self.tbl_fields.item(i, 1).text(),
                    'alias': self.tbl_fields.item(i, 2).text(),
                    'suffix': self.tbl_fields.item(i, 3).text(),
                    'order': i
                })
        
        return {
            'name_fields': {
                'field1': self.cbo_name1.currentText(),
                'field2': self.cbo_name2.currentText(),
                'separator': self.txt_sep.text(),
                'font_size': self.spn_name_size.value()
            },
            'description_fields': desc_fields,
            'polygon_style': {
                'border_color': self.btn_border_color.text(),
                'border_width': self.spn_border_width.value(),
                'fill_color': self.btn_fill_color.text(),
                'fill_opacity': self.spn_opacity.value()
            },
            'conditional_colors': {
                'enabled': self.chk_cond.isChecked(),
                'field': self.cbo_cond_field.currentText(),
                'rules': [{
                    'operator': self.cbo_operator.currentText(),
                    'value': self.txt_cond_val.text(),
                    'border_color': self.btn_border_color.text(),
                    'fill_color': self.btn_fill_color.text()
                }] if self.chk_cond.isChecked() else []
            },
            'header': {
                'title': self.txt_header_title.text(),
                'font_size': self.spn_header_size.value(),
                'bold': self.chk_header_bold.isChecked(),
                'bg_color': '#1B5E20',
                'text_color': '#FFFFFF'
            },
            'row_highlights': {
                'enabled': self.chk_row_hl_enable.isChecked(),
                'rules': [{
                    'field': self.cbo_row_field.currentText(),
                    'operator': self.cbo_row_op.currentText(),
                    'value': self.txt_row_val.text(),
                    'text_color': '#C62828',
                    'bg_color': '#FFF5F5',
                    'bold': self.chk_hl_bold.isChecked(),
                    'italic': self.chk_hl_italic.isChecked()
                }] if self.chk_row_hl_enable.isChecked() else []
            }
        }

    def _preview(self):
        from qgis.core import QgsVectorLayer
        path = self.txt_shp.text()
        if not path:
            QMessageBox.warning(self, tr('msg_warning', self.lang), tr('msg_no_shp', self.lang))
            return
        layer = QgsVectorLayer(path, "preview", "ogr")
        if not layer.isValid():
            # Try getting from cbo_layers
            layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
            if layers: layer = layers[0]
            else: return
            
        feat = next(layer.getFeatures(), None)
        if feat:
            config = self._get_current_config()
            from .html_template import HtmlTemplateBuilder
            html = HtmlTemplateBuilder(config).build({f.name(): feat[f.name()] for f in feat.fields()})
            dlg = PreviewDialog(html, self)
            dlg.exec_()

    def _export(self):
        path = self.txt_shp.text()
        if not path:
            QMessageBox.warning(self, tr('msg_warning', self.lang), tr('msg_no_shp', self.lang))
            return
        
        out_path, _ = QFileDialog.getSaveFileName(self, "Save KML/KMZ", "", "KML (*.kml);;KMZ (*.kmz)")
        if not out_path: return
        
        from qgis.core import QgsVectorLayer
        layer = QgsVectorLayer(path, "export", "ogr")
        if not layer.isValid():
            layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
            if layers: layer = layers[0]
            else: return

        config = self._get_current_config()
        builder = KmlBuilder(config)
        fmt = 'kmz' if out_path.lower().endswith('.kmz') else 'kml'
        success, msg = builder.build(layer, out_path, fmt)
        if success:
            QMessageBox.information(self, tr('msg_success', self.lang), tr('msg_success', self.lang))
        else:
            QMessageBox.critical(self, tr('msg_error', self.lang), msg)

    def _convert_kml(self):
        kml_path = self.txt_kml_input.text()
        if not kml_path:
            QMessageBox.warning(self, tr('msg_warning', self.lang), tr('msg_kml_no_file', self.lang))
            return
        
        out_shp, _ = QFileDialog.getSaveFileName(self, "Save Shapefile", "", "Shapefiles (*.shp)")
        if not out_shp: return
        
        crs_str = self.txt_target_crs.text()
        converter = KmlToShpConverter()
        success, msg = converter.convert(kml_path, out_shp, crs_str)
        if success:
            self.last_converted_shp = out_shp
            QMessageBox.information(self, tr('msg_success', self.lang), tr('msg_convert_ok', self.lang))
        else:
            QMessageBox.critical(self, tr('msg_error', self.lang), msg)

    def _add_to_map(self):
        if hasattr(self, 'last_converted_shp') and os.path.exists(self.last_converted_shp):
            from qgis.core import QgsVectorLayer, QgsProject
            layer = QgsVectorLayer(self.last_converted_shp, os.path.basename(self.last_converted_shp), "ogr")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
            else:
                QMessageBox.critical(self, tr('msg_error', self.lang), "Could not load layer.")
        else:
            QMessageBox.warning(self, tr('msg_warning', self.lang), "No converted SHP found.")
