"""KML/KMZ builder engine.

Reads features from QgsVectorLayer, reprojects to EPSG:4326,
and generates KML with styled HTML popup descriptions.
"""

import zipfile
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform, QgsProject, QgsWkbTypes
)
from .color_utils import hex_to_kml_color
from .html_template import HtmlTemplateBuilder


class KmlBuilder:
    """Builds KML/KMZ files from vector layer features."""

    def __init__(self, config):
        self.config = config
        self.html_builder = HtmlTemplateBuilder(config)

    def build(self, layer, output_path, output_format='kml'):
        """Build KML/KMZ file from a vector layer.

        Args:
            layer: QgsVectorLayer
            output_path: Output file path
            output_format: 'kml' or 'kmz'

        Returns:
            (success: bool, message: str)
        """
        try:
            target_crs = QgsCoordinateReferenceSystem('EPSG:4326')
            source_crs = layer.crs()

            transform = None
            if source_crs != target_crs:
                transform = QgsCoordinateTransform(
                    source_crs, target_crs, QgsProject.instance()
                )

            kml_content = self._build_kml_document(layer, transform)

            if output_format == 'kmz':
                return self._write_kmz(kml_content, output_path)
            else:
                return self._write_kml(kml_content, output_path)

        except Exception as e:
            return False, f"Error: {str(e)}"

    def _build_kml_document(self, layer, transform):
        """Build the complete KML XML string."""
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
        lines.append('<Document>')
        lines.append(f'<name>{self._escape_xml(layer.name())}</name>')

        # Styles
        lines.extend(self._build_styles())

        # Placemarks
        name_cfg = self.config.get('name_fields', {})
        cond_cfg = self.config.get('conditional_colors', {})

        for feature in layer.getFeatures():
            pm = self._build_placemark(feature, name_cfg, cond_cfg, transform)
            if pm:
                lines.extend(pm)

        lines.append('</Document>')
        lines.append('</kml>')
        return '\n'.join(lines)

    def _build_styles(self):
        """Build KML Style elements."""
        lines = []
        poly = self.config.get('polygon_style', {})
        border_kml = hex_to_kml_color(poly.get('border_color', '#FF0000'), 100)
        fill_kml = hex_to_kml_color(poly.get('fill_color', '#00FF00'),
                                     poly.get('fill_opacity', 50))
        border_w = poly.get('border_width', 2)

        # Default style
        lines.append('<Style id="style_default">')
        lines.append('<LabelStyle><scale>1</scale></LabelStyle>')
        lines.append(f'<LineStyle><color>{border_kml}</color><width>{border_w}</width></LineStyle>')
        lines.append(f'<PolyStyle><color>{fill_kml}</color></PolyStyle>')
        lines.append('</Style>')

        # Conditional styles
        cond = self.config.get('conditional_colors', {})
        if cond.get('enabled', False):
            for i, rule in enumerate(cond.get('rules', [])):
                r_border = hex_to_kml_color(rule.get('border_color', '#FF0000'), 100)
                r_fill = hex_to_kml_color(rule.get('fill_color', '#FF0000'),
                                           poly.get('fill_opacity', 50))
                lines.append(f'<Style id="style_rule_{i}">')
                lines.append('<LabelStyle><scale>1</scale></LabelStyle>')
                lines.append(f'<LineStyle><color>{r_border}</color>'
                             f'<width>{border_w}</width></LineStyle>')
                lines.append(f'<PolyStyle><color>{r_fill}</color></PolyStyle>')
                lines.append('</Style>')

        return lines

    def _build_placemark(self, feature, name_cfg, cond_cfg, transform):
        """Build a single Placemark element."""
        geom = feature.geometry()
        if geom is None or geom.isEmpty():
            return None

        if transform:
            geom.transform(transform)

        # Name
        name = self._build_name(feature, name_cfg)

        # Description HTML
        feature_data = {}
        for field in feature.fields():
            feature_data[field.name()] = feature[field.name()]
        desc_html = self.html_builder.build(feature_data)

        # Style
        style_id = self._determine_style(feature, cond_cfg)

        lines = ['<Placemark>']
        lines.append(f'<name>{self._escape_xml(name)}</name>')
        lines.append(f'<styleUrl>#{style_id}</styleUrl>')
        lines.append(f'<description><![CDATA[{desc_html}]]></description>')

        # Geometry
        geom_type = QgsWkbTypes.geometryType(geom.wkbType())
        if geom_type == QgsWkbTypes.PolygonGeometry:
            lines.extend(self._polygon_to_kml(geom))
        elif geom_type == QgsWkbTypes.LineGeometry:
            lines.extend(self._line_to_kml(geom))
        elif geom_type == QgsWkbTypes.PointGeometry:
            lines.extend(self._point_to_kml(geom))

        lines.append('</Placemark>')
        return lines

    def _build_name(self, feature, name_cfg):
        """Build placemark name from configured fields."""
        f1 = name_cfg.get('field1', '')
        f2 = name_cfg.get('field2', '')
        sep = name_cfg.get('separator', ' - ')

        v1 = str(feature[f1]) if f1 and feature[f1] is not None else ''
        v2 = str(feature[f2]) if f2 and feature[f2] is not None else ''

        if v1 and v2:
            return f"{v1}{sep}{v2}"
        return v1 or v2 or 'Unnamed'

    def _determine_style(self, feature, cond_cfg):
        """Determine which style to apply based on conditional rules."""
        if not cond_cfg.get('enabled', False):
            return 'style_default'
        field = cond_cfg.get('field', '')
        if not field:
            return 'style_default'

        field_names = [f.name() for f in feature.fields()]
        value = feature[field] if field in field_names else None

        for i, rule in enumerate(cond_cfg.get('rules', [])):
            if HtmlTemplateBuilder._evaluate_condition(
                    value, rule.get('operator', '='), rule.get('value', '')):
                return f'style_rule_{i}'
        return 'style_default'

    def _polygon_to_kml(self, geom):
        """Convert polygon geometry to KML elements."""
        lines = []
        if geom.isMultipart():
            lines.append('<MultiGeometry>')
            for part in geom.asMultiPolygon():
                lines.extend(self._single_polygon_to_kml(part))
            lines.append('</MultiGeometry>')
        else:
            polygon = geom.asPolygon()
            if polygon:
                lines.extend(self._single_polygon_to_kml(polygon))
        return lines

    def _single_polygon_to_kml(self, rings):
        """Convert a single polygon (list of rings) to KML."""
        lines = ['<Polygon>']
        # Outer ring
        lines.append('<outerBoundaryIs><LinearRing><coordinates>')
        lines.append(' '.join(f'{p.x()},{p.y()},0' for p in rings[0]))
        lines.append('</coordinates></LinearRing></outerBoundaryIs>')
        # Inner rings (holes)
        for i in range(1, len(rings)):
            lines.append('<innerBoundaryIs><LinearRing><coordinates>')
            lines.append(' '.join(f'{p.x()},{p.y()},0' for p in rings[i]))
            lines.append('</coordinates></LinearRing></innerBoundaryIs>')
        lines.append('</Polygon>')
        return lines

    def _line_to_kml(self, geom):
        """Convert line geometry to KML."""
        lines = []
        if geom.isMultipart():
            lines.append('<MultiGeometry>')
            for part in geom.asMultiPolyline():
                lines.append('<LineString><coordinates>')
                lines.append(' '.join(f'{p.x()},{p.y()},0' for p in part))
                lines.append('</coordinates></LineString>')
            lines.append('</MultiGeometry>')
        else:
            polyline = geom.asPolyline()
            if polyline:
                lines.append('<LineString><coordinates>')
                lines.append(' '.join(f'{p.x()},{p.y()},0' for p in polyline))
                lines.append('</coordinates></LineString>')
        return lines

    def _point_to_kml(self, geom):
        """Convert point geometry to KML."""
        lines = []
        if geom.isMultipart():
            lines.append('<MultiGeometry>')
            for pt in geom.asMultiPoint():
                lines.append(f'<Point><coordinates>{pt.x()},{pt.y()},0</coordinates></Point>')
            lines.append('</MultiGeometry>')
        else:
            pt = geom.asPoint()
            lines.append(f'<Point><coordinates>{pt.x()},{pt.y()},0</coordinates></Point>')
        return lines

    @staticmethod
    def _write_kml(content, path):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"KML saved: {path}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    @staticmethod
    def _write_kmz(kml_content, path):
        try:
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('doc.kml', kml_content)
            return True, f"KMZ saved: {path}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    @staticmethod
    def _escape_xml(text):
        if text is None:
            return ''
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
