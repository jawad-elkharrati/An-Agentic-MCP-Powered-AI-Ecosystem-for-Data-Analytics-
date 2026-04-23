# app/orchestrator/engine.py
from app.orchestrator.models  import RunState
from app.orchestrator.planner import Planner
from app.orchestrator.router  import Router
import json
import os


class Engine:
    """
    La boucle principale du pipeline.
    Ordre : data_engineer → data_scientist → bi_agent (skip) → reporter (skip)
    """

    def __init__(self):
        self.planner = Planner()
        self.router  = Router()

    def run(self, file_path: str, run_id: str) -> dict:

        print(f"\n{'='*55}")
        print(f"  ENGINE DEMARRE — run_id : {run_id}")
        print(f"  Fichier : {file_path}")
        print(f"{'='*55}\n")

        state = RunState(run_id=run_id, file_path=file_path)
        print(f"[Engine] Taches a faire : {state.pending}\n")

        # Contexte partagé entre les agents
        context = {
            "run_id"      : run_id,
            "dataset_path": file_path,
            "artifacts"   : {},
        }

        while not state.is_finished():

            task = self.planner.next_task(state)
            if not task:
                break

            state.current = task
            print(f"\n[Engine] Lancement : {task}")

            agent = self.router.get_agent(task, run_id)

            if agent is None:
                # Agent pas encore codé — skip
                print(f"[Engine] Skip '{task}' — agent non disponible\n")
                state.pending.remove(task)
                state.completed.append(task + "_skipped")
                continue

            try:

                # ── data_engineer ─────────────────────────────────────────
                if task == "data_engineer":
                    result = agent.run(file_path)

                    if result.get("status") == "success":
                        clean_path = result["clean_path"]
                        state.mark_done(task, {
                            "clean_csv"     : clean_path,
                            "quality_score" : str(result.get("quality_score", "")),
                            "final_rows"    : str(result.get("final_rows", "")),
                        })
                        context["artifacts"]["last_file"]     = clean_path
                        context["artifacts"]["data_engineer"] = result
                        print(f"[Engine] '{task}' termine ✓")
                        print(f"[Engine] Artifact : {clean_path}")
                    else:
                        error = result.get("error", "Erreur inconnue")
                        print(f"[Engine] ERREUR dans '{task}' : {error}")
                        state.errors.append(f"{task}: {error}")
                        break

                # ── data_scientist ────────────────────────────────────────
                elif task == "data_scientist":
                    ds_context = {
                        "run_id"      : run_id,
                        "dataset_path": file_path,
                        "artifacts"   : context["artifacts"],
                    }
                    result = agent.run(step=task, context=ds_context)

                    if result.get("success", False):
                        state.mark_done(task, {
                            "insights_json": result.get("output_path", ""),
                            "CA_total"     : str(result.get("kpis", {}).get("CA_total", "")),
                        })
                        context["artifacts"]["last_file"]      = result.get("output_path", "")
                        context["artifacts"]["data_scientist"] = result
                        print(f"[Engine] '{task}' termine ✓")
                        print(f"[Engine] CA total : {result.get('kpis', {}).get('CA_total', 'N/A')}")
                    else:
                        error = result.get("error", "Erreur inconnue")
                        print(f"[Engine] ERREUR dans '{task}' : {error}")
                        state.errors.append(f"{task}: {error}")
                        break

            except Exception as e:
                print(f"[Engine] Exception dans '{task}' : {e}")
                state.errors.append(f"{task}: {str(e)}")
                break

        # Fin du pipeline
        state.status = "completed" if not state.errors else "failed"

        print(f"\n{'='*55}")
        print(f"  PIPELINE TERMINE — statut : {state.status}")
        print(f"  Taches terminees : {state.completed}")
        print(f"{'='*55}\n")

        self._save_summary(state)
        return state.summary()

    def _save_summary(self, state: RunState):
        run_dir = f"runs/{state.run_id}"
        os.makedirs(run_dir, exist_ok=True)
        path = f"{run_dir}/metadata.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state.summary(), f, indent=2, ensure_ascii=False)
        print(f"[Engine] Metadata sauvegarde : {path}")
