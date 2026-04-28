"""KML/KMZ to Shapefile converter."""

import os
import zipfile
import tempfile
from qgis.core import (
    QgsVectorLayer, QgsVectorFileWriter, QgsProject,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform
)


class KmlToShpConverter:
    """Convert KML/KMZ files to Shapefile format."""

    def convert(self, input_path, output_path, target_crs_str='EPSG:4326'):
        """Convert KML/KMZ to SHP.

        Args:
            input_path: Path to KML or KMZ file
            output_path: Path for output SHP file
            target_crs_str: Target CRS string (e.g. 'EPSG:4326')

        Returns:
            (success, message, layer_or_none)
        """
        try:
            kml_path = input_path

            # If KMZ, extract KML first
            if input_path.lower().endswith('.kmz'):
                kml_path = self._extract_kmz(input_path)
                if not kml_path:
                    return False, "Cannot extract KML from KMZ", None

            # Load KML as vector layer
            layer = QgsVectorLayer(kml_path, 'kml_import', 'ogr')
            if not layer.isValid():
                return False, "Cannot read KML file", None

            # Set up CRS transform
            target_crs = QgsCoordinateReferenceSystem(target_crs_str)
            transform = None
            if layer.crs() != target_crs:
                transform = QgsCoordinateTransform(
                    layer.crs(), target_crs, QgsProject.instance()
                )

            # Write to SHP
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'ESRI Shapefile'
            options.fileEncoding = 'UTF-8'
            if transform:
                options.ct = transform

            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_path, QgsProject.instance().transformContext(), options
            )

            if error[0] == QgsVectorFileWriter.NoError:
                result_layer = QgsVectorLayer(output_path, os.path.basename(output_path), 'ogr')
                return True, f"Saved: {output_path}", result_layer
            else:
                return False, f"Write error: {error[1]}", None

        except Exception as e:
            return False, f"Error: {str(e)}", None

    @staticmethod
    def _extract_kmz(kmz_path):
        """Extract KML from KMZ file."""
        try:
            tmp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile(kmz_path, 'r') as zf:
                kml_files = [f for f in zf.namelist() if f.lower().endswith('.kml')]
                if not kml_files:
                    return None
                zf.extract(kml_files[0], tmp_dir)
                return os.path.join(tmp_dir, kml_files[0])
        except Exception:
            return None
