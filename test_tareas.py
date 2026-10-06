"""
Pruebas automatizadas del gestor de tareas.
Usa pytest para ejecutar las pruebas.
"""

import json
import os
import shutil
import tempfile
import unittest

from tarea_app import TareaManager


class TestTareaManager(unittest.TestCase):
    """Pruebas unitarias para TareaManager."""
    
    def setUp(self):
        """Preparar un ambiente de prueba limpio antes de cada test."""
        self.tareas_file = "tareas_backup_antes_test.json"
        
        # Guardar el archivo original si existe
        if os.path.exists("tareas.json"):
            shutil.copy2("tareas.json", self.tareas_file)
        
        # Eliminar tareas actuales para empezar limpio
        if os.path.exists("tareas.json"):
            os.remove("tareas.json")
    
    def tearDown(self):
        """Limpiar después de cada test."""
        # Restaurar el archivo original
        if self.tareas_file and os.path.exists(self.tareas_file):
            shutil.copy2(self.tareas_file, "tareas.json")
            os.remove(self.tareas_file)
    
    def test_crear_tarea(self):
        """Test: Crear una nueva tarea."""
        manager = TareaManager()
        tarea = manager.crear_tarea("Comprar leche")
        
        self.assertEqual(tarea["titulo"], "Comprar leche")
        self.assertFalse(tarea["completa"])
        self.assertIn("id", tarea)
        self.assertIn("creado", tarea)
    
    def test_crear_tareas_múltiples(self):
        """Test: Crear múltiples tareas."""
        manager = TareaManager()
        
        tarea1 = manager.crear_tarea("Tarea 1")
        tarea2 = manager.crear_tarea("Tarea 2")
        
        self.assertEqual(len(manager.listar_tareas()), 2)
        self.assertNotEqual(tarea1["id"], tarea2["id"])
    
    def test_listar_tareas(self):
        """Test: Listar todas las tareas."""
        manager = TareaManager()
        manager.crear_tarea("A")
        manager.crear_tarea("B")
        
        tasks = manager.listar_tareas()
        
        self.assertEqual(len(tasks), 2)
        titles = [t["titulo"] for t in tasks]
        self.assertIn("A", titles)
        self.assertIn("B", titles)
    
    def test_completar_tarea(self):
        """Test: Marcar tarea como completada."""
        manager = TareaManager()
        manager.crear_tarea("Tarea pendiente")
        
        tasks = manager.listar_tareas()
        assert len(tasks) == 1
        assert not tasks[0]["completa"]
        
        result = manager.completar_tarea(tasks[0]["id"])
        
        self.assertTrue(result["completa"])
        
        # Verificar persistencia
        TareaManager().listar_tareas()
        
        manager2 = TareaManager()
        tasks_fresh = manager2.listar_tareas()
        self.assertTrue(tasks_fresh[0]["completa"])
    
    def test_eliminar_tarea(self):
        """Test: Eliminar una tarea."""
        manager = TareaManager()
        tarea1 = manager.crear_tarea("A")
        tarea2 = manager.crear_tarea("B")
        
        self.assertEqual(len(manager.listar_tareas()), 2)
        
        self.assertTrue(manager.eliminar_tarea(tarea1["id"]))
        
        tasks = manager.listar_tareas()
        self.assertEqual(len(tasks), 1)
        self.assertNotIn("A", [t["titulo"] for t in tasks])
    
    def test_eliminar_no_existe(self):
        """Test: Eliminar tarea que no existe."""
        manager = TareaManager()
        
        result = manager.eliminar_tarea(999)
        
        self.assertFalse(result)
    
    def test_buscar_por_titulo(self):
        """Test: Buscar tareas por título parcial."""
        manager = TareaManager()
        manager.crear_tarea("Comprar leche en el supermercado")
        manager.crear_tarea("Preparar café")
        manager.crear_tarea("Llamar al abuelo")
        
        results = manager.buscar_por_titulo("comprar")
        
        self.assertEqual(len(results), 1)
        self.assertIn("Comprar leche en el supermercado", [r["titulo"] for r in results])
    
    def test_buscar_no_encontrado(self):
        """Test: Buscar sin resultados."""
        manager = TareaManager()
        manager.crear_tarea("Tarea ABC")
        
        results = manager.buscar_por_titulo("DEF")
        
        self.assertEqual(len(results), 0)
    
    def test_error_titulo_vacio(self):
        """Test: Crear tarea con título vacío debe fallar."""
        manager = TareaManager()
        
        with self.assertRaises(ValueError):
            manager.crear_tarea("")
        
        with self.assertRaises(ValueError):
            manager.crear_tarea("   ")
    
    def test_crear_tarea_con_prioridad(self):
        """Test: Crear tarea con prioridad explícita."""
        manager = TareaManager()
        
        alta = manager.crear_tarea("Tarea importante", prioridad="alta")
        media = manager.crear_tarea("Tarea normal", prioridad="media")
        baja = manager.crear_tarea("Tarea menos importante", prioridad="baja")
        
        self.assertEqual(alta["prioridad"], "alta")
        self.assertEqual(media["prioridad"], "media")
        self.assertEqual(baja["prioridad"], "baja")
    
    def test_crear_tarea_sin_prioridad(self):
        """Test: Crear tarea sin especificar prioridad (debe ser "media" por defecto)."""
        manager = TareaManager()
        tarea = manager.crear_tarea("Tarea sin prioridad")
        
        self.assertEqual(tarea["prioridad"], "media")
    
    def test_crear_tarea_prioridad_invalida(self):
        """Test: Crear tarea con prioridad inválida debe fallar."""
        manager = TareaManager()
        
        with self.assertRaises(ValueError):
            manager.crear_tarea("Tarea", prioridad="urgente")
        
        with self.assertRaises(ValueError):
            manager.crear_tarea("Tarea", prioridad="")


def run_suite():
    """Ejecutar todas las pruebas y mostrar resultados."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTareaManager)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Reporte final
    print("\n" + "=" * 60)
    print(f"PRUEBAS COMPLETADAS: {result.testsRun}")
    print(f"Aprobadas:       {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falladas:        {len(result.failures)}")
    print(f"Errores:         {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ¡Todas las pruebas aprobadas!")
    else:
        print("\n❌ Algunas pruebas fallaron. Revisar error(es) anterior(es).")
    
    return result


if __name__ == "__main__":
    run_suite()
