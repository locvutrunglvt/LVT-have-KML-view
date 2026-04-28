"""Main dialog for LVT have KML view plugin."""
import os
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QSlider, QCheckBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QRadioButton, QButtonGroup,
    QColorDialog, QHeaderView, QMessageBox, QAbstractItemView
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsVectorLayer
from .config_manager import ConfigManager
from .kml_builder import KmlBuilder
from .preview_widget import PreviewDialog


class LvtKmlViewDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.layer = None
        self.field_names = []
        self.config_mgr = ConfigManager()
        self.setWindowTitle('LVT have KML view')
        self.setMinimumSize(700, 780)
        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)

        # Section 1 - Input/Output
        root.addWidget(self._build_io_section())
        # Section 2 - Name
        root.addWidget(self._build_name_section())
        # Section 3 - Description fields
        root.addWidget(self._build_desc_section())
        # Section 4 - Polygon style
        root.addWidget(self._build_style_section())
        # Section 5 - Header + Row highlight
        root.addWidget(self._build_header_section())
        # Buttons
        root.addLayout(self._build_buttons())

    # ── Section 1: Input / Output ────────────────────────────────────
    def _build_io_section(self):
        grp = QGroupBox('1. Input / Output')
        lay = QHBoxLayout(grp)

        lay.addWidget(QLabel('SHP:'))
        self.txt_shp = QLineEdit()
        self.txt_shp.setReadOnly(True)
        lay.addWidget(self.txt_shp, 3)
        btn = QPushButton('Browse...')
        btn.clicked.connect(self._browse_shp)
        lay.addWidget(btn)

        lay.addWidget(QLabel('  Output:'))
        self.rb_kml = QRadioButton('KML')
        self.rb_kmz = QRadioButton('KMZ')
        self.rb_kml.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self.rb_kml)
        bg.addButton(self.rb_kmz)
        lay.addWidget(self.rb_kml)
        lay.addWidget(self.rb_kmz)
        return grp

    # ── Section 2: Name ──────────────────────────────────────────────
    def _build_name_section(self):
        grp = QGroupBox('2. Name (Label trên bản đồ)')
        lay = QHBoxLayout(grp)

        lay.addWidget(QLabel('Field 1:'))
        self.cmb_name1 = QComboBox()
        lay.addWidget(self.cmb_name1, 2)

        lay.addWidget(QLabel('Separator:'))
        self.cmb_sep = QComboBox()
        self.cmb_sep.setEditable(True)
        self.cmb_sep.addItems([' - ', ' , ', ' / ', ' _ '])
        lay.addWidget(self.cmb_sep, 1)

        lay.addWidget(QLabel('Field 2:'))
        self.cmb_name2 = QComboBox()
        self.cmb_name2.addItem('(none)')
        lay.addWidget(self.cmb_name2, 2)

        self.lbl_name_preview = QLabel('')
        self.lbl_name_preview.setStyleSheet('color:#1565C0;font-weight:bold')
        lay.addWidget(self.lbl_name_preview, 2)
        self.cmb_name1.currentIndexChanged.connect(self._update_name_preview)
        self.cmb_name2.currentIndexChanged.connect(self._update_name_preview)
        self.cmb_sep.currentTextChanged.connect(self._update_name_preview)
        return grp

    # ── Section 3: Description Fields ────────────────────────────────
    def _build_desc_section(self):
        grp = QGroupBox('3. Description (Popup Fields + Alias)')
        lay = QVBoxLayout(grp)

        self.tbl_fields = QTableWidget(0, 3)
        self.tbl_fields.setHorizontalHeaderLabels(['☑', 'Field gốc', 'Alias hiển thị'])
        hdr = self.tbl_fields.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_fields.setColumnWidth(0, 30)
        self.tbl_fields.setSelectionBehavior(QAbstractItemView.SelectRows)
        lay.addWidget(self.tbl_fields)

        btn_lay = QHBoxLayout()
        btn_up = QPushButton('▲ Lên')
        btn_up.clicked.connect(self._move_field_up)
        btn_down = QPushButton('▼ Xuống')
        btn_down.clicked.connect(self._move_field_down)
        btn_lay.addWidget(btn_up)
        btn_lay.addWidget(btn_down)
        btn_lay.addStretch()
        lay.addLayout(btn_lay)
        return grp

    # ── Section 4: Polygon Style ─────────────────────────────────────
    def _build_style_section(self):
        grp = QGroupBox('4. Polygon Style')
        lay = QVBoxLayout(grp)

        # Border + Fill row
        r1 = QHBoxLayout()
        r1.addWidget(QLabel('Viền:'))
        self.btn_border_color = QPushButton()
        self.btn_border_color.setFixedSize(28, 28)
        self._set_btn_color(self.btn_border_color, '#FF0000')
        self.btn_border_color.clicked.connect(lambda: self._pick_color(self.btn_border_color))
        r1.addWidget(self.btn_border_color)
        r1.addWidget(QLabel('Dày:'))
        self.spn_border = QSpinBox()
        self.spn_border.setRange(1, 5)
        self.spn_border.setValue(2)
        r1.addWidget(self.spn_border)

        r1.addWidget(QLabel('   Nền:'))
        self.btn_fill_color = QPushButton()
        self.btn_fill_color.setFixedSize(28, 28)
        self._set_btn_color(self.btn_fill_color, '#00FF00')
        self.btn_fill_color.clicked.connect(lambda: self._pick_color(self.btn_fill_color))
        r1.addWidget(self.btn_fill_color)
        r1.addWidget(QLabel('Opacity:'))
        self.sld_opacity = QSlider(Qt.Horizontal)
        self.sld_opacity.setRange(0, 100)
        self.sld_opacity.setValue(50)
        r1.addWidget(self.sld_opacity)
        self.lbl_opacity = QLabel('50%')
        self.sld_opacity.valueChanged.connect(lambda v: self.lbl_opacity.setText(f'{v}%'))
        r1.addWidget(self.lbl_opacity)
        r1.addStretch()
        lay.addLayout(r1)

        # Conditional color
        self.chk_cond = QCheckBox('Tô màu theo điều kiện')
        lay.addWidget(self.chk_cond)

        self.cond_widget = QGroupBox()
        cond_lay = QVBoxLayout(self.cond_widget)
        cf = QHBoxLayout()
        cf.addWidget(QLabel('Field:'))
        self.cmb_cond_field = QComboBox()
        cf.addWidget(self.cmb_cond_field, 2)
        cf.addStretch()
        cond_lay.addLayout(cf)

        self.tbl_cond = QTableWidget(0, 5)
        self.tbl_cond.setHorizontalHeaderLabels(['Operator', 'Giá trị', 'Màu fill', 'Màu viền', ''])
        self.tbl_cond.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        cond_lay.addWidget(self.tbl_cond)

        cb = QHBoxLayout()
        btn_add_rule = QPushButton('+ Thêm')
        btn_add_rule.clicked.connect(self._add_cond_rule)
        btn_del_rule = QPushButton('- Xóa')
        btn_del_rule.clicked.connect(self._del_cond_rule)
        cb.addWidget(btn_add_rule)
        cb.addWidget(btn_del_rule)
        cb.addStretch()
        cond_lay.addLayout(cb)

        self.cond_widget.setVisible(False)
        self.chk_cond.toggled.connect(self.cond_widget.setVisible)
        lay.addWidget(self.cond_widget)
        return grp

    # ── Section 5: Header + Row Highlight ────────────────────────────
    def _build_header_section(self):
        grp = QGroupBox('5. Header & Row Highlight')
        lay = QVBoxLayout(grp)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel('Tiêu đề:'))
        self.txt_header = QLineEdit('Thông tin')
        r1.addWidget(self.txt_header, 3)
        r1.addWidget(QLabel('Nền:'))
        self.btn_hdr_bg = QPushButton()
        self.btn_hdr_bg.setFixedSize(28, 28)
        self._set_btn_color(self.btn_hdr_bg, '#1B5E20')
        self.btn_hdr_bg.clicked.connect(lambda: self._pick_color(self.btn_hdr_bg))
        r1.addWidget(self.btn_hdr_bg)
        r1.addWidget(QLabel('Chữ:'))
        self.btn_hdr_fg = QPushButton()
        self.btn_hdr_fg.setFixedSize(28, 28)
        self._set_btn_color(self.btn_hdr_fg, '#FFFFFF')
        self.btn_hdr_fg.clicked.connect(lambda: self._pick_color(self.btn_hdr_fg))
        r1.addWidget(self.btn_hdr_fg)
        self.chk_bold = QCheckBox('Đậm')
        self.chk_bold.setChecked(True)
        r1.addWidget(self.chk_bold)
        lay.addLayout(r1)

        # Row highlight
        self.chk_row_hl = QCheckBox('Tô màu dòng đặc biệt')
        lay.addWidget(self.chk_row_hl)
        self.row_hl_widget = QGroupBox()
        rhl = QVBoxLayout(self.row_hl_widget)
        self.tbl_rowhl = QTableWidget(0, 6)
        self.tbl_rowhl.setHorizontalHeaderLabels(
            ['Field', 'Op', 'Giá trị', 'Màu chữ', 'Màu nền', ''])
        self.tbl_rowhl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rhl.addWidget(self.tbl_rowhl)
        rb = QHBoxLayout()
        btn_ar = QPushButton('+ Thêm')
        btn_ar.clicked.connect(self._add_rowhl_rule)
        btn_dr = QPushButton('- Xóa')
        btn_dr.clicked.connect(self._del_rowhl_rule)
        rb.addWidget(btn_ar)
        rb.addWidget(btn_dr)
        rb.addStretch()
        rhl.addLayout(rb)
        self.row_hl_widget.setVisible(False)
        self.chk_row_hl.toggled.connect(self.row_hl_widget.setVisible)
        lay.addWidget(self.row_hl_widget)
        return grp

    # ── Action Buttons ───────────────────────────────────────────────
    def _build_buttons(self):
        lay = QHBoxLayout()
        for text, slot in [
            ('💾 Save Config', self._save_config),
            ('📂 Load Config', self._load_config),
            ('👁 Preview', self._preview),
            ('📤 Export', self._export),
            ('❌ Cancel', self.reject)
        ]:
            b = QPushButton(text)
            b.setStyleSheet('padding:8px 14px;font-size:12px')
            b.clicked.connect(slot)
            lay.addWidget(b)
        return lay

    # ── SHP Loading ──────────────────────────────────────────────────
    def _browse_shp(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Chọn Shapefile', '', 'Shapefile (*.shp)')
        if not path:
            return
        self.txt_shp.setText(path)
        self.layer = QgsVectorLayer(path, os.path.basename(path), 'ogr')
        if not self.layer.isValid():
            QMessageBox.critical(self, 'Lỗi', 'Không thể đọc Shapefile!')
            return
        self.field_names = [f.name() for f in self.layer.fields()]
        self._populate_combos()
        self._populate_field_table()

    def _populate_combos(self):
        for cmb in [self.cmb_name1, self.cmb_name2, self.cmb_cond_field]:
            cmb.clear()
        self.cmb_name2.addItem('(none)')
        for fn in self.field_names:
            self.cmb_name1.addItem(fn)
            self.cmb_name2.addItem(fn)
            self.cmb_cond_field.addItem(fn)

    def _populate_field_table(self):
        self.tbl_fields.setRowCount(len(self.field_names))
        for i, fn in enumerate(self.field_names):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Checked)
            self.tbl_fields.setItem(i, 0, chk)
            item_field = QTableWidgetItem(fn)
            item_field.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.tbl_fields.setItem(i, 1, item_field)
            self.tbl_fields.setItem(i, 2, QTableWidgetItem(fn))

    # ── Field reorder ────────────────────────────────────────────────
    def _move_field_up(self):
        row = self.tbl_fields.currentRow()
        if row <= 0:
            return
        self._swap_rows(self.tbl_fields, row, row - 1)
        self.tbl_fields.setCurrentCell(row - 1, 0)

    def _move_field_down(self):
        row = self.tbl_fields.currentRow()
        if row < 0 or row >= self.tbl_fields.rowCount() - 1:
            return
        self._swap_rows(self.tbl_fields, row, row + 1)
        self.tbl_fields.setCurrentCell(row + 1, 0)

    @staticmethod
    def _swap_rows(tbl, a, b):
        for col in range(tbl.columnCount()):
            ia = tbl.takeItem(a, col)
            ib = tbl.takeItem(b, col)
            tbl.setItem(a, col, ib)
            tbl.setItem(b, col, ia)

    # ── Conditional color rules ──────────────────────────────────────
    def _add_cond_rule(self):
        r = self.tbl_cond.rowCount()
        self.tbl_cond.insertRow(r)
        op = QComboBox()
        op.addItems(['=', '>', '<'])
        self.tbl_cond.setCellWidget(r, 0, op)
        self.tbl_cond.setItem(r, 1, QTableWidgetItem(''))
        bf = QPushButton()
        self._set_btn_color(bf, '#FF0000')
        bf.setFixedSize(26, 26)
        bf.clicked.connect(lambda: self._pick_color(bf))
        self.tbl_cond.setCellWidget(r, 2, bf)
        bb = QPushButton()
        self._set_btn_color(bb, '#CC0000')
        bb.setFixedSize(26, 26)
        bb.clicked.connect(lambda: self._pick_color(bb))
        self.tbl_cond.setCellWidget(r, 3, bb)

    def _del_cond_rule(self):
        r = self.tbl_cond.currentRow()
        if r >= 0:
            self.tbl_cond.removeRow(r)

    # ── Row highlight rules ──────────────────────────────────────────
    def _add_rowhl_rule(self):
        r = self.tbl_rowhl.rowCount()
        self.tbl_rowhl.insertRow(r)
        cmb_f = QComboBox()
        cmb_f.addItems(self.field_names)
        self.tbl_rowhl.setCellWidget(r, 0, cmb_f)
        op = QComboBox()
        op.addItems(['=', '>', '<'])
        self.tbl_rowhl.setCellWidget(r, 1, op)
        self.tbl_rowhl.setItem(r, 2, QTableWidgetItem(''))
        for col, clr in [(3, '#C62828'), (4, '#FFF5F5')]:
            b = QPushButton()
            self._set_btn_color(b, clr)
            b.setFixedSize(26, 26)
            b.clicked.connect(lambda checked, btn=b: self._pick_color(btn))
            self.tbl_rowhl.setCellWidget(r, col, b)

    def _del_rowhl_rule(self):
        r = self.tbl_rowhl.currentRow()
        if r >= 0:
            self.tbl_rowhl.removeRow(r)

    # ── Color picker helper ──────────────────────────────────────────
    def _pick_color(self, btn):
        c = QColorDialog.getColor(QColor(btn.property('hex_color') or '#000000'), self)
        if c.isValid():
            self._set_btn_color(btn, c.name())

    @staticmethod
    def _set_btn_color(btn, hex_color):
        btn.setStyleSheet(f'background-color:{hex_color};border:1px solid #888')
        btn.setProperty('hex_color', hex_color)

    # ── Name preview ─────────────────────────────────────────────────
    def _update_name_preview(self):
        if not self.layer:
            return
        feat = next(self.layer.getFeatures(), None)
        if not feat:
            return
        f1 = self.cmb_name1.currentText()
        f2 = self.cmb_name2.currentText()
        sep = self.cmb_sep.currentText()
        v1 = str(feat[f1]) if f1 and f1 in self.field_names else ''
        v2 = str(feat[f2]) if f2 and f2 != '(none)' and f2 in self.field_names else ''
        if v1 and v2:
            self.lbl_name_preview.setText(f'→ {v1}{sep}{v2}')
        else:
            self.lbl_name_preview.setText(f'→ {v1 or v2}')

    # ── Build config dict ────────────────────────────────────────────
    def _gather_config(self):
        cfg = self.config_mgr.get_default_config()
        cfg['name_fields'] = {
            'field1': self.cmb_name1.currentText(),
            'field2': self.cmb_name2.currentText() if self.cmb_name2.currentText() != '(none)' else '',
            'separator': self.cmb_sep.currentText()
        }
        # Description fields
        desc = []
        for i in range(self.tbl_fields.rowCount()):
            chk = self.tbl_fields.item(i, 0)
            desc.append({
                'field': self.tbl_fields.item(i, 1).text(),
                'alias': self.tbl_fields.item(i, 2).text(),
                'enabled': chk.checkState() == Qt.Checked,
                'order': i
            })
        cfg['description_fields'] = desc
        # Polygon style
        cfg['polygon_style'] = {
            'border_color': self.btn_border_color.property('hex_color') or '#FF0000',
            'border_width': self.spn_border.value(),
            'fill_color': self.btn_fill_color.property('hex_color') or '#00FF00',
            'fill_opacity': self.sld_opacity.value()
        }
        # Conditional colors
        rules = []
        for i in range(self.tbl_cond.rowCount()):
            op_w = self.tbl_cond.cellWidget(i, 0)
            val_item = self.tbl_cond.item(i, 1)
            fc = self.tbl_cond.cellWidget(i, 2)
            bc = self.tbl_cond.cellWidget(i, 3)
            rules.append({
                'operator': op_w.currentText() if op_w else '=',
                'value': val_item.text() if val_item else '',
                'fill_color': fc.property('hex_color') if fc else '#FF0000',
                'border_color': bc.property('hex_color') if bc else '#CC0000'
            })
        cfg['conditional_colors'] = {
            'enabled': self.chk_cond.isChecked(),
            'field': self.cmb_cond_field.currentText(),
            'rules': rules
        }
        # Header
        cfg['header'] = {
            'title': self.txt_header.text(),
            'bg_color': self.btn_hdr_bg.property('hex_color') or '#1B5E20',
            'text_color': self.btn_hdr_fg.property('hex_color') or '#FFFFFF',
            'bold': self.chk_bold.isChecked()
        }
        # Row highlights
        rh_rules = []
        for i in range(self.tbl_rowhl.rowCount()):
            fw = self.tbl_rowhl.cellWidget(i, 0)
            ow = self.tbl_rowhl.cellWidget(i, 1)
            vi = self.tbl_rowhl.item(i, 2)
            tc = self.tbl_rowhl.cellWidget(i, 3)
            bc = self.tbl_rowhl.cellWidget(i, 4)
            rh_rules.append({
                'field': fw.currentText() if fw else '',
                'operator': ow.currentText() if ow else '=',
                'value': vi.text() if vi else '',
                'text_color': tc.property('hex_color') if tc else '#C62828',
                'bg_color': bc.property('hex_color') if bc else '#FFF5F5'
            })
        cfg['row_highlights'] = {'enabled': self.chk_row_hl.isChecked(), 'rules': rh_rules}
        return cfg

    # ── Actions ──────────────────────────────────────────────────────
    def _get_features_data(self):
        data = []
        for feat in self.layer.getFeatures():
            d = {}
            for f in feat.fields():
                d[f.name()] = feat[f.name()]
            data.append(d)
        return data

    def _preview(self):
        if not self.layer:
            QMessageBox.warning(self, 'Cảnh báo', 'Vui lòng chọn Shapefile trước!')
            return
        cfg = self._gather_config()
        data = self._get_features_data()
        dlg = PreviewDialog(cfg, data, self)
        dlg.exec_()

    def _export(self):
        if not self.layer:
            QMessageBox.warning(self, 'Cảnh báo', 'Vui lòng chọn Shapefile trước!')
            return
        fmt = 'kmz' if self.rb_kmz.isChecked() else 'kml'
        ext = f'*.{fmt}'
        path, _ = QFileDialog.getSaveFileName(self, f'Lưu file {fmt.upper()}', '', f'{fmt.upper()} ({ext})')
        if not path:
            return
        cfg = self._gather_config()
        builder = KmlBuilder(cfg)
        ok, msg = builder.build(self.layer, path, fmt)
        if ok:
            QMessageBox.information(self, 'Thành công', msg)
        else:
            QMessageBox.critical(self, 'Lỗi', msg)

    def _save_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Lưu cấu hình', self.config_mgr.config_dir, 'JSON (*.json)')
        if path:
            ok, msg = self.config_mgr.save(self._gather_config(), path)
            QMessageBox.information(self, 'Config', msg)

    def _load_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Nạp cấu hình', self.config_mgr.config_dir, 'JSON (*.json)')
        if not path:
            return
        cfg, msg = self.config_mgr.load(path)
        if cfg is None:
            QMessageBox.critical(self, 'Lỗi', msg)
            return
        self._apply_config(cfg)
        QMessageBox.information(self, 'Config', 'Đã nạp cấu hình!')

    def _apply_config(self, cfg):
        nf = cfg.get('name_fields', {})
        idx1 = self.cmb_name1.findText(nf.get('field1', ''))
        if idx1 >= 0:
            self.cmb_name1.setCurrentIndex(idx1)
        f2 = nf.get('field2', '')
        idx2 = self.cmb_name2.findText(f2) if f2 else 0
        self.cmb_name2.setCurrentIndex(max(0, idx2))
        self.cmb_sep.setCurrentText(nf.get('separator', ' - '))

        # Description fields
        for df in cfg.get('description_fields', []):
            for i in range(self.tbl_fields.rowCount()):
                if self.tbl_fields.item(i, 1).text() == df.get('field'):
                    self.tbl_fields.item(i, 0).setCheckState(
                        Qt.Checked if df.get('enabled', True) else Qt.Unchecked)
                    self.tbl_fields.item(i, 2).setText(df.get('alias', ''))

        # Polygon style
        ps = cfg.get('polygon_style', {})
        self._set_btn_color(self.btn_border_color, ps.get('border_color', '#FF0000'))
        self.spn_border.setValue(ps.get('border_width', 2))
        self._set_btn_color(self.btn_fill_color, ps.get('fill_color', '#00FF00'))
        self.sld_opacity.setValue(ps.get('fill_opacity', 50))

        # Header
        hdr = cfg.get('header', {})
        self.txt_header.setText(hdr.get('title', 'Thông tin'))
        self._set_btn_color(self.btn_hdr_bg, hdr.get('bg_color', '#1B5E20'))
        self._set_btn_color(self.btn_hdr_fg, hdr.get('text_color', '#FFFFFF'))
        self.chk_bold.setChecked(hdr.get('bold', True))
