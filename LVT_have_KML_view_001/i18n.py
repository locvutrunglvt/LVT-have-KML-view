"""Internationalization: English / Vietnamese translations."""

LANG_VI = 'vi'
LANG_EN = 'en'

T = {
    'plugin_title': {'vi': 'LVT have KML view', 'en': 'LVT have KML view'},
    'tab_shp2kml': {'vi': 'SHP → KML', 'en': 'SHP → KML'},
    'tab_kml2shp': {'vi': 'KML → SHP', 'en': 'KML → SHP'},
    'tab_help': {'vi': 'Trợ giúp', 'en': 'Help'},
    # Section 1
    'sec_io': {'vi': '1. Dữ liệu vào / ra', 'en': '1. Input / Output'},
    'lbl_shp': {'vi': 'SHP:', 'en': 'SHP:'},
    'lbl_layer': {'vi': 'Hoặc chọn Layer:', 'en': 'Or select Layer:'},
    'btn_browse': {'vi': 'Duyệt...', 'en': 'Browse...'},
    'lbl_output': {'vi': 'Xuất:', 'en': 'Output:'},
    # Section 2
    'sec_name': {'vi': '2. Name (Nhãn trên bản đồ)', 'en': '2. Name (Map Label)'},
    'lbl_field1': {'vi': 'Trường 1:', 'en': 'Field 1:'},
    'lbl_field2': {'vi': 'Trường 2:', 'en': 'Field 2:'},
    'lbl_sep': {'vi': 'Phân cách:', 'en': 'Separator:'},
    'lbl_name_size': {'vi': 'Cỡ chữ:', 'en': 'Font size:'},
    # Section 3
    'sec_desc': {'vi': '3. Mô tả (Popup)', 'en': '3. Description (Popup)'},
    'col_check': {'vi': '☑', 'en': '☑'},
    'col_field': {'vi': 'Trường gốc', 'en': 'Source Field'},
    'col_alias': {'vi': 'Tên hiển thị', 'en': 'Display Name'},
    'col_suffix': {'vi': 'Hậu tố', 'en': 'Suffix'},
    'btn_up': {'vi': '▲ Lên', 'en': '▲ Up'},
    'btn_down': {'vi': '▼ Xuống', 'en': '▼ Down'},
    # Section 4
    'sec_style': {'vi': '4. Kiểu Polygon', 'en': '4. Polygon Style'},
    'lbl_border': {'vi': 'Viền:', 'en': 'Border:'},
    'lbl_width': {'vi': 'Dày:', 'en': 'Width:'},
    'lbl_fill': {'vi': 'Nền:', 'en': 'Fill:'},
    'lbl_opacity': {'vi': 'Độ mờ:', 'en': 'Opacity:'},
    'chk_cond': {'vi': 'Tô màu theo điều kiện', 'en': 'Conditional coloring'},
    'lbl_cond_field': {'vi': 'Trường:', 'en': 'Field:'},
    # Section 5
    'sec_header': {'vi': '5. Tiêu đề & Tô dòng', 'en': '5. Header & Row Highlight'},
    'lbl_title': {'vi': 'Tiêu đề:', 'en': 'Title:'},
    'lbl_title_size': {'vi': 'Cỡ:', 'en': 'Size:'},
    'lbl_bg': {'vi': 'Nền:', 'en': 'BG:'},
    'lbl_fg': {'vi': 'Chữ:', 'en': 'Text:'},
    'chk_bold': {'vi': 'Đậm', 'en': 'Bold'},
    'chk_row_hl': {'vi': 'Tô màu dòng đặc biệt', 'en': 'Highlight special rows'},
    'chk_hl_bold': {'vi': 'Đậm', 'en': 'Bold'},
    'chk_hl_italic': {'vi': 'Nghiêng', 'en': 'Italic'},
    'default_title': {'vi': 'Thông tin', 'en': 'Information'},
    # Buttons
    'btn_save_cfg': {'vi': '💾 Lưu cấu hình', 'en': '💾 Save Config'},
    'btn_load_cfg': {'vi': '📂 Nạp cấu hình', 'en': '📂 Load Config'},
    'btn_preview': {'vi': '👁 Xem trước', 'en': '👁 Preview'},
    'btn_export': {'vi': '📤 Xuất', 'en': '📤 Export'},
    'btn_cancel': {'vi': '❌ Hủy', 'en': '❌ Cancel'},
    # KML to SHP tab
    'lbl_kml_input': {'vi': 'File KML/KMZ:', 'en': 'KML/KMZ File:'},
    'lbl_target_crs': {'vi': 'Hệ tọa độ đích:', 'en': 'Target CRS:'},
    'lbl_default_crs': {'vi': '(Mặc định: EPSG:4326)', 'en': '(Default: EPSG:4326)'},
    'btn_convert': {'vi': '🔄 Chuyển đổi', 'en': '🔄 Convert'},
    'btn_add_to_map': {'vi': '🗺 Thêm vào bản đồ', 'en': '🗺 Add to Map'},
    # Messages
    'msg_no_shp': {'vi': 'Vui lòng chọn Shapefile hoặc Layer!', 'en': 'Please select a Shapefile or Layer!'},
    'msg_success': {'vi': 'Thành công', 'en': 'Success'},
    'msg_error': {'vi': 'Lỗi', 'en': 'Error'},
    'msg_warning': {'vi': 'Cảnh báo', 'en': 'Warning'},
    'msg_config_saved': {'vi': 'Đã lưu cấu hình!', 'en': 'Config saved!'},
    'msg_config_loaded': {'vi': 'Đã nạp cấu hình!', 'en': 'Config loaded!'},
    'msg_kml_no_file': {'vi': 'Vui lòng chọn file KML/KMZ!', 'en': 'Please select a KML/KMZ file!'},
    'msg_convert_ok': {'vi': 'Đã chuyển đổi thành công!', 'en': 'Conversion successful!'},
    # Language
    'btn_lang': {'vi': '🌐 English', 'en': '🌐 Tiếng Việt'},
    # Help
    'help_title': {'vi': 'Hướng dẫn sử dụng', 'en': 'User Guide'},
}

