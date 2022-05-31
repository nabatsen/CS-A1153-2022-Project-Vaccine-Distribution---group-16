from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
from dateutil import relativedelta


def main():
    try:
        pd.options.display.max_columns = 500
        pd.options.display.width = 0
        DIALECT = "postgresql+psycopg2://"
        database = "grp16_vaccinedist"
        user = "grp16"
        host = "dbcourse2022.cs.aalto.fi"
        password = input("Enter password:")
        uri = "%s:%s@%s/%s" % (user, password, host, database)
        engine = create_engine(DIALECT + uri)
        conn = engine.connect()

        # Task 1
        PatientSymptoms_df = pd.read_sql_query(""" SELECT ssNo AS ssNO, gender, birthday AS dateOfBirth, symptom, 
                                                          date AS diagnosisDate
                                                   FROM Patient, Diagnosis 
                                                   WHERE patient = ssNo;""", conn)
        PatientSymptoms_df.to_sql("PatientSymptoms", conn, index=True, if_exists="replace")
        print("Task 1")
        print(PatientSymptoms_df)
        print("------------------------------------------------------------------------------------------------------")

        # Task 2
        conn.execute(""" CREATE TEMPORARY TABLE PatientAppointment AS  
                         SELECT ssNo, VA.date, Vaccine.name AS vaccinetype 
                         FROM Patient, VaccinationAppointment AS VA, VaccinationEvent AS VE, Batch, Vaccine
                         WHERE ssNo = patient AND VA.vaccinationPoint = VE.vaccinationPoint AND VA.date = VE.date 
                         AND VE.batch = Batch.id  AND Batch.vaccine = Vaccine.id;""")
        conn.execute(""" CREATE TEMPORARY TABLE FirstAppointment AS  
                         SELECT *
                         FROM PatientAppointment AS PA
                         WHERE NOT EXISTS(
                            SELECT * 
                            FROM PatientAppointment
                            WHERE PatientAppointment.ssNo = PA.ssNo AND PatientAppointment.date < PA.date);""")
        conn.execute(""" CREATE TEMPORARY TABLE NotFirstAppointment AS
                         SELECT * 
                         FROM PatientAppointment
                         EXCEPT 
                         SELECT *
                         FROM FirstAppointment;""")
        conn.execute(""" CREATE TEMPORARY TABLE SecondAppointment AS  
                         SELECT *
                         FROM NotFirstAppointment AS NFA
                         WHERE NOT EXISTS(
                            SELECT * 
                            FROM NotFirstAppointment
                            WHERE NotFirstAppointment.ssNo = NFA.ssNo AND NotFirstAppointment.date < NFA.date);""")
        PatientVaccineInfo_df = pd.read_sql_query(
            """ SELECT Patient.ssNo AS patientssNO, FirstAppointment.date AS date1, FirstAppointment.vaccinetype AS vaccinetype1,
                       SecondAppointment.date AS date2, SecondAppointment.vaccinetype AS vaccinetype2
                FROM Patient LEFT JOIN FirstAppointment ON Patient.ssNO = FirstAppointment.ssNo 
                             LEFT JOIN SecondAppointment ON FirstAppointment.ssNo = SecondAppointment.ssNo;""", conn)
        PatientVaccineInfo_df.to_sql("PatientVaccineInfo", conn, index=True, if_exists="replace")
        print("Task 2")
        print(PatientVaccineInfo_df)
        print("------------------------------------------------------------------------------------------------------")

        # Task 3
        PatientSymptoms_df = pd.read_sql_query(""" SELECT *
                                                   FROM "PatientSymptoms";""", conn)
        MaleSymptoms = PatientSymptoms_df[PatientSymptoms_df["gender"] == "M"]
        FemaleSymptoms = PatientSymptoms_df[PatientSymptoms_df["gender"] == "F"]
        MaleSymptomsTop3 = MaleSymptoms.groupby("symptom").agg({"ssno": "count"}).sort_values("ssno", ascending=False).head(3)
        FemaleSymptomsTop3 = FemaleSymptoms.groupby("symptom").agg({"ssno": "count"}).sort_values("ssno", ascending=False).head(3)
        MaleSymptomsTop3.rename(columns={"ssno": "count"}, inplace=True)
        FemaleSymptomsTop3.rename(columns={"ssno": "count"}, inplace=True)
        print("Task 3")
        print("Female Symptoms")
        print(FemaleSymptoms)
        print("Top 3 Female Symptoms")
        print(FemaleSymptomsTop3)
        print("Male Symptoms")
        print(MaleSymptoms)
        print("Top 3 Male Symptoms")
        print(MaleSymptomsTop3)
        print("------------------------------------------------------------------------------------------------------")

        # Task 4
        Patient_df = pd.read_sql_query(""" SELECT * FROM patient;""", conn)
        AgeColumn = Patient_df["birthday"].apply(lambda b: relativedelta.relativedelta(datetime.now(), datetime.strptime(b, "%Y-%m-%d")).years)
        Patient_df["ageGroup"] = pd.cut(AgeColumn, [0, 10, 20, 40, 60, 200], labels=["0-9", "10-19", "20-39", "40-59", "60+"], right=False)
        print("Task 4")
        print(Patient_df)
        print("------------------------------------------------------------------------------------------------------")

        # Task 5
        VaccineStatus = PatientVaccineInfo_df[["patientssno", "date1", "date2"]].apply(
            lambda r: pd.Series([r[0], (1 if r[1] else 0) + (1 if r[2] else 0)], ["ssno", "vaccinationStatus"]), axis=1)
        PatientVaccineStatus = pd.merge(Patient_df, VaccineStatus, on="ssno")
        print("Task 5")
        print(PatientVaccineStatus)
        print("------------------------------------------------------------------------------------------------------")

        # Task 6
        percentages = PatientVaccineStatus.groupby(["ageGroup", "vaccinationStatus"]).aggregate({"ssno": "count"}).reset_index()
        percentages["ssno"] = percentages["ssno"] / percentages.groupby("ageGroup")["ssno"].transform("sum") * 100
        percentages.rename(columns={"ssno": "percent"}, inplace=True)
        percentages["percent"] = percentages["percent"].apply(lambda v: "{:.2f}".format(v) + "%" if v == v else "-")
        percentages = percentages.pivot(index="vaccinationStatus", columns="ageGroup", values="percent")
        print("Task 6")
        print(percentages)
        print("------------------------------------------------------------------------------------------------------")

        # Task 7
        ##########
        Frequency = pd.read_sql_query("""WITH Tables AS(SELECT VA.patient as patientid, Vaccine.name, VA.date
                                        FROM VaccinationAppointment VA
                                        JOIN VaccinationEvent VE ON VE.date = VA.date AND VE.vaccinationPoint = VA.vaccinationPoint
                                        JOIN Batch ON Batch.id = VE.batch
                                        JOIN Vaccine ON Vaccine.id = Batch.vaccine
                                        ),
                                        SymptomOccurences AS(SELECT name, symptom, COUNT(DISTINCT(Tables.patientid)) AS total
                                        FROM Tables JOIN Diagnosis D ON D.patient = Tables.patientID AND D.date > Tables.date
                                        GROUP BY name, symptom),
                                        TotalVaccinations AS(SELECT name, COUNT(DISTINCT(patientid)) AS total
                                        FROM Tables GROUP BY name)
                                        SELECT SO.name AS "Vaccine", SO.symptom,
                                        ROUND(SO.total*1.0/TV.total, 6) AS "Frequency"
                                        FROM SymptomOccurences AS SO JOIN TotalVaccinations AS TV ON SO.name = TV.name;""", conn)

        Frequency.to_sql("Frequency", conn, index=True, if_exists="replace")  # dataframe
        Symptoms = pd.read_sql_query("""SELECT name AS symptom FROM Symptom ORDER BY name;""", conn)
        Symptoms.to_sql("Symptoms", conn, index=True, if_exists="replace")
        
        FreqAstra = Frequency[:13].reset_index().drop(columns=['index', 'Vaccine']).sort_values(by=['symptom'])
        FreqComirnaty = Frequency[14:23].reset_index().drop(columns=['index', 'Vaccine']).sort_values(by=['symptom'])
        FreqModerna = Frequency[24:].reset_index().drop(columns=['index', 'Vaccine']).sort_values(by=['symptom'])
        merge_df = pd.merge(Symptoms, FreqAstra, how='left', on='symptom')
        merge_df = pd.merge(merge_df, FreqComirnaty, how='left', on='symptom')
        merge_df = pd.merge(merge_df, FreqModerna, how='left', on='symptom')
        merge_df.rename(columns={"Frequency_x": "V01", "Frequency_y": "V02", "Frequency": "V03"}, inplace=True)
        cols = ['V01', 'V02', 'V03']
        merge_df[cols] = merge_df[cols].apply(pd.to_numeric, errors='coerce', axis=1)
        merge_df['V01'] = pd.cut(merge_df['V01'], [0.0, 0.05, 0.1, 1], labels=["rare", "common", "very common"],
                                 right=False).values.add_categories('-')
        merge_df['V02'] = pd.cut(merge_df['V02'], [0.0001, 0.05, 0.1, 1], labels=["rare", "common", "very common"],
                                 right=False).values.add_categories('-')
        merge_df['V03'] = pd.cut(merge_df['V03'], [0.0001, 0.05, 0.1, 1], labels=["rare", "common", "very common"],
                                 right=False).values.add_categories('-')
        merge_df = merge_df.fillna('-')
        ##########
        print("Task 7\n")
        print(merge_df)
        print("------------------------------------------------------------------------------------------------------")
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()


main()
