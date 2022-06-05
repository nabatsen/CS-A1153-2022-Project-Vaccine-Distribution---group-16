from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
from dateutil import relativedelta
import numpy as np

import matplotlib.pyplot as plt
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

        # Task 8
        # From Vaccination Event, we know there are 5 days across 6 vaccination points, and there will be total 8
        # vaccination events happen. I will implement query that find number of registered patient and the amount of
        # vaccine in the batch that the vaccination point will use at a specific date. The date and vaccination point
        # are from the table VaccinationEvent.

        # Information from VaccinationEvent table
        VaccinationEvent = pd.read_sql_query("""SELECT * FROM VaccinationEvent;""", conn)
        VaccinationEvent.to_sql("VaccinationEvent", conn, index=False, if_exists="replace")

        # Get amount of vaccine and type
        messukeskus_d1 = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                            VaccinationEvent WHERE date='2021-01-30' AND vaccinationPoint='Messukeskus');""", conn)
        messukeskus_d2 = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                    VaccinationEvent WHERE date='2021-02-14' AND vaccinationPoint='Messukeskus');""",
                                           conn)
        tapiola_d1 = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                    VaccinationEvent WHERE date='2021-03-16' AND vaccinationPoint='Tapiola Health Center');""",
                                           conn)
        tapiola_d2 = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                            VaccinationEvent WHERE date='2021-05-10' AND vaccinationPoint='Tapiola Health Center');""",
                                       conn)
        myyrmaki = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                    VaccinationEvent WHERE vaccinationPoint='Myyrmäki Energia Areena');""", conn)
        malmi = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                    VaccinationEvent WHERE vaccinationPoint='Malmi');""", conn)
        iso_omena = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                    VaccinationEvent WHERE vaccinationPoint='Iso Omena Vaccination Point');""", conn)
        sanomala = pd.read_sql_query("""SELECT vaccine, amount FROM Batch WHERE id IN (SELECT batch FROM 
                                    VaccinationEvent WHERE vaccinationPoint='Sanomala Vaccination Point');""", conn)

        # Get number of registered patient
        p_messu_d1 = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.date='2021-01-30' AND VA.vaccinationPoint='Messukeskus';""", conn)
        p_messu_d2 = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.date='2021-02-14' AND VA.vaccinationPoint='Messukeskus';""", conn)
        p_tapiola_d1 = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.date='2021-03-16' AND VA.vaccinationPoint='Tapiola Health Center';""", conn)
        p_tapiola_d2 = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.date='2021-05-10' AND VA.vaccinationPoint='Tapiola Health Center';""", conn)
        p_myyrmaki = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.vaccinationPoint='Myyrmäki Energia Areena';""", conn)
        p_malmi = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.vaccinationPoint='Malmi';""", conn)
        p_isoomena = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.vaccinationPoint='Iso Omena Vaccination Point';""", conn)
        p_sanomala = pd.read_sql_query("""SELECT COUNT(patient) FROM VaccinationAppointment AS VA WHERE 
                                        VA.vaccinationPoint='Sanomala Vaccination Point';""", conn)

        # For V01: Messukeskus on 2021-01-30, Sanomala on 2021-05-10, Tapiola Health Center on 2021-03-16
        # For V02: Tapiola Health Center on 2021-05-10, Myyramaki Energua Areena on 2021-05-10
        # For V03: Iso Omena on 2021-05-14, Malmi on 2021-01-30, Messukeskus on 2021-02-14

        V01_amount = [messukeskus_d1['amount'].iloc[0], sanomala['amount'].iloc[0], tapiola_d1['amount'].iloc[0]]
        V02_amount = [tapiola_d2['amount'].iloc[0], myyrmaki['amount'].iloc[0]]
        V03_amount = [iso_omena['amount'].iloc[0], malmi['amount'].iloc[0], messukeskus_d2['amount'].iloc[0]]

        V01_patient = [p_messu_d1['count'].iloc[0], p_sanomala['count'].iloc[0], p_tapiola_d1['count'].iloc[0]]
        V02_patient = [p_tapiola_d2['count'].iloc[0], p_myyrmaki['count'].iloc[0]]
        V03_patient = [p_isoomena['count'].iloc[0], p_malmi['count'].iloc[0], p_messu_d2['count'].iloc[0]]

        V01_percentage = [V01_patient[0]*100/V01_amount[0], V01_patient[1]*100/V01_amount[1],
                          V01_patient[2]*100/V01_amount[2]]
        V02_percentage = [V02_patient[0] * 100 / V02_amount[0], V02_patient[1] * 100 / V02_amount[1]]
        V03_percentage = [V03_patient[0] * 100 / V03_amount[0], V03_patient[1] * 100 / V03_amount[1],
                          V03_patient[2] * 100 / V03_amount[2]]

        V01_expected = np.mean(V01_percentage) + np.std(V01_percentage)
        V02_expected = np.mean(V02_percentage) + np.std(V02_percentage)
        V03_expected = np.mean(V03_percentage) + np.std(V03_percentage)

        # Print result
        print('Task 8\n')
        print('Base information from VaccinationEvent table:')
        print(VaccinationEvent, '\n')
        print('Estimation')

        print('V01: {:.5f}%'.format(V01_expected))
        print('V02: {:.5f}%'.format(V02_expected))
        print('V03: {:.5f}%'.format(V03_expected))
        print("------------------------------------------------------------------------------------------------------")
        
        # Task 9: 
        PatientVaccineInfoDF = pd.read_sql("""SELECT * FROM "PatientVaccineInfo"; """, engine)
        # print(PatientVaccineInfoDF['date1'].values.tolist())
        # print(PatientVaccineInfoDF['date2'].values.tolist())
        date1List = PatientVaccineInfoDF['date1'].values.tolist()
        date2List = PatientVaccineInfoDF['date2'].values.tolist()
        
        date1Dictionary = {}
        for i in date1List:
            if i != None:
                date1Dictionary[i] = date1List.count(i)
        
        date2Dictionary = {}
        for i in date2List:
            if i != None:
                date2Dictionary[i] = date2List.count(i)
        
        vaccinatedDictionary = {}
        
        for i in date1Dictionary:
            if i in date2Dictionary:
                vaccinatedDictionary[i] = date1Dictionary[i] + date2Dictionary[i]
            else:
                vaccinatedDictionary[i] = date1Dictionary[i]
        
        mainList = vaccinatedDictionary.items()
        mainList = sorted(mainList)
        x , y = zip(*mainList)        
        plt.plot(x,y)
        plt.xlabel('Date')
        plt.ylabel('Vaccinated Patients at Date')
        plt.title('Vaccinations according to date')
        plt.show()
    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()


main()
