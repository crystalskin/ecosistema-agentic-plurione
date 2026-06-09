from fastapi import FastAPI
from mlflow import MlflowClient
from datetime import datetime

app = FastAPI()

MLFLOW_URI = "http://localhost:5000"
EXPERIMENT_NAME = "AC06_FineTuning_IntencionClasificador"

def obtener_ultimo_run(client, experiment_id, status_tag):
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f"tags.status = '{status_tag}'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )
    if not runs:
        return None
    
    run = runs[0]
    fecha = datetime.fromtimestamp(run.info.start_time / 1000).strftime("%Y-%m-%d %H:%M")
    
    metricas = {}
    for key, val in run.data.metrics.items():
        metricas[key] = round(val, 4)
        
    return {
        "run_id": run.info.run_id[:8],
        "nombre": run.data.tags.get("mlflow.runName", "Desconocido"),
        "fecha": fecha,
        "status": status_tag,
        "metricas": metricas
    }

@app.get("/api/ml-status")
def get_ml_status():
    try:
        client = MlflowClient(tracking_uri=MLFLOW_URI)
        experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
        
        if not experiment:
            return {"error": "Experimento no encontrado"}
            
        exp_id = experiment.experiment_id
        
        return {
            "activo": obtener_ultimo_run(client, exp_id, "activo"),
            "candidato": obtener_ultimo_run(client, exp_id, "candidato"),
            "rechazado": obtener_ultimo_run(client, exp_id, "rechazado_rollback")
        }
    except Exception as e:
        return {"error": str(e)}