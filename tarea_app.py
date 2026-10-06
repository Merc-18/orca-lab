"""
Aplicación simple para gestión de tareas.
Funcionalidades: crear, listar, completar y eliminar tareas.
Las tareas se guardan en un archivo JSON.
"""

import json
import os
from datetime import datetime
from typing import Optional


TAREAS_FILE = "tareas.json"


def _cargar_tareas() -> list[dict]:
    """Cargar tareas desde el archivo JSON."""
    if not os.path.exists(TAREAS_FILE):
        return []
    
    try:
        with open(TAREAS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("tareas", [])
    except (json.JSONDecodeError, IOError):
        return []


def _guardar_tareas(tareas: list[dict]) -> bool:
    """Guardar tareas en el archivo JSON."""
    try:
        with open(TAREAS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "tareas": tareas,
                "ultima_actualizacion": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


class TareaManager:
    """Gestor de tareas con CRUD básico."""
    
    def __init__(self):
        self.tareas = _cargar_tareas()
    
    def crear_tarea(self, titulo: str, prioridad: str = "media") -> dict:
        """Crear una nueva tarea."""
        if not titulo or not titulo.strip():
            raise ValueError("El título de la tarea no puede estar vacío.")
        
        if prioridad not in ("alta", "media", "baja"):
            raise ValueError("La prioridad debe ser 'alta', 'media' o 'baja'.")
        
        tarea = {
            "id": self._generar_id(),
            "titulo": titulo.strip(),
            "completa": False,
            "creado": datetime.now().isoformat(),
            "prioridad": prioridad
        }
        self.tareas.append(tarea)
        _guardar_tareas(self.tareas)
        return tarea.copy()
    
    def listar_tareas(self) -> list[dict]:
        """Listar todas las tareas."""
        # Cargar nuevamente para obtener los datos más recientes
        tareas_frescas = _cargar_tareas()
        return sorted(tareas_frescas, key=lambda t: t.get("id", 0))
    
    def completar_tarea(self, tarea_id: int) -> Optional[dict]:
        """Marcar una tarea como completada."""
        for tarea in self.tareas:
            if tarea["id"] == tarea_id:
                tarea["completa"] = True
                tarea["actualizada"] = datetime.now().isoformat()
                _guardar_tareas(self.tareas)
                return tarea.copy()
        return None
    
    def eliminar_tarea(self, tarea_id: int) -> bool:
        """Eliminar una tarea."""
        for i, tarea in enumerate(self.tareas):
            if tarea["id"] == tarea_id:
                self.tareas.pop(i)
                _guardar_tareas(self.tareas)
                return True
        return False
    
    def obtener_tarea_por_id(self, tarea_id: int) -> Optional[dict]:
        """Obtener una tarea por su ID."""
        for tarea in self.tareas:
            if tarea["id"] == tarea_id:
                return tarea.copy()
        return None
    
    def buscar_por_titulo(self, parcial: str) -> list[dict]:
        """Buscar tareas que contengan el parcial."""
        resultados = []
        for tarea in self.tareas:
            if parcial.lower() in tarea["titulo"].lower():
                resultados.append(tarea.copy())
        return resultados
    
    def _generar_id(self) -> int:
        """Generar un ID único para una tarea."""
        ids_existentes = [t["id"] for t in self.tareas]
        if not ids_existentes:
            return 1
        return max(ids_existentes) + 1
    
    def resetear(self) -> None:
        """Eliminar todas las tareas (borrador limpio)."""
        self.tareas = []
        _guardar_tareas(self.tareas)


def main():
    """Entrypoint para pruebas manuales y CLI básica."""
    manager = TareaManager()
    
    while True:
        print("\n=== GESTOR DE TAREAS ===")
        print("1. Crear nueva tarea")
        print("2. Listar todas las tareas")
        print("3. Marcar tarea como completada")
        print("4. Eliminar tarea")
        print("5. Buscar tarea")
        print("6. Salir")
        
        opcion = input("\nSeleccione una opción (1-6): ").strip()
        
        if opcion == "1":
            titulo = input("Ingrese el título de la tarea: ").strip()
            try:
                tarea = manager.crear_tarea(titulo)
                print(f"Tarea creada con ID: {tarea['id']}\n{json.dumps(tarea, indent=2, ensure_ascii=False)}")
            except ValueError as e:
                print(f"Error: {e}")
        
        elif opcion == "2":
            tareas = manager.listar_tareas()
            if not tareas:
                print("No hay tareas registradas.")
            else:
                print(f"\n--- {len(tareas)} tarea(s) ---")
                for t in tareas:
                    estado = "✓ COMPLETADA" if t["completa"] else "PENDIENTE"
                    print(f"[{t['id']}] {t['titulo']} | {estado}")
        
        elif opcion == "3":
            tareas = manager.listar_tareas()
            if not tareas:
                print("No hay tareas.")
                continue
            
            ids_disponibles = ", ".join(str(t["id"]) for t in tareas)
            tarea_id = input(f"Ingrese el ID de la tarea a completar (disponibles: {ids_disponibles}): ").strip()
            
            if tarea_id.isdigit():
                resultado = manager.completar_tarea(int(tarea_id))
                if resultado:
                    print(f"Tarea {tarea_id} marcada como completada.\n{json.dumps(resultado, indent=2, ensure_ascii=False)}")
                else:
                    print(f"No se encontró una tarea con ID: {tarea_id}")
        
        elif opcion == "4":
            tareas = manager.listar_tareas()
            if not tareas:
                print("No hay tareas.")
                continue
            
            ids_disponibles = ", ".join(str(t["id"]) for t in tareas)
            tarea_id = input(f"Ingrese el ID de la tarea a eliminar (disponibles: {ids_disponibles}): ").strip()
            
            if tarea_id.isdigit():
                if manager.eliminar_tarea(int(tarea_id)):
                    print(f"Tarea {tarea_id} eliminada correctamente.")
                else:
                    print(f"No se encontró una tarea con ID: {tarea_id}")
        
        elif opcion == "5":
            par = input("Ingrese texto para buscar en las tareas: ").strip()
            resultados = manager.buscar_por_titulo(par)
            if not resultados:
                print(f"No hay tareas que contengan: '{par}'")
            else:
                print(f"\n--- {len(resultados)} tarea(s) encontrada(s) ---")
                for r in resultados:
                    estado = "✓ COMPLETADA" if r["completa"] else "PENDIENTE"
                    print(f"[{r['id']}] {r['titulo']} | {estado}")
        
        elif opcion == "6":
            print("Saliendo...")
            break
        
        if opcion not in ("1", "2", "3", "4", "5", "6"):
            print("Opción no válida.")


if __name__ == "__main__":
    main()
