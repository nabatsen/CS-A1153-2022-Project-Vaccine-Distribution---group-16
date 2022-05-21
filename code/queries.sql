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
