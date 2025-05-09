
from flask import Flask, render_template, jsonify
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
import os
from dotenv import load_dotenv
from datetime import timezone, timedelta
import datetime
from models_extended import *  # models_extended herite de models (genere via sqlacodegen script .ps1). Herite de models mais aussi de utils_mixin qui elle contient des fonctions de type to_dict()


# Charger les variables denvironnement
load_dotenv()

# Creer la session
DATABASE_URL = f"mysql+pymysql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}/{os.getenv('DATABASE_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = Flask(__name__)


def get_dose_summary(volumes_and_doses):
    """
    Fonction pour extraire les totaldosevalue des volumes_and_doses,
    trier les valeurs et renvoyer une chaine sous la forme de valeurs triees
    sans doublon, ou une seule valeur si necessaire.
    """
    # Extraire les valeurs totaldosevalue de la liste volumes_and_doses
    doses = {vd['totaldosevalue'] /100 for vd in volumes_and_doses if 'totaldosevalue' in vd}
    
    # Si la liste des doses est vide, retourner une valeur par defaut
    if not doses:
        return "N/A"
    
    # Si une seule valeur, la retourner seule
    if len(doses) == 1:
        return str(next(iter(doses))) + " Gy" 
    
    # Trier les doses par ordre decroissant et les joindre avec '/'
    doses_sorted = sorted(doses, reverse=True)
    return '/'.join(map(str, doses_sorted)) + " Gy"



@app.route('/get_patient_events/<int:patient_id>', methods=['GET'])
def get_patient_events(patient_id):
    session = SessionLocal()
    patient = session.query(Patients).filter_by(id=patient_id).first()
    if patient:
        events = []
        for event in patient.events:
            events.append(
            {"event_type": event.event_type, "timestamp": event.last_updated.strftime('%Y-%m-%d %H:%M:%S') }
            )           
    session.close() 
    return jsonify({"events": events})


@app.route("/get_patient_tasks/<int:patient_id>")  
def get_patient_tasks(patient_id):
    session = SessionLocal()
    patient = session.query(Patients).filter_by(id=patient_id).first()

    if not patient:
        print("Patient non trouve.")
        return jsonify({"timeline": []})

    # Calcul de la date un mois avant aujourdhui
    one_month_ago = datetime.datetime.utcnow() - timedelta(days=30)

    # Recuperer les careplans mis a jour depuis un mois
    recent_careplans = [
        cp for cp in patient.careplans if cp.last_updated >= one_month_ago
    ]

    if not recent_careplans:
        session.close()
        return jsonify({"timeline": []})

    # Construire la timeline avec une liste par careplan
    data = {"timeline": []}
    all_tasks = [] 

    for careplan in recent_careplans:
        careplan_timeline = {
            "careplan_id": careplan.id,
            "careplan_name":careplan.title,
            "last_updated": careplan.last_updated.strftime('%Y-%m-%d'),
            "tasks": []
        }

        for task in careplan.tasks:
            careplan_timeline["tasks"].append({
                "status": task.status,
                "name": task.display_focus,
                "timestamp": task.last_updated.strftime('%Y-%m-%d')
            })

        data["timeline"].append(careplan_timeline)

    session.close()
    return jsonify(data)


#---------------------------------------
@app.route('/get_patient_prescriptions/<int:patient_id>')
def get_patient_prescriptions(patient_id):
    session = SessionLocal()
    patient = session.query(Patients).options(joinedload(Patients.prescriptions)).filter_by(id=patient_id).first()
    if not patient or not patient.prescriptions:
        return jsonify({"prescriptions": []})
    prescriptions_data = [
    {
        **pres.to_dict(),  # Inclure toutes les donnees de prescription
        "dose_summary": get_dose_summary(pres.volumes_and_doses)  # Ajouter la cle 'dose_summary'
    }
    for pres in sorted(patient.prescriptions, key=lambda p: p.last_updated, reverse=True)
    ]

    #print(f"DEBUG - JSON response: {json.dumps({'prescriptions': prescriptions_data}, indent=4)}")
    return jsonify({"prescriptions": prescriptions_data})


    

#----------------------------------------
@app.route("/")
def home():
    session = SessionLocal()
    
    query_results = (
        session.query(Patients)
        .options(joinedload(Patients.appointments), joinedload(Patients.careplans).joinedload(Careplans.tasks),joinedload(Patients.prescriptions))
        .all()
    )

    today = datetime.datetime.today()
    one_month_ago = today - timedelta(days=30)  # Date de reference pour les careplans actifs. Si les careplans sont trop vieux alors ne pas prendre

    patients = []
    for patient in query_results:
        # Recuperation des careplans actifs mis a jour dans les 30 derniers jours
        active_careplans = [cp for cp in patient.careplans if cp.last_updated >= one_month_ago]

        # Recherche de la derniere tache active parmi ces careplans
        last_active_task = None
        last_active_careplan_name = None

        for careplan in active_careplans:
            ready_tasks = [task for task in careplan.tasks if task.status == "ready"]
            in_progress_tasks = [task for task in careplan.tasks if task.status == "in-progress"]

            if ready_tasks:
                last_active_task = max(ready_tasks, key=lambda t: t.last_updated)
            elif in_progress_tasks:
                last_active_task = max(in_progress_tasks, key=lambda t: t.last_updated)

            if last_active_task:
                last_active_careplan_name = careplan.title
                break  # On garde la premiere tache trouvee avec priorite

        # Formatage des donnees patient envoyees dans mon html
        patient_datas = {
            "id": patient.id,
            "family": f"{patient.family_name_official}, {patient.given}",
            "ipp": patient.ipp,
            "birth_date": patient.birth_date,
            "appointments": [
                {
                    "id": appt.id,
                    "date": appt.start_scheduled_period if appt.start_scheduled_period else "N/A",
                    "code": appt.code
                }
                for appt in patient.appointments
            ] if patient.appointments else None,
            "last_active_task": 
            {
                "name": last_active_task.display_focus if last_active_task else "Aucun wf en cours",
                "careplan_name": last_active_careplan_name if last_active_task else ""
            },
            "prescriptions": [
                {
                    **pres.to_dict(),  # Inclure toutes les donnees de prescription
                    "dose_summary": get_dose_summary(pres.volumes_and_doses)  # Ajouter la cle 'dose_summary'
                }
                for pres in patient.prescriptions
            ] if patient.prescriptions else [],

        }
        patients.append(patient_datas)

    session.close()
    return render_template("web_main4.html", patients=patients)



if __name__ == "__main__":
    session = SessionLocal()
   

    app.run(debug=True)