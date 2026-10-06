"""
Pruebas automatizadas para el módulo exportador.py.

Verifica la exportación de tareas a formato CSV en diferentes escenarios
utilizando únicamente la librería estándar de Python.
"""

from datetime import date, datetime
import csv
import io
import json
import os
import shutil
import tempfile
import unittest

from exportador import (
    CAMPOS_BASE,
    CAMPO_FECHA_LIMITE,
    ExportadorCSV,
    exportar_a_csv,
    exportar_a_csv_string,
    exportar_csv,
    exportar_tareas_a_csv,
    exportar_tareas_csv,
)
from tarea_app import TareaManager


class TestExportadorCSV(unittest.TestCase):
    """Conjunto de pruebas para la exportación de tareas a CSV."""

    def setUp(self):
        """Crear un directorio temporal para las pruebas."""
        self.temp_dir = tempfile.mkdtemp()
        self.archivo_salida = os.path.join(self.temp_dir, "test_salida.csv")

    def tearDown(self):
        """Limpiar el directorio temporal."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _leer_csv(self, ruta: str) -> tuple[list[str], list[dict[str, str]]]:
        """Función auxiliar para leer un CSV y retornar encabezados y filas."""
        with open(ruta, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            filas = list(reader)
        encabezados = filas[0] if filas else []
        with open(ruta, "r", newline="", encoding="utf-8") as f:
            dict_reader = csv.DictReader(f)
            registros = list(dict_reader)
        return encabezados, registros

    def test_exportar_lista_vacia(self):
        """Test: Exportar una lista vacía genera un CSV únicamente con encabezados base."""
        resultado = exportar_a_csv([], self.archivo_salida)
        self.assertEqual(resultado, self.archivo_salida)
        self.assertTrue(os.path.exists(self.archivo_salida))

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(encabezados, CAMPOS_BASE)
        self.assertEqual(len(registros), 0)

    def test_exportar_tareas_basicas(self):
        """Test: Exportar tareas estándar con los campos mínimos requeridos."""
        tareas = [
            {
                "id": 1,
                "titulo": "Preparar informe",
                "completa": False,
                "prioridad": "alta",
                "creado": "2026-10-06T10:00:00",
            },
            {
                "id": 2,
                "titulo": "Enviar correo al cliente",
                "completa": True,
                "prioridad": "baja",
                "creado": "2026-10-06T11:00:00",
            },
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(encabezados, ["id", "titulo", "completa", "prioridad", "creado"])
        self.assertEqual(len(registros), 2)

        self.assertEqual(registros[0]["id"], "1")
        self.assertEqual(registros[0]["titulo"], "Preparar informe")
        self.assertEqual(registros[0]["completa"], "False")
        self.assertEqual(registros[0]["prioridad"], "alta")
        self.assertEqual(registros[0]["creado"], "2026-10-06T10:00:00")

        self.assertEqual(registros[1]["id"], "2")
        self.assertEqual(registros[1]["titulo"], "Enviar correo al cliente")
        self.assertEqual(registros[1]["completa"], "True")
        self.assertEqual(registros[1]["prioridad"], "baja")
        self.assertEqual(registros[1]["creado"], "2026-10-06T11:00:00")

    def test_exportar_con_fecha_limite(self):
        """Test: Si existe fecha límite en las tareas, se incluye la columna correspondiente."""
        tareas = [
            {
                "id": 1,
                "titulo": "Entrega de proyecto",
                "completa": False,
                "prioridad": "alta",
                "creado": "2026-10-06T09:00:00",
                "fecha_limite": "2026-10-20",
            },
            {
                "id": 2,
                "titulo": "Revisar notas",
                "completa": False,
                "prioridad": "media",
                "creado": "2026-10-06T09:30:00",
                # Sin fecha límite
            },
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        encabezados, registros = self._leer_csv(self.archivo_salida)
        esperado = ["id", "titulo", "completa", "prioridad", "creado", "fecha_limite"]
        self.assertEqual(encabezados, esperado)
        self.assertEqual(len(registros), 2)

        self.assertEqual(registros[0]["fecha_limite"], "2026-10-20")
        self.assertEqual(registros[1]["fecha_limite"], "")

    def test_exportar_claves_alternativas_fecha_limite(self):
        """Test: Soporta variantes de nombre como limite, fecha_vencimiento o due_date."""
        tareas = [
            {
                "id": 1,
                "titulo": "Tarea 1",
                "completa": False,
                "prioridad": "alta",
                "creado": "2026-10-06T09:00:00",
                "limite": "2026-10-15",
            },
            {
                "id": 2,
                "titulo": "Tarea 2",
                "completa": False,
                "prioridad": "media",
                "creado": "2026-10-06T09:00:00",
                "fecha_vencimiento": "2026-10-18",
            },
            {
                "id": 3,
                "titulo": "Tarea 3",
                "completa": True,
                "prioridad": "baja",
                "creado": "2026-10-06T09:00:00",
                "due_date": "2026-10-25",
            },
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertIn("fecha_limite", encabezados)
        self.assertEqual(registros[0]["fecha_limite"], "2026-10-15")
        self.assertEqual(registros[1]["fecha_limite"], "2026-10-18")
        self.assertEqual(registros[2]["fecha_limite"], "2026-10-25")

    def test_sin_fecha_limite_no_incluye_columna(self):
        """Test: Si ninguna tarea tiene fecha límite, la columna no se añade automáticamente."""
        tareas = [
            {"id": 1, "titulo": "T1", "completa": False, "prioridad": "media", "creado": "2026-10-06"},
            {"id": 2, "titulo": "T2", "completa": True, "prioridad": "alta", "creado": "2026-10-06"},
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        encabezados, _ = self._leer_csv(self.archivo_salida)
        self.assertNotIn("fecha_limite", encabezados)
        self.assertEqual(encabezados, ["id", "titulo", "completa", "prioridad", "creado"])

    def test_forzar_incluir_fecha_limite(self):
        """Test: Se puede forzar incluir fecha_limite con incluir_fecha_limite=True."""
        tareas = [
            {"id": 1, "titulo": "T1", "completa": False, "prioridad": "media", "creado": "2026-10-06"},
        ]
        exportar_a_csv(tareas, self.archivo_salida, incluir_fecha_limite=True)

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertIn("fecha_limite", encabezados)
        self.assertEqual(registros[0]["fecha_limite"], "")

    def test_forzar_excluir_fecha_limite(self):
        """Test: Se puede forzar excluir fecha_limite con incluir_fecha_limite=False."""
        tareas = [
            {
                "id": 1,
                "titulo": "T1",
                "completa": False,
                "prioridad": "media",
                "creado": "2026-10-06",
                "fecha_limite": "2026-11-01",
            },
        ]
        exportar_a_csv(tareas, self.archivo_salida, incluir_fecha_limite=False)

        encabezados, _ = self._leer_csv(self.archivo_salida)
        self.assertNotIn("fecha_limite", encabezados)

    def test_prioridad_por_defecto_para_tareas_antiguas(self):
        """Test: Si una tarea no tiene campo prioridad, se asigna 'media' por defecto."""
        tareas = [
            {"id": 1, "titulo": "Tarea antigua", "completa": False, "creado": "2026-09-01T12:00:00"},
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        _, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(registros[0]["prioridad"], "media")

    def test_manejo_caracteres_especiales(self):
        """Test: Preserva caracteres especiales, comas, comillas, acentos, saltos de línea y emojis."""
        titulo_complejo = 'Tarea con "comillas", comas y acento: ñandú 🚀\nSegunda línea'
        tareas = [
            {
                "id": 1,
                "titulo": titulo_complejo,
                "completa": True,
                "prioridad": "alta",
                "creado": "2026-10-06",
            }
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        _, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(registros[0]["titulo"], titulo_complejo)

    def test_exportar_desde_tarea_manager(self):
        """Test: Acepta directamente una instancia de TareaManager."""
        manager = TareaManager()
        # Mock de tareas del manager para no depender del archivo del sistema
        manager.tareas = [
            {"id": 1, "titulo": "Tarea Manager 1", "completa": False, "prioridad": "alta", "creado": "2026-10-06"},
            {"id": 2, "titulo": "Tarea Manager 2", "completa": True, "prioridad": "baja", "creado": "2026-10-06"},
        ]
        exportar_a_csv(manager, self.archivo_salida)

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0]["titulo"], "Tarea Manager 1")
        self.assertEqual(registros[1]["titulo"], "Tarea Manager 2")

    def test_exportar_desde_archivo_json(self):
        """Test: Acepta la ruta a un archivo JSON con formato de tareas."""
        json_path = os.path.join(self.temp_dir, "tareas_test.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "tareas": [
                    {"id": 10, "titulo": "Desde JSON", "completa": False, "prioridad": "media", "creado": "2026-10-06"}
                ]
            }, f)

        exportar_a_csv(json_path, self.archivo_salida)

        _, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["id"], "10")
        self.assertEqual(registros[0]["titulo"], "Desde JSON")

    def test_exportar_a_buffer_stringio(self):
        """Test: Soporta escribir directamente a un objeto tipo archivo en memoria."""
        buffer = io.StringIO()
        tareas = [{"id": 1, "titulo": "En memoria", "completa": False, "prioridad": "media", "creado": "2026-10-06"}]
        resultado = exportar_a_csv(tareas, buffer)

        self.assertIs(resultado, buffer)
        contenido = buffer.getvalue()
        self.assertIn("id,titulo,completa,prioridad,creado", contenido)
        self.assertIn("1,En memoria,False,media,2026-10-06", contenido)

    def test_exportar_a_csv_string(self):
        """Test: La función exportar_a_csv_string retorna el contenido CSV como texto."""
        tareas = [{"id": 5, "titulo": "Texto plano", "completa": True, "prioridad": "alta", "creado": "2026-10-06"}]
        csv_str = exportar_a_csv_string(tareas)

        lineas = [l for l in csv_str.strip().split("\n") if l]
        self.assertEqual(len(lineas), 2)
        self.assertEqual(lineas[0], "id,titulo,completa,prioridad,creado")
        self.assertEqual(lineas[1], "5,Texto plano,True,alta,2026-10-06")

    def test_clase_exportador_csv(self):
        """Test: La clase ExportadorCSV configura y exporta correctamente."""
        exportador = ExportadorCSV(ruta_archivo=self.archivo_salida, incluir_fecha_limite=True)
        tareas = [{"id": 1, "titulo": "Clase", "completa": False, "prioridad": "media", "creado": "2026-10-06"}]
        exportador.exportar(tareas)

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertIn("fecha_limite", encabezados)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["titulo"], "Clase")

    def test_no_modifica_datos_originales(self):
        """Test: La exportación no altera los diccionarios originales ni la lista de tareas."""
        tarea_original = {
            "id": 1,
            "titulo": "No mutar",
            "completa": False,
            "creado": "2026-10-06",
            "detalles": {"extra": 123},
        }
        tareas = [tarea_original]
        tareas_copia = [dict(tarea_original)]

        exportar_a_csv(tareas, self.archivo_salida)
        self.assertEqual(tareas, tareas_copia)
        self.assertNotIn("prioridad", tarea_original)

    def test_crea_directorio_padre_si_no_existe(self):
        """Test: Crea automáticamente las carpetas intermedias si no existen."""
        ruta_anidada = os.path.join(self.temp_dir, "carpeta1", "carpeta2", "export.csv")
        tareas = [{"id": 1, "titulo": "Anidado", "completa": False, "prioridad": "media", "creado": "2026-10-06"}]

        exportar_a_csv(tareas, ruta_anidada)
        self.assertTrue(os.path.exists(ruta_anidada))

    def test_aliases_disponibles(self):
        """Test: Todos los nombres de función alias están disponibles y funcionan."""
        tareas = [{"id": 1, "titulo": "Alias", "completa": False, "prioridad": "media", "creado": "2026-10-06"}]

        for alias_fn in (exportar_csv, exportar_tareas_csv, exportar_tareas_a_csv):
            buffer = io.StringIO()
            alias_fn(tareas, buffer)
            self.assertIn("1,Alias,False,media,2026-10-06", buffer.getvalue())

    def test_validaciones_de_entradas_invalidas(self):
        """Test: Manejo adecuado de argumentos None o estructuras inválidas."""
        with self.assertRaises(ValueError):
            exportar_a_csv(None, self.archivo_salida)

        with self.assertRaises(TypeError):
            exportar_a_csv(["no es diccionario"], self.archivo_salida)

        with self.assertRaises(TypeError):
            exportar_a_csv(12345, self.archivo_salida)

    def test_columnas_personalizadas(self):
        """Test: Permite especificar un subconjunto personalizado de columnas."""
        tareas = [
            {"id": 1, "titulo": "Personalizado", "completa": False, "prioridad": "alta", "creado": "2026-10-06"}
        ]
        exportar_a_csv(tareas, self.archivo_salida, columnas=["id", "titulo"])

        encabezados, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(encabezados, ["id", "titulo"])
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0], {"id": "1", "titulo": "Personalizado"})

    def test_objetos_datetime_en_campos(self):
        """Test: Los objetos date y datetime en creado y fecha_limite se formatean a ISO."""
        fecha_creacion = datetime(2026, 10, 6, 14, 30, 0)
        fecha_fin = date(2026, 10, 31)
        tareas = [
            {
                "id": 1,
                "titulo": "Con fechas datetime",
                "completa": False,
                "prioridad": "alta",
                "creado": fecha_creacion,
                "fecha_limite": fecha_fin,
            }
        ]
        exportar_a_csv(tareas, self.archivo_salida)

        _, registros = self._leer_csv(self.archivo_salida)
        self.assertEqual(registros[0]["creado"], "2026-10-06T14:30:00")
        self.assertEqual(registros[0]["fecha_limite"], "2026-10-31")


if __name__ == "__main__":
    unittest.main()
