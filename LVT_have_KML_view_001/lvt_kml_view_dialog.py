import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QComboBox, QLineEdit, QPushButton, QSpinBox, 
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QColorDialog, QGroupBox, QTextEdit,
    QSlider, QRadioButton, QButtonGroup
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QColor
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
        self.lang = 'vi'
        
        self.setMinimumSize(700, 850)
        self._setup_ui()
        self._load_current_layers()
        self._refresh_ui_text()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)
        
        # Top Bar: Language Toggle
        top_layout = QHBoxLayout()
        self.btn_lang = QPushButton()
        self.btn_lang.setFixedWidth(120)
        self.btn_lang.clicked.connect(self._toggle_language)
        top_layout.addWidget(self.btn_lang)
        top_layout.addStretch()
        self.layout.addLayout(top_layout)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: SHP -> KML
        self.tab_shp2kml = QWidget()
        self._setup_tab_shp2kml()
        self.tabs.addTab(self.tab_shp2kml, "SHP → KML")
        
        # Tab 2: KML -> SHP
        self.tab_kml2shp = QWidget()
        self._setup_tab_kml2shp()
        self.tabs.addTab(self.tab_kml2shp, "KML → SHP")
        
        # Tab 3: Hướng dẫn (User Guide)
        self.tab_guide = QWidget()
        self._setup_tab_guide()
        self.tabs.addTab(self.tab_guide, tr('tab_help', self.lang))
        
        # Tab 4: Tác giả (Author)
        self.tab_author = QWidget()
        self._setup_tab_author()
        self.tabs.addTab(self.tab_author, "Tác giả")
        
        # Bottom Buttons Bar
        btn_layout = QHBoxLayout()
        self.btn_save_cfg = QPushButton(tr('btn_save_cfg', self.lang))
        self.btn_save_cfg.setIcon(QIcon(':/images/themes/default/mActionFileSave.svg'))
        self.btn_save_cfg.clicked.connect(self._save_config)
        
        self.btn_load_cfg = QPushButton(tr('btn_load_cfg', self.lang))
        self.btn_load_cfg.setIcon(QIcon(':/images/themes/default/mActionFolder.svg'))
        self.btn_load_cfg.clicked.connect(self._load_config)
        
        self.btn_close = QPushButton(tr('btn_cancel', self.lang))
        self.btn_close.setIcon(QIcon(':/images/themes/default/mActionDelete.svg'))
        self.btn_close.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save_cfg)
        btn_layout.addWidget(self.btn_load_cfg)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        self.layout.addLayout(btn_layout)

    def _setup_tab_shp2kml(self):
        layout = QVBoxLayout(self.tab_shp2kml)
        layout.setSpacing(8)
        
        # 1. Input / Output
        self.gp_io = QGroupBox("1. Input / Output")
        io_layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("SHP:"))
        self.txt_shp = QLineEdit()
        self.btn_browse_shp = QPushButton("Browse...")
        self.btn_browse_shp.clicked.connect(self._browse_shp)
        row1.addWidget(self.txt_shp, 1); row1.addWidget(self.btn_browse_shp)
        row1.addWidget(QLabel("Output:"))
        self.rad_kml = QRadioButton("KML"); self.rad_kmz = QRadioButton("KMZ")
        self.rad_kmz.setChecked(True)
        row1.addWidget(self.rad_kml); row1.addWidget(self.rad_kmz)
        io_layout.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel(tr('lbl_layer', self.lang)))
        self.cbo_layers = QComboBox()
        self.cbo_layers.currentIndexChanged.connect(self._on_layer_changed)
        row2.addWidget(self.cbo_layers, 1)
        io_layout.addLayout(row2)
        self.gp_io.setLayout(io_layout)
        layout.addWidget(self.gp_io)
        
        # 2. Name
        self.gp_name = QGroupBox("2. Name")
        name_layout = QVBoxLayout()
        n_row = QHBoxLayout()
        n_row.addWidget(QLabel("F1:")); self.cbo_name1 = QComboBox(); n_row.addWidget(self.cbo_name1, 1)
        n_row.addWidget(QLabel("Sep:")); self.txt_sep = QLineEdit(" - "); n_row.addWidget(self.txt_sep)
        n_row.addWidget(QLabel("F2:")); self.cbo_name2 = QComboBox(); n_row.addWidget(self.cbo_name2, 1)
        self.lbl_name_preview = QLabel("→ ..."); self.lbl_name_preview.setStyleSheet("color: blue; font-weight: bold")
        n_row.addWidget(self.lbl_name_preview)
        name_layout.addLayout(n_row)
        self.gp_name.setLayout(name_layout)
        layout.addWidget(self.gp_name)

        # 3. Description
        self.gp_desc = QGroupBox("3. Description")
        desc_layout = QVBoxLayout()
        self.tbl_fields = QTableWidget(0, 4)
        self.tbl_fields.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        desc_layout.addWidget(self.tbl_fields)
        self.gp_desc.setLayout(desc_layout)
        layout.addWidget(self.gp_desc)

        # 4. Polygon Style
        self.gp_poly = QGroupBox("4. Polygon Style")
        poly_layout = QVBoxLayout()
        s_row = QHBoxLayout()
        s_row.addWidget(QLabel("Viền:")); self.btn_border_color = QPushButton("#FF0000"); s_row.addWidget(self.btn_border_color)
        s_row.addWidget(QLabel("Dày:")); self.spn_border_width = QSpinBox(); s_row.addWidget(self.spn_border_width)
        s_row.addWidget(QLabel("Nền:")); self.btn_fill_color = QPushButton("#00FF00"); s_row.addWidget(self.btn_fill_color)
        s_row.addWidget(QLabel("Opacity:")); self.sld_opacity = QSlider(Qt.Horizontal); self.sld_opacity.setRange(0, 100); s_row.addWidget(self.sld_opacity)
        self.lbl_opacity_val = QLabel("50%"); s_row.addWidget(self.lbl_opacity_val)
        poly_layout.addLayout(s_row)
        self.chk_cond = QCheckBox("Tô màu theo điều kiện"); poly_layout.addWidget(self.chk_cond)
        self.gp_poly.setLayout(poly_layout)
        layout.addWidget(self.gp_poly)

        # 5. Header_Row Highlight
        self.gp_style_row = QGroupBox("5. Header_Row Highlight")
        style_layout = QVBoxLayout()
        h_row = QHBoxLayout()
        h_row.addWidget(QLabel("Tiêu đề:")); self.txt_header_title = QLineEdit("Thông tin"); h_row.addWidget(self.txt_header_title, 1)
        h_row.addWidget(QLabel("Nền:")); self.btn_h_bg = QPushButton("#1B5E20"); h_row.addWidget(self.btn_h_bg)
        h_row.addWidget(QLabel("Chữ:")); self.btn_h_fg = QPushButton("#FFFFFF"); h_row.addWidget(self.btn_h_fg)
        self.chk_h_bold = QCheckBox("Đậm"); self.chk_h_bold.setChecked(True); h_row.addWidget(self.chk_h_bold)
        style_layout.addLayout(h_row)
        self.chk_row_hl = QCheckBox("Tô màu dòng đặc biệt"); style_layout.addWidget(self.chk_row_hl)
        self.tbl_rules = QTableWidget(0, 5); self.tbl_rules.setHorizontalHeaderLabels(["Field", "Op", "Giá trị", "Màu chữ", "Màu nền"])
        self.tbl_rules.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); style_layout.addWidget(self.tbl_rules)
        r_btns = QHBoxLayout(); self.btn_add_rule = QPushButton("+ Thêm"); self.btn_add_rule.clicked.connect(self._add_rule_row)
        self.btn_del_rule = QPushButton("- Xóa"); self.btn_del_rule.clicked.connect(self._del_rule_row)
        r_btns.addWidget(self.btn_add_rule); r_btns.addWidget(self.btn_del_rule); r_btns.addStretch()
        style_layout.addLayout(r_btns)
        self.gp_style_row.setLayout(style_layout)
        layout.addWidget(self.gp_style_row)
        
        # Action Buttons
        act_layout = QHBoxLayout()
        self.btn_preview = QPushButton(tr('btn_preview', self.lang))
        self.btn_preview.setIcon(QIcon(':/images/themes/default/mActionZoomIn.svg'))
        self.btn_preview.clicked.connect(self._preview)
        self.btn_export = QPushButton(tr('btn_export', self.lang))
        self.btn_export.setIcon(QIcon(':/images/themes/default/mActionFileSaveAs.svg'))
        self.btn_export.clicked.connect(self._export)
        act_layout.addWidget(self.btn_preview); act_layout.addWidget(self.btn_export)
        layout.addLayout(act_layout)

    def _setup_tab_kml2shp(self):
        layout = QVBoxLayout(self.tab_kml2shp)
        layout.addWidget(QLabel("KML/KMZ:"))
        h1 = QHBoxLayout(); self.txt_kml_input = QLineEdit(); self.btn_browse_kml = QPushButton("..."); h1.addWidget(self.txt_kml_input); h1.addWidget(self.btn_browse_kml)
        layout.addLayout(h1)
        layout.addWidget(QLabel("Hệ tọa độ đích:")); self.txt_target_crs = QLineEdit("EPSG:4326"); layout.addWidget(self.txt_target_crs)
        h2 = QHBoxLayout(); self.btn_convert = QPushButton("🔄 Chuyển đổi"); self.btn_add_to_map = QPushButton("🗺 Thêm vào bản đồ")
        h2.addWidget(self.btn_convert); h2.addWidget(self.btn_add_to_map); layout.addLayout(h2); layout.addStretch()

    def _setup_tab_guide(self):
        layout = QVBoxLayout(self.tab_guide)
        self.browser_guide = QTextEdit()
        self.browser_guide.setReadOnly(True)
        layout.addWidget(self.browser_guide)

    def _setup_tab_author(self):
        layout = QVBoxLayout(self.tab_author)
        self.browser_author = QTextEdit()
        self.browser_author.setReadOnly(True)
        layout.addWidget(self.browser_author)

    def _refresh_ui_text(self):
        self.setWindowTitle(tr('plugin_title', self.lang))
        self.btn_lang.setText(tr('btn_lang', self.lang))
        self.btn_save_cfg.setText(tr('btn_save_cfg', self.lang))
        self.btn_load_cfg.setText(tr('btn_load_cfg', self.lang))
        self.btn_close.setText(tr('btn_cancel', self.lang))
        
        self.tabs.setTabText(0, tr('tab_shp2kml', self.lang))
        self.tabs.setTabText(1, tr('tab_kml2shp', self.lang))
        self.tabs.setTabText(2, tr('tab_help', self.lang))
        self.tabs.setTabText(3, "Tác giả")
        
        # Update Guide and Author content
        self.browser_guide.setHtml(get_help(self.lang))
        
        img_path = os.path.join(self.plugin_dir, 'author.png')
        img_url = f"file:///{img_path.replace('\\', '/')}"
        author_html = f"""
        <div style="text-align:center; font-family:sans-serif">
            <img src="{img_url}" width="450">
            <h2 style="color:#1B5E20; margin:10px 0">Lộc Vũ Trung</h2>
            <p style="font-size:16px; font-weight:bold">Chuyên gia Công nghệ GIS & Lâm nghiệp</p>
            <div style="text-align:left; display:inline-block; margin-top:15px; width:80%">
                <p><b>📱 Zalo:</b> 0913 191 178</p>
                <p><b>🌐 Website:</b> <a href="http://locvutrung.lvtcenter.it.com">locvutrung.lvtcenter.it.com</a></p>
                <p><b>🎬 YouTube:</b> <a href="http://youtube.com/@locvutrung">@locvutrung</a></p>
            </div>
            <p style="font-size:12px; color:#666; margin-top:20px"><i>LVT Map Layout v2.0 — Giải pháp bản đồ chuyên nghiệp.</i></p>
        </div>
        """
        self.browser_author.setHtml(author_html)

    def _toggle_language(self):
        self.lang = 'en' if self.lang == 'vi' else 'vi'
        self._refresh_ui_text()

    def _add_rule_row(self):
        row = self.tbl_rules.rowCount(); self.tbl_rules.insertRow(row)
        cb_field = QComboBox(); layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers: cb_field.addItems([f.name() for f in layers[0].fields()])
        self.tbl_rules.setCellWidget(row, 0, cb_field)
        cb_op = QComboBox(); cb_op.addItems(["=", ">", "<"]); self.tbl_rules.setCellWidget(row, 1, cb_op)
        self.tbl_rules.setItem(row, 2, QTableWidgetItem(""))
        btn_txt = QPushButton("#C62828"); btn_txt.clicked.connect(lambda: self._pick_color(btn_txt)); self.tbl_rules.setCellWidget(row, 3, btn_txt)
        btn_bg = QPushButton("#FFF5F5"); btn_bg.clicked.connect(lambda: self._pick_color(btn_bg)); self.tbl_rules.setCellWidget(row, 4, btn_bg)

    def _del_rule_row(self): self.tbl_rules.removeRow(self.tbl_rules.currentRow())

    def _pick_color(self, btn):
        color = QColorDialog.getColor(QColor(btn.text()))
        if color.isValid(): btn.setText(color.name()); btn.setStyleSheet(f"background-color: {color.name()}")

    def _on_layer_changed(self):
        layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers: self.txt_shp.setText(layers[0].source()); self._update_fields(layers[0]); self._update_name_preview()

    def _update_fields(self, layer):
        fnames = [f.name() for f in layer.fields()]
        self.cbo_name1.clear(); self.cbo_name1.addItems(fnames); self.cbo_name2.clear(); self.cbo_name2.addItems(fnames)
        self.tbl_fields.setRowCount(0)
        for i, name in enumerate(fnames):
            self.tbl_fields.insertRow(i); chk = QCheckBox(); chk.setChecked(True); self.tbl_fields.setCellWidget(i, 0, chk)
            self.tbl_fields.setItem(i, 1, QTableWidgetItem(name)); self.tbl_fields.setItem(i, 2, QTableWidgetItem(name))
            self.tbl_fields.setItem(i, 3, QTableWidgetItem("ha" if "dien_tich" in name.lower() or "area" in name.lower() else ""))

    def _update_name_preview(self):
        layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers:
            feat = next(layers[0].getFeatures(), None)
            if feat:
                f1, f2, sep = self.cbo_name1.currentText(), self.cbo_name2.currentText(), self.txt_sep.text()
                v1 = str(feat[f1]) if f1 in feat.fields().names() else "..."
                v2 = str(feat[f2]) if f2 in feat.fields().names() else "..."
                self.lbl_name_preview.setText(f"→ {v1}{sep}{v2}")

    def _load_current_layers(self):
        self.cbo_layers.clear()
        for layer in QgsProject.instance().mapLayers().values(): self.cbo_layers.addItem(layer.name())

    def _browse_shp(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Shapefile", "", "Shapefiles (*.shp)")
        if path:
            self.txt_shp.setText(path)
            from qgis.core import QgsVectorLayer
            layer = QgsVectorLayer(path, "temp", "ogr")
            if layer.isValid(): self._update_fields(layer)

    def _browse_kml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open KML/KMZ", "", "KML/KMZ (*.kml *.kmz)")
        if path: self.txt_kml_input.setText(path)

    def _get_current_config(self):
        rules = []
        for i in range(self.tbl_rules.rowCount()):
            rules.append({
                'field': self.tbl_rules.cellWidget(i, 0).currentText(),
                'operator': self.tbl_rules.cellWidget(i, 1).currentText(),
                'value': self.tbl_rules.item(i, 2).text(),
                'text_color': self.tbl_rules.cellWidget(i, 3).text(),
                'bg_color': self.tbl_rules.cellWidget(i, 4).text(),
                'bold': self.chk_hl_bold.isChecked(), 'italic': self.chk_hl_italic.isChecked()
            })
        desc_fields = []
        for i in range(self.tbl_fields.rowCount()):
            chk = self.tbl_fields.cellWidget(i, 0)
            if chk and chk.isChecked():
                desc_fields.append({'field': self.tbl_fields.item(i, 1).text(), 'alias': self.tbl_fields.item(i, 2).text(), 'suffix': self.tbl_fields.item(i, 3).text(), 'order': i})
        return {
            'name_fields': {'field1': self.cbo_name1.currentText(), 'field2': self.cbo_name2.currentText(), 'separator': self.txt_sep.text(), 'font_size': 12},
            'description_fields': desc_fields,
            'polygon_style': {'border_color': self.btn_border_color.text(), 'border_width': self.spn_border_width.value(), 'fill_color': self.btn_fill_color.text(), 'fill_opacity': self.sld_opacity.value()},
            'header': {'title': self.txt_header_title.text(), 'bg_color': self.btn_h_bg.text(), 'text_color': self.btn_h_fg.text(), 'bold': self.chk_h_bold.isChecked(), 'font_size': self.spn_header_size.value()},
            'row_highlights': {'enabled': self.chk_row_hl.isChecked(), 'rules': rules}
        }

    def _save_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON (*.json)")
        if path: self.config_manager.save_config(self._get_current_config(), path); QMessageBox.information(self, "Success", tr('msg_config_saved', self.lang))

    def _load_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON (*.json)")
        if path:
            cfg = self.config_manager.load_config(path)
            if cfg: QMessageBox.information(self, "Success", tr('msg_config_loaded', self.lang))

    def _preview(self):
        path = self.txt_shp.text()
        if not path: return
        from qgis.core import QgsVectorLayer
        layer = QgsVectorLayer(path, "preview", "ogr")
        if not layer.isValid():
            layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
            if layers: layer = layers[0]
            else: return
        feat = next(layer.getFeatures(), None)
        if feat:
            from .html_template import HtmlTemplateBuilder
            html = HtmlTemplateBuilder(self._get_current_config()).build({f.name(): feat[f.name()] for f in feat.fields()})
            PreviewDialog(html, self).exec_()

    def _export(self):
        path = self.txt_shp.text()
        if not path: return
        out_path, _ = QFileDialog.getSaveFileName(self, "Save KML/KMZ", "", "KML (*.kml);;KMZ (*.kmz)")
        if not out_path: return
        from qgis.core import QgsVectorLayer
        layer = QgsVectorLayer(path, "export", "ogr")
        if not layer.isValid():
            layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
            if layers: layer = layers[0]
            else: return
        builder = KmlBuilder(self._get_current_config())
        success, msg = builder.build(layer, out_path, 'kmz' if out_path.lower().endswith('.kmz') else 'kml')
        if success: QMessageBox.information(self, "Success", tr('msg_success', self.lang))
        else: QMessageBox.critical(self, "Error", msg)

    def _convert_kml(self):
        kml_path = self.txt_kml_input.text()
        if not kml_path: return
        out_shp, _ = QFileDialog.getSaveFileName(self, "Save Shapefile", "", "Shapefiles (*.shp)")
        if not out_shp: return
        success, msg = KmlToShpConverter().convert(kml_path, out_shp, self.txt_target_crs.text())
        if success: self.last_converted_shp = out_shp; QMessageBox.information(self, "Success", tr('msg_convert_ok', self.lang))
        else: QMessageBox.critical(self, "Error", msg)

    def _add_to_map(self):
        if hasattr(self, 'last_converted_shp') and os.path.exists(self.last_converted_shp):
            from qgis.core import QgsVectorLayer, QgsProject
            layer = QgsVectorLayer(self.last_converted_shp, os.path.basename(self.last_converted_shp), "ogr")
            if layer.isValid(): QgsProject.instance().addMapLayer(layer)
