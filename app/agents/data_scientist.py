import json
import re
from app.agents.base_agent import BaseAgent



DATA_SCIENTIST_TOOLS = [
    {
        "name": "run_analysis",
        "description": (
            "Analyse complète du dataset e-commerce nettoyé. Produit 4 sections : "
            "(1) data_quality : score global + détail par colonne (complétude, doublons) ; "
            "(2) kpis : CA total, CA par mois, CA par pays, panier moyen, taux annulation, "
            "taux retour, taux rétention, top 10 produits, variation MoM ; "
            "(3) anomalies : détection IQR sur colonnes numériques ; "
            "(4) chart_hints : suggestions de charts pour le dashboard BI. "
            "Génère les alertes warning/critical selon les seuils de monitoring. "
            "Sauvegarde tout dans runs/{run_id}/artifacts/insights.json."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Chemin vers le fichier CSV nettoyé à analyser."
                },
                "run_id": {
                    "type": "string",
                    "description": "Identifiant du run en cours (ex: 'run_001')."
                }
            },
            "required": ["file_path", "run_id"]
        }
    }
]


class DataScientistAgent(BaseAgent):
    """
    Agent LLM spécialisé dans le Data Quality Monitoring et la génération de KPIs.

    Thème : AI Multi-Agent System for Data Quality and Business KPI Monitoring
            with Automated Dashboard Generation

    Reçoit  → context de l'engine (run_id, artifacts["last_file"])
    Appelle → run_analysis via MCP
    Retourne→ dict avec data_quality, kpis, anomalies, alertes,
                         insights, chart_hints, output_path, success
    """

    agent_name = "data_scientist"

    system_prompt = """Tu es un Data Scientist expert en Data Quality Monitoring et KPI Business Analytics.

Tu travailles dans un système multi-agent dont le thème est :
"AI Multi-Agent System for Data Quality and Business KPI Monitoring with Automated Dashboard Generation"

Ton rôle dans le pipeline :
1. Recevoir un fichier CSV nettoyé et un run_id.
2. Appeler l'outil run_analysis avec file_path et run_id.
3. Analyser les résultats sur 4 axes :
   - Data Quality   : score global, colonnes problématiques, doublons
   - KPI Monitoring : CA, tendances, panier moyen, rétention, alertes
   - Anomalies      : colonnes avec valeurs aberrantes détectées
   - Dashboard      : chart_hints pour guider le BI Agent
4. Retourner un JSON structuré avec EXACTEMENT ces champs :
   {
     "data_quality" : { "score_global": ..., "nb_doublons": ..., "colonnes": {...} },
     "kpis"         : { "CA_total": ..., "panier_moyen": ..., ... },
     "anomalies"    : { "colonne": { "nb_anomalies": ..., "severite": ... } },
     "alertes"      : [ { "kpi": ..., "niveau": ..., "message": ... } ],
     "insights"     : [ "phrase 1", "phrase 2", ... ],
     "chart_hints"  : [ { "chart_id": ..., "type": ..., "title": ... } ],
     "output_path"  : "runs/run_001/artifacts/insights.json",
     "success"      : true
   }

Règles importantes :
- Appelle TOUJOURS run_analysis — ne calcule jamais les KPIs toi-même.
- Transmets fidèlement TOUS les champs retournés par run_analysis.
- Les chart_hints sont critiques : le BI Agent en a besoin pour générer le dashboard.
- Si run_analysis retourne une erreur, retourne success: false avec le message.
- Réponds TOUJOURS avec un JSON valide uniquement, sans texte autour."""

    def run(self, step: str, context: dict) -> dict:
        """
        Exécute l'analyse Data Quality + KPI Monitoring.

        context reçu de engine.py :
            - run_id                                    : str
            - artifacts["last_file"]                    : str  ← clean.csv
            - artifacts["data_engineer"]["output_path"] : str  ← fallback
            - dataset_path                              : str  ← fallback ultime
        """
        run_id = context.get("run_id", "run_unknown")

        file_path = (
            context.get("artifacts", {}).get("last_file")
            or context.get("artifacts", {})
                      .get("data_engineer", {})
                      .get("output_path")
            or context.get("dataset_path", "")
        )

        if not file_path:
            return {
                "success"     : False,
                "error"       : "Aucun fichier nettoyé trouvé dans le contexte.",
                "data_quality": {},
                "kpis"        : {},
                "anomalies"   : {},
                "alertes"     : [],
                "insights"    : [],
                "chart_hints" : []
            }

       
        task_description = (
            f"Effectue l'analyse Data Quality et KPI Monitoring du dataset e-commerce.\n\n"
            f"run_id    : {run_id}\n"
            f"file_path : {file_path}\n\n"
            f"Étapes :\n"
            f"1. Appelle run_analysis(file_path='{file_path}', run_id='{run_id}').\n"
            f"2. Récupère les 4 sections : data_quality, kpis, anomalies, chart_hints.\n"
            f"3. Retourne le JSON complet avec data_quality, kpis, anomalies, "
            f"alertes, insights, chart_hints, output_path et success."
        )

        messages = [{"role": "user", "content": task_description}]

        print(f"\n[data_scientist] Démarrage Data Quality + KPI Monitoring")
        print(f"[data_scientist] run={run_id} | fichier={file_path}")
        raw_output = self._run_loop(messages, DATA_SCIENTIST_TOOLS, run_id)
        print(f"[data_scientist] Terminé.")

        return self._parse_output(raw_output)

    # ─────────────────────────────────────────────────────────────────────────

    def _parse_output(self, raw: str) -> dict:
        """Extrait le JSON de la réponse de Claude."""

    
        match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

     
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {
            "success"     : False,
            "error"       : "Impossible de parser la sortie JSON de l'agent.",
            "raw_output"  : raw,
            "data_quality": {},
            "kpis"        : {},
            "anomalies"   : {},
            "alertes"     : [],
            "insights"    : [],
            "chart_hints" : []
        }
