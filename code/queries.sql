SELECT ssNo, name, phone, role, vaccinationStatus, Employee.vaccinationPoint AS vaccinationPoint
FROM Employee, Shift, VaccinationEvent
WHERE date = '2021-05-10' AND VaccinationEvent.vaccinationPoint = Employee.vaccinationPoint
    AND Shift.employee = ssNo AND weekday = 'Monday';

SELECT Employee.name AS doctor
FROM Employee, Shift, VaccinationPoint
WHERE Employee.vaccinationPoint = VaccinationPoint.name AND Shift.employee = ssNo AND weekday = 'Wednesday'
    AND role = 'doctor' AND address LIKE '%HELSINKI%';

SELECT id, location AS currentLocation, arrivalPoint AS latestArrivalLocation
FROM Batch LEFT JOIN TransportationLog AS T ON id = batch
WHERE NOT EXISTS(
    SELECT 1
    FROM TransportationLog
    WHERE TransportationLog.batch = T.batch AND TransportationLog.arrivalDate > T.arrivalDate
)
ORDER BY id;

SELECT id, phone
FROM Batch, VaccinationPoint, TransportationLog AS T
WHERE id = batch AND name = arrivalPoint AND NOT EXISTS(
    SELECT 1
    FROM TransportationLog
    WHERE TransportationLog.batch = T.batch AND TransportationLog.arrivalDate > T.arrivalDate
) AND location != arrivalPoint
ORDER BY id;

-- Query 6
SELECT location AS "Hospital/Clinic", name AS vaccine, total AS "No. of vaccines of different types", SUM(total) OVER (PARTITION BY location) AS "No. of Vaccine" 
FROM(SELECT location, Vaccine.name, SUM(amount) AS total 
        FROM Batch JOIN Vaccine ON Vaccine.id = Batch.vaccine 
        GROUP BY location, Vaccine.name) AS tempTable;

--Query 7
WITH Tables AS(SELECT VA.patient as patientid, Vaccine.name, symptom FROM VaccinationAppointment VA 
    JOIN VaccinationEvent VE ON VE.date = VA.date AND VE.vaccinationPoint = VA.vaccinationPoint
    JOIN Batch ON Batch.id = VE.batch
    JOIN Vaccine ON Vaccine.id = Batch.vaccine
    JOIN Diagnosis D ON D.patient = VA.patient AND D.date > VA.date), 
    Calculation AS(SELECT name, COUNT(DISTINCT(tables.patientid)) AS total 
        FROM Tables GROUP BY name),
    Types AS(SELECT name, symptom, COUNT(DISTINCT(tables.patientid)) AS total 
        FROM Tables GROUP BY name, symptom) 
SELECT Types.name AS "Vaccine", Types.symptom, 
ROUND(Types.total*1.0/Calculation.total, 6) AS "Frequency"
FROM Types JOIN Calculation ON Types.name = Calculation.name;