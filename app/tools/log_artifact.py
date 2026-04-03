# app/tools/log_artifact.py
from app.storage.artifact_store import ArtifactStore
from app.orchestrator.models import Artifact
import uuid
import os
import json

store = ArtifactStore()

def log_artifact(
    run_id       : str,
    artifact_type: str = "generic",   # ← type → artifact_type (mot réservé Python)
    path         : str = "",
    producer     : str = "",
    metadata     : dict = {}
) -> dict:

    # Si le fichier est un JSON d'insights → enrichir metadata
    if os.path.exists(path) and path.endswith(".json"):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                if "kpis"     in data: metadata["kpis"]     = data["kpis"]
                if "alertes"  in data: metadata["alertes"]  = data["alertes"]
                if "insights" in data: metadata["insights"] = data["insights"]
        except Exception as e:
            metadata["read_error"] = str(e)

    # Type automatique pour insights.json
    if artifact_type == "generic" and path.endswith("insights.json"):
        artifact_type = "insights"

    artifact = Artifact(
        artifact_id = str(uuid.uuid4())[:8],
        type        = artifact_type,
        path        = path,
        producer    = producer,
        metadata    = metadata
    )

    store.save_artifact(run_id, artifact)

    print(f"[log_artifact] {producer} → {artifact_type} : {path}")

    return {
        "artifact_id": artifact.artifact_id,
        "saved"      : True,
        "type"       : artifact_type,
        "path"       : path,
        "metadata"   : metadata
    }
