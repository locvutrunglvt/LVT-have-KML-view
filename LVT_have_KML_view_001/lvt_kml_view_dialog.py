import os
import re
from qgis.PyQt import uic, QtCore, QtGui
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QComboBox, QLineEdit, QPushButton, QSpinBox, 
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QColorDialog, QGroupBox, QTextEdit,
    QSlider, QRadioButton, QButtonGroup, QScrollArea, QFrame
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QPoint
from qgis.PyQt.QtGui import QIcon, QColor, QPainter, QPen, QBrush, QPixmap, QPolygon
from qgis.core import QgsProject, QgsVectorLayer

from .i18n import tr, get_help
from .config_manager import ConfigManager
from .kml_builder import KmlBuilder
from .kml_to_shp import KmlToShpConverter
from .html_template import HtmlTemplateBuilder

class LvtKmlViewDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.bg_img = os.path.join(self.plugin_dir, "google_maps_satellite_bg.png")
        self.config_manager = ConfigManager()
        self.lang = 'vi'
        
        self.resize(900, 750) 
        self._setup_ui()
        self._load_current_layers()
        self._refresh_ui_text()
        self._connect_live_preview()
        
        # Connect main buttons
        self.btn_close.clicked.connect(self.close)
        self.btn_save_cfg.clicked.connect(self._save_config)
        self.btn_load_cfg.clicked.connect(self._load_config)
        
        # Trigger read input with a small delay for safety
        QtCore.QTimer.singleShot(1000, self._on_layer_changed)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        left_widget = QWidget(); left_layout = QVBoxLayout(left_widget); scroll.setWidget(left_widget)
        main_layout.addWidget(scroll, 6)

        top_ly = QHBoxLayout()
        self.btn_lang = QPushButton(); self.btn_lang.setFixedWidth(100); self.btn_lang.clicked.connect(self._toggle_language)
        top_ly.addWidget(self.btn_lang); top_ly.addStretch(); left_layout.addLayout(top_ly)

        self.tabs = QTabWidget(); left_layout.addWidget(self.tabs)
        self.tab_shp2kml = QWidget(); self._setup_tab_shp2kml(); self.tabs.addTab(self.tab_shp2kml, "SHP → KML")
        self.tab_kml2shp = QWidget(); self._setup_tab_kml2shp(); self.tabs.addTab(self.tab_kml2shp, "KML → SHP")
        self.tab_guide = QWidget(); self._setup_tab_guide(); self.tabs.addTab(self.tab_guide, tr('tab_help', self.lang))
        self.tab_author = QWidget(); self._setup_tab_author(); self.tabs.addTab(self.tab_author, "Tác giả")

        btn_layout = QHBoxLayout()
        self.btn_save_cfg = QPushButton(tr('btn_save_cfg', self.lang))
        self.btn_load_cfg = QPushButton(tr('btn_load_cfg', self.lang))
        self.btn_close = QPushButton(tr('btn_cancel', self.lang))
        btn_layout.addWidget(self.btn_save_cfg); btn_layout.addWidget(self.btn_load_cfg); btn_layout.addStretch(); btn_layout.addWidget(self.btn_close)
        left_layout.addLayout(btn_layout)

        right_widget = QGroupBox("LIVE PREVIEW"); right_layout = QVBoxLayout(right_widget); main_layout.addWidget(right_widget, 4)
        right_layout.addWidget(QLabel("<b>Polygon Contrast Preview:</b>"))
        self.poly_preview = QFrame(); self.poly_preview.setMinimumHeight(180); self.poly_preview.setFrameStyle(QFrame.StyledPanel)
        self.poly_preview.setStyleSheet(f"background-image: url({self.bg_img.replace('\\', '/')}); background-position: center;")
        self.poly_preview.paintEvent = self._paint_poly_preview; right_layout.addWidget(self.poly_preview)
        right_layout.addWidget(QLabel("<b>Popup Preview:</b>"))
        self.html_preview = QTextEdit(); self.html_preview.setReadOnly(True); right_layout.addWidget(self.html_preview)
        self.btn_export_big = QPushButton("🚀 XUẤT KML / KMZ")
        self.btn_export_big.setMinimumHeight(50); self.btn_export_big.setStyleSheet("background-color: #1B5E20; color: white; font-weight: bold; border-radius: 5px")
        self.btn_export_big.clicked.connect(self._export); right_layout.addWidget(self.btn_export_big)

    def _setup_tab_shp2kml(self):
        layout = QVBoxLayout(self.tab_shp2kml)
        self.gp_io = QGroupBox("1. Input / Output"); io_ly = QVBoxLayout()
        self.txt_shp = QLineEdit(); io_ly.addWidget(QLabel("SHP Source:")); io_ly.addWidget(self.txt_shp)
        r2 = QHBoxLayout(); r2.addWidget(QLabel("Select Layer:")); self.cbo_layers = QComboBox(); r2.addWidget(self.cbo_layers, 1); io_ly.addLayout(r2)
        self.gp_io.setLayout(io_ly); layout.addWidget(self.gp_io)
        self.gp_name = QGroupBox("2. Name Settings"); n_ly = QHBoxLayout()
        self.cbo_name1 = QComboBox(); self.txt_sep = QLineEdit(" - "); self.cbo_name2 = QComboBox()
        n_ly.addWidget(QLabel("F1:")); n_ly.addWidget(self.cbo_name1, 1); n_ly.addWidget(QLabel("Sep:")); n_ly.addWidget(self.txt_sep); n_ly.addWidget(QLabel("F2:")); n_ly.addWidget(self.cbo_name2, 1)
        self.gp_name.setLayout(n_ly); layout.addWidget(self.gp_name)
        self.gp_desc = QGroupBox("3. Popup Info"); d_ly = QVBoxLayout()
        self.tbl_fields = QTableWidget(0, 4); self.tbl_fields.setHorizontalHeaderLabels(["√", "Field", "Alias", "Unit"])
        self.tbl_fields.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); d_ly.addWidget(self.tbl_fields)
        self.gp_desc.setLayout(d_ly); layout.addWidget(self.gp_desc)
        self.gp_poly = QGroupBox("4. Style"); p_ly = QHBoxLayout()
        self.btn_border = QPushButton("#FF0000"); self.spn_width = QSpinBox(); self.btn_fill = QPushButton("#00FF00"); self.sld_op = QSlider(Qt.Horizontal)
        self.sld_op.setRange(0, 100); self.sld_op.setValue(50)
        p_ly.addWidget(QLabel("V:")); p_ly.addWidget(self.btn_border); p_ly.addWidget(QLabel("W:")); p_ly.addWidget(self.spn_width); p_ly.addWidget(QLabel("N:")); p_ly.addWidget(self.btn_fill); p_ly.addWidget(QLabel("Op:")); p_ly.addWidget(self.sld_op)
        self.gp_poly.setLayout(p_ly); layout.addWidget(self.gp_poly)
        self.gp_hl = QGroupBox("5. Conditions"); hl_ly = QVBoxLayout()
        r3 = QHBoxLayout(); self.txt_h_title = QLineEdit("Thông tin"); self.btn_h_bg = QPushButton("#1B5E20"); r3.addWidget(QLabel("Header:")); r3.addWidget(self.txt_h_title, 1); r3.addWidget(self.btn_h_bg)
        hl_ly.addLayout(r3); self.chk_row_hl = QCheckBox("Enable Highlighting"); hl_ly.addWidget(self.chk_row_hl)
        self.tbl_rules = QTableWidget(0, 5); self.tbl_rules.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); hl_ly.addWidget(self.tbl_rules)
        r4 = QHBoxLayout(); btn_add = QPushButton("+ Add Rule"); btn_del = QPushButton("- Del"); btn_add.clicked.connect(self._add_rule); btn_del.clicked.connect(self._del_rule); r4.addWidget(btn_add); r4.addWidget(btn_del); r4.addStretch()
        hl_ly.addLayout(r4); self.gp_hl.setLayout(hl_ly); layout.addWidget(self.gp_hl)

    def _setup_tab_author(self):
        ly = QVBoxLayout(self.tab_author); self.author = QTextEdit(); self.author.setReadOnly(True); ly.addWidget(self.author)

    def _setup_tab_guide(self): 
        ly = QVBoxLayout(self.tab_guide); self.guide = QTextEdit(); self.guide.setReadOnly(True); ly.addWidget(self.guide)

    def _refresh_ui_text(self):
        self.setWindowTitle("LVT have KML view _V011")
        self.btn_lang.setText("🌐 " + ("English" if self.lang == 'vi' else "Tiếng Việt"))
        img_path = os.path.join(self.plugin_dir, 'author.png'); img_url = f"file:///{img_path.replace('\\', '/')}"
        author_html = f"""<div style='font-family:Arial;text-align:center;color:#333'><div style='background:#f4f4f4;padding:20px;border-radius:10px'><img src='{img_url}' width='350'><h1 style='color:#1B5E20'>Lộc Vũ Trung</h1><p style='font-size:18px;font-weight:bold'>Chuyên gia Công nghệ GIS & Lâm nghiệp</p><hr><div style='text-align:left;display:inline-block;width:80%'><b>📱 Zalo:</b> 0913 191 178<br><b>🌐 Website:</b> locvutrung.lvtcenter.it.com<br><b>🎬 YouTube:</b> youtube.com/@locvutrung<br></div><div style='margin-top:15px;background:#fff;padding:10px;border-radius:5px;border-left:5px solid #1B5E20;text-align:left'><b>Phạm vi chuyên môn:</b><br>• FSC/CoC | • EUDR | • Webapp<br>• Appsheet | • QGIS | • Lâm sinh | • DATA</div></div></div>"""
        self.author.setHtml(author_html); self.guide.setHtml(get_help(self.lang))

    def _load_current_layers(self):
        self.cbo_layers.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer): self.cbo_layers.addItem(layer.name())

    def _connect_live_preview(self):
        for w in [self.cbo_layers, self.cbo_name1, self.cbo_name2, self.txt_sep, self.sld_op, self.spn_width, self.txt_h_title, self.chk_row_hl]:
            if hasattr(w, 'currentIndexChanged'): w.currentIndexChanged.connect(self._trigger_refresh)
            if hasattr(w, 'textChanged'): w.textChanged.connect(self._trigger_refresh)
            if hasattr(w, 'valueChanged'): w.valueChanged.connect(self._trigger_refresh)
            if hasattr(w, 'toggled'): w.toggled.connect(self._trigger_refresh)
        self.btn_border.clicked.connect(lambda: (self._pick_color(self.btn_border), self._trigger_refresh()))
        self.btn_fill.clicked.connect(lambda: (self._pick_color(self.btn_fill), self._trigger_refresh()))
        self.btn_h_bg.clicked.connect(lambda: (self._pick_color(self.btn_h_bg), self._trigger_refresh()))
        self.tbl_fields.itemChanged.connect(self._trigger_refresh); self.tbl_rules.itemChanged.connect(self._trigger_refresh)

    def _trigger_refresh(self):
        self.poly_preview.update()
        try: self._update_popup_preview()
        except: pass

    def _paint_poly_preview(self, event):
        painter = QPainter(self.poly_preview); painter.setRenderHint(QPainter.Antialiasing)
        b_c = QColor(self.btn_border.text()); f_c = QColor(self.btn_fill.text()); w = self.spn_width.value()
        f_c.setAlpha(int(self.sld_op.value() * 2.55)); painter.setPen(QPen(b_c, w)); painter.setBrush(QBrush(f_c))
        pts = [QPoint(175, 40), QPoint(300, 100), QPoint(175, 160), QPoint(50, 100)]; painter.drawPolygon(QPolygon(pts))

    def _on_layer_changed(self):
        layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers: self.txt_shp.setText(layers[0].source()); self._update_fields(layers[0]); self._trigger_refresh()

    def _update_fields(self, layer):
        self.tbl_fields.blockSignals(True); fnames = [f.name() for f in layer.fields()]
        self.cbo_name1.clear(); self.cbo_name1.addItems(fnames); self.cbo_name2.clear(); self.cbo_name2.addItems(fnames)
        self.tbl_fields.setRowCount(0)
        for i, name in enumerate(fnames):
            self.tbl_fields.insertRow(i); chk = QCheckBox(); chk.setChecked(True); self.tbl_fields.setCellWidget(i, 0, chk)
            self.tbl_fields.setItem(i, 1, QTableWidgetItem(name)); self.tbl_fields.setItem(i, 2, QTableWidgetItem(name)); self.tbl_fields.setItem(i, 3, QTableWidgetItem(""))
        self.tbl_fields.blockSignals(False); self._trigger_refresh()

    def _update_popup_preview(self):
        layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers:
            feat = next(layers[0].getFeatures(), None)
            if feat:
                cfg = self._get_current_config()
                if cfg: html = HtmlTemplateBuilder(cfg).build({f.name(): feat[f.name()] for f in feat.fields()}); self.html_preview.setHtml(html)

    def _get_current_config(self):
        rules = []
        for i in range(self.tbl_rules.rowCount()):
            rules.append({'field': self.tbl_rules.cellWidget(i,0).currentText() if self.tbl_rules.cellWidget(i,0) else "", 'operator': self.tbl_rules.cellWidget(i,1).currentText() if self.tbl_rules.cellWidget(i,1) else "=", 'value': self.tbl_rules.item(i,2).text() if self.tbl_rules.item(i,2) else "", 'text_color': self.tbl_rules.cellWidget(i,3).text() if self.tbl_rules.cellWidget(i,3) else "#000", 'bg_color': self.tbl_rules.cellWidget(i,4).text() if self.tbl_rules.cellWidget(i,4) else "#fff", 'bold': True, 'italic': False})
        df = []
        for i in range(self.tbl_fields.rowCount()):
            chk = self.tbl_fields.cellWidget(i,0)
            if chk and chk.isChecked():
                f_item = self.tbl_fields.item(i,1); a_item = self.tbl_fields.item(i,2); s_item = self.tbl_fields.item(i,3)
                if f_item and a_item: df.append({'field': f_item.text(), 'alias': a_item.text(), 'suffix': s_item.text() if s_item else "", 'order': i})
        return {'name_fields': {'field1': self.cbo_name1.currentText(), 'field2': self.cbo_name2.currentText(), 'separator': self.txt_sep.text(), 'font_size': 12}, 'description_fields': df, 'polygon_style': {'border_color': self.btn_border.text(), 'border_width': self.spn_width.value(), 'fill_color': self.btn_fill.text(), 'fill_opacity': self.sld_op.value()}, 'header': {'title': self.txt_h_title.text(), 'bg_color': self.btn_h_bg.text(), 'text_color': "#FFFFFF", 'bold': True, 'font_size': 14}, 'row_highlights': {'enabled': self.chk_row_hl.isChecked(), 'rules': rules}}

    def _export(self):
        layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers:
            out_path, _ = QFileDialog.getSaveFileName(self, "Save KML/KMZ", "", "KML (*.kml);;KMZ (*.kmz)")
            if out_path:
                builder = KmlBuilder(self._get_current_config()); builder.build(layers[0], out_path, 'kmz' if out_path.lower().endswith('.kmz') else 'kml')
                QMessageBox.information(self, "Success", tr('msg_success', self.lang))

    def _toggle_language(self): self.lang = 'en' if self.lang == 'vi' else 'vi'; self._refresh_ui_text(); self._trigger_refresh()
    def _pick_color(self, btn):
        c = QColorDialog.getColor(QColor(btn.text())); 
        if c.isValid(): btn.setText(c.name()); btn.setStyleSheet(f"background-color: {c.name()}")
    def _add_rule(self):
        r = self.tbl_rules.rowCount(); self.tbl_rules.insertRow(r)
        cb = QComboBox(); layers = QgsProject.instance().mapLayersByName(self.cbo_layers.currentText())
        if layers: cb.addItems([f.name() for f in layers[0].fields()])
        self.tbl_rules.setCellWidget(r, 0, cb); cb_op = QComboBox(); cb_op.addItems(["=", ">", "<"]); self.tbl_rules.setCellWidget(r, 1, cb_op)
        self.tbl_rules.setItem(r, 2, QTableWidgetItem("")); self.tbl_rules.setCellWidget(r, 3, QPushButton("#C62828")); self.tbl_rules.setCellWidget(r, 4, QPushButton("#FFF5F5"))
    def _del_rule(self): self.tbl_rules.removeRow(self.tbl_rules.currentRow())
    def _save_config(self): pass
    def _load_config(self): pass
    def _setup_tab_kml2shp(self):
        ly = QVBoxLayout(self.tab_kml2shp); ly.addWidget(QLabel("KML Source:")); self.txt_kml_in = QLineEdit(); ly.addWidget(self.txt_kml_in)
        ly.addWidget(QLabel("Target CRS:")); self.txt_crs = QLineEdit("EPSG:4326"); ly.addWidget(self.txt_crs); btn = QPushButton("🔄 EXTRACT NOW"); btn.clicked.connect(self._convert_kml); ly.addWidget(btn); ly.addStretch()
    def _convert_kml(self): pass
