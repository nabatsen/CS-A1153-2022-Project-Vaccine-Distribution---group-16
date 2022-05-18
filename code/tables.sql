CREATE TABLE Manufacturer(
    id VARCHAR PRIMARY KEY,
    phone varchar NOT NULL
);

CREATE TABLE ProductionFacility(
    manufacturer VARCHAR REFERENCES Manufacturer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    country VARCHAR,
    PRIMARY KEY(manufacturer, country)
);

CREATE TABLE Vaccine(
    id VARCHAR PRIMARY KEY,
    requiredDoses INTEGER NOT NULL,
    tempMin INTEGER NOT NULL,
    tempMax INTEGER NOT NULL
);

CREATE TABLE License(
    manufacturer VARCHAR REFERENCES Manufacturer(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    vaccine VARCHAR REFERENCES Vaccine(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    PRIMARY KEY(manufacturer, vaccine)
);

CREATE TABLE Batch(
    id VARCHAR PRIMARY KEY,
    vaccine VARCHAR NOT NULL REFERENCES Vaccine(id) ON UPDATE CASCADE,
    amount INTEGER NOT NULL,
    manufacturer VARCHAR NOT NULL REFERENCES ProductionFacility(manufacturer) ON UPDATE CASCADE,
    country VARCHAR NOT NULL REFERENCES ProductionFacility(country),
    productionDate VARCHAR NOT NULL,
    expiryDate VARCHAR NOT NULL
);

CREATE TABLE VaccinationPoint(
    name VARCHAR PRIMARY KEY,
    address VARCHAR NOT NULL,
    phone VARCHAR NOT NULL
);

CREATE TABLE TransportationLog(
    batch VARCHAR REFERENCES Batch(id),
    departureDate VARCHAR,
    departurePoint VARCHAR REFERENCES VaccinationPoint(name) ON UPDATE CASCADE,
    arrivalDate VARCHAR,
    arrivalPoint VARCHAR REFERENCES VaccinationPoint(name) ON UPDATE CASCADE,
    PRIMARY KEY(batch, arrivalDate, arrivalPoint)
);

CREATE TABLE Employee(
    ssNo VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    birthday VARCHAR NOT NULL,
    phone VARCHAR NOT NULL,
    vaccinationStatus INTEGER NOT NULL,
    role VARCHAR NOT NULL CHECK(role IN ("doctor", "nurse"))
);

CREATE DOMAIN WeekdayDomain VARCHAR CHECK(VALUE IN ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"));

CREATE TABLE Shift(
    vaccinationPoint REFERENCES VaccinationPoint(name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    weekday WeekdayDomain,
    employee REFERENCES Employee(ssNo) ON DELETE CASCADE,
    PRIMARY KEY(vaccinationPoint,weekday,employee)
);

CREATE TABLE VaccinationEvent(
    date VARCHAR,
    point VARCHAR REFERENCES VaccinationPoint(name)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    batch VARCHAR NOT NULL REFERENCES Batch(id),
    PRIMARY KEY(date, point)
);

CREATE TABLE Patient(
    ssNo VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    birthday VARCHAR NOT NULL,
    gender CHAR(1) NOT NULL CHECK(gender IN ('F', 'M', 'O')),
    vaccinationStatus INTEGER NOT NULL,
);

CREATE TABLE VaccinationAppointment(
    patient VARCHAR REFERENCES Patient(ssNo) ON DELETE CASCADE,
    date VARCHAR REFERENCES VaccinationEvent(date)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    point VARCHAR REFERENCES VaccinationEvent(point)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    PRIMARY KEY (patient, date, point)
);

CREATE TABLE Symptom(
    patient VARCHAR REFERENCES Patient(ssNo) ON DELETE CASCADE,
    symptom VARCHAR,
    date VARCHAR,
    critical BOOLEAN NOT NULL,
    PRIMARY KEY(patient, symptom, date)
);
