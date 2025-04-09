from pymysql.cursors import DictCursor
import pymysql
from collections import defaultdict

connexion = pymysql.connect(
    host="EC****30",
    user="****",
    password="****",
    database="****",
    port=3306,
    cursorclass=DictCursor
)

try:
    with connexion.cursor() as cursor:
        cursor.execute("""
            SELECT
                DATE(p.last_updated) AS date_prescription,
                pat.family
            FROM
                prescriptions p
            JOIN
                patients pat ON p.patient_id = pat.id
            ORDER BY
                date_prescription;
        """)

        resultats = cursor.fetchall()

        # Regrouper les noms de famille par date
        prescriptions_par_jour = defaultdict(list)

        for ligne in resultats:
            date = ligne['date_prescription'].strftime('%Y-%m-%d')
            prescriptions_par_jour[date].append(ligne['family'])

        # Affichage
        for date, noms in prescriptions_par_jour.items():
            print(f"{date} : {len(noms)} prescriptions")
            for nom in noms:
                print(f"   - {nom}")

finally:
    connexion.close()