HELP_TEXT = {
    'vi': """<h2>LVT have KML view - Hướng dẫn</h2>
<h3>Tab SHP → KML</h3>
<ol>
<li><b>Chọn dữ liệu:</b> Browse file SHP hoặc chọn layer đang mở trong QGIS</li>
<li><b>Cấu hình Name:</b> Chọn 1-2 trường làm nhãn hiển thị trên bản đồ, điều chỉnh cỡ chữ</li>
<li><b>Cấu hình Popup:</b> Tick chọn trường, đặt tên hiển thị (alias), thêm hậu tố (vd: ha, m²)</li>
<li><b>Kiểu Polygon:</b> Chọn màu viền/nền, độ trong suốt. Bật tô màu điều kiện nếu cần</li>
<li><b>Tiêu đề:</b> Đặt tên header popup, chọn màu nền/chữ, cỡ chữ</li>
<li><b>Xem trước:</b> Nhấn Preview để xem popup trước khi xuất</li>
<li><b>Xuất:</b> Chọn KML hoặc KMZ, nhấn Export</li>
</ol>
<h3>Tab KML → SHP</h3>
<ol>
<li>Chọn file KML hoặc KMZ</li>
<li>Chọn hệ tọa độ đích (mặc định WGS84)</li>
<li>Nhấn Chuyển đổi để tạo Shapefile</li>
<li>Nhấn Thêm vào bản đồ để hiển thị trong QGIS</li>
</ol>
<p><i>Phiên bản: 0.2.0 (_002) | Tác giả: LVT (Lộc Vũ Trung)</i></p>""",

    'en': """<h2>LVT have KML view - User Guide</h2>
<h3>Tab SHP → KML</h3>
<ol>
<li><b>Select data:</b> Browse SHP file or select an open layer in QGIS</li>
<li><b>Configure Name:</b> Choose 1-2 fields for map label, adjust font size</li>
<li><b>Configure Popup:</b> Check fields, set display names (alias), add suffix (e.g. ha, m²)</li>
<li><b>Polygon Style:</b> Choose border/fill colors, opacity. Enable conditional coloring if needed</li>
<li><b>Header:</b> Set popup header title, background/text color, font size</li>
<li><b>Preview:</b> Click Preview to see popup before exporting</li>
<li><b>Export:</b> Choose KML or KMZ, click Export</li>
</ol>
<h3>Tab KML → SHP</h3>
<ol>
<li>Select KML or KMZ file</li>
<li>Choose target CRS (default WGS84)</li>
<li>Click Convert to create Shapefile</li>
<li>Click Add to Map to display in QGIS</li>
</ol>
<p><i>Version: 0.2.0 (_002) | Author: LVT (Lộc Vũ Trung)</i></p>"""
}


def tr(key, lang='vi'):
    """Get translated string."""
    entry = T.get(key, {})
    return entry.get(lang, entry.get('vi', key))


def get_help(lang='vi'):
    """Get help text in specified language."""
    return HELP_TEXT.get(lang, HELP_TEXT['vi'])
