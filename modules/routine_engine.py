"""
modules/routine_engine.py — Phase 4: YAML routine loader and executor
Loads routines.yaml and executes a predefined list of dispatcher actions.
"""

import yaml
import os

class RoutineEngine:
    """Loads and executes YAML-defined routines."""

    def __init__(self, routines_path="routines.yaml"):
        # Resolve absolute path relative to project root
        filepath = routines_path
        if not os.path.isabs(routines_path):
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                routines_path,
            )
            
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.routines = data.get("routines", {})
            
    def run(self, routine_name: str, dispatcher) -> str:
        """
        Execute all steps in a given routine sequentially.
        """
        if routine_name not in self.routines:
            msg = f"Routine error: '{routine_name}' not found in routines.yaml"
            print(f"[RoutineEngine] {msg}")
            return msg
            
        steps = self.routines[routine_name].get("steps", [])
        if not steps:
            msg = f"Routine error: '{routine_name}' has no steps."
            print(f"[RoutineEngine] {msg}")
            return msg
            
        print(f"[RoutineEngine] Starting routine: {routine_name} ({len(steps)} steps)")
        
        for index, step in enumerate(steps, start=1):
            print(f"[RoutineEngine]   Step {index}: {step.get('action')}")
            try:
                # The steps from YAML are already dictionaries with 'action' and parameters
                result = dispatcher._execute_action(step)
                print(f"[RoutineEngine]     → {result}")
            except Exception as e:
                print(f"[RoutineEngine]     → Step {index} failed: {e}")
                
        return f"Routine '{routine_name}' completed."
