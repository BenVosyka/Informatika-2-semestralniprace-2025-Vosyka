CREATE TABLE IF NOT EXISTS SystemCas (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    aktualni_datum TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Vozidlo (
    vozidlo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT UNIQUE NOT NULL,
    vpz TEXT UNIQUE NOT NULL,
    vyrobce TEXT,
    model TEXT,
    typ_vozidla TEXT NOT NULL,
    barva TEXT,
    pocet_kol INTEGER,
    rok INTEGER,
    aktivni INTEGER DEFAULT 1,
    aktualni_km INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ServisniPravidlo (
    pravidlo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    typ_vozidla TEXT NOT NULL,
    komponenta TEXT NOT NULL,
    interval_dni INTEGER NOT NULL,
    UNIQUE(typ_vozidla, komponenta)
);

CREATE TABLE IF NOT EXISTS ServisniZaznam (
    zaznam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vozidlo_id INTEGER NOT NULL,
    komponenta TEXT NOT NULL,
    posledni_servis TEXT NOT NULL,
    posledni_servis_km INTEGER,
    FOREIGN KEY (vozidlo_id) REFERENCES Vozidlo(vozidlo_id)
);

CREATE TABLE IF NOT EXISTS VstupniServis (
    vozidlo_id INTEGER PRIMARY KEY,
    vstupni_datum TEXT NOT NULL,
    FOREIGN KEY (vozidlo_id) REFERENCES Vozidlo(vozidlo_id)
);

CREATE TABLE IF NOT EXISTS KilometrovePravidlo (
    pravidlo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    typ_vozidla TEXT NOT NULL,
    komponenta TEXT NOT NULL,
    interval_km INTEGER NOT NULL,
    UNIQUE(typ_vozidla, komponenta)
);

CREATE TABLE IF NOT EXISTS ZivotnostVozidla (
    typ_vozidla TEXT PRIMARY KEY,
    zivotnost_km INTEGER NOT NULL
);

INSERT OR IGNORE INTO Vozidlo (vozidlo_id, vin, vpz, vyrobce, model, typ_vozidla, barva, pocet_kol, rok, aktualni_km)
VALUES 
    (1, 'TMBABCDEF3H123456', '212 97-56', 'Toyota'    , 'Hilux'    , 'sluzebni', 'zelena' , 4, 2022, 1050000),
    (2, 'TMBJCEGH5J2345670', '018 86-16', 'Land Rover', 'Defender' , 'takticke', 'zelena' , 4, 2016, 180000),
    (3, 'TMBAKDHG7K3456781', '212 77-43', 'Skoda'     , 'Fabia'    , 'sluzebni', 'cerna'  , 4, 2017, 85000),
    (4, 'TMBELFHJ9L4567892', '214 40-38', 'Tatra'     , '815-7'    , 'nakladni', 'zelena' , 6, 2023, 120000),
    (5, 'TMBGMGJK2M5678905', '026 09-83', 'Tatra'     , '810'      , 'nakladni', 'zelena' , 6, 2013, 180000),
    (6, 'TMBHNHHM4N6789017', '200 89-67', 'IVECO'     , 'LMV CZ5'  , 'takticke', 'piskova', 4, 2018, 95000),
    (7, 'TMBJPKJN6P7890124', '211 56-17', 'TDV'       , 'Pandur II', 'bojove'  , 'zelena' , 8, 2021, 120000),
    (8, 'TMBKRLKP8R8901239', '215 41-76', 'Nexter Systems', 'TITUS', 'takticke', 'piskova', 6, 2024, 60000),
    (9, 'TMBMSMKR1S9012343', '140 98-73', 'KMW'       , 'Dingo 2'  , 'takticke', 'zelena' , 4, 2008, 220000),
    (10, 'TMBNTNLS3T0123456', '084 72-60', 'ZTS'       , 'DANA'     , 'bojove'  , 'piskova', 4, 2003, 255000),
    (11, 'TYBCD12EF3G456789', '312 45-67', 'Toyota'    , 'Hilux'    , 'sluzebni', 'zelena' , 4, 2021, 120000),
    (12, 'SKLMN34OP5Q678901', '415 23-89', 'Skoda'     , 'Fabia'    , 'sluzebni', 'cerna'  , 4, 2019, 95000),
    (13, 'LDRVR56ST7U890123', '216 78-34', 'Land Rover', 'Defender' , 'takticke', 'piskova', 4, 2018, 145000),
    (14, 'TATXA78BC9D012345', '318 90-12', 'Tatra'     , '815-7'    , 'nakladni', 'zelena' , 6, 2020, 320000),
    (15, 'TATXB90DE1F234567', '419 56-78', 'Tatra'     , '810'      , 'nakladni', 'zelena' , 6, 2015, 210000),
    (16, 'IVECC12GH3I456789', '520 34-90', 'IVECO'     , 'LMV CZ5'  , 'takticke', 'piskova', 4, 2020, 88000),
    (17, 'TDVXP34JK5L678901', '221 67-45', 'TDV'       , 'Pandur II', 'bojove'  , 'zelena' , 8, 2022, 105000),
    (18, 'NXTRS56MN7O890123', '322 89-23', 'Nexter Systems', 'TITUS', 'takticke', 'zelena' , 6, 2023, 72000),
    (19, 'KMWDG78PQ9R012345', '123 45-67', 'KMW'       , 'Dingo 2'  , 'takticke', 'piskova', 4, 2010, 415000),
    (20, 'ZTSDN90ST1U234567', '624 12-34', 'ZTS'       , 'DANA'     , 'bojove'  , 'piskova', 4, 2005, 240000),
    (21, 'TYHLX12VW3X456789', '125 78-90', 'Toyota'    , 'Hilux'    , 'sluzebni', 'zelena' , 4, 2023, 45000),
    (22, 'SKFAB34YZ5A678901', '726 56-12', 'Skoda'     , 'Fabia'    , 'sluzebni', 'bila'   , 4, 2020, 67000),
    (23, 'LDDEF56BC7D890123', '227 34-56', 'Land Rover', 'Defender' , 'takticke', 'zelena' , 4, 2017, 156000),
    (24, 'TAT8178EF9G012345', '828 90-78', 'Tatra'     , '815-7'    , 'nakladni', 'zelena' , 6, 2022, 98000),
    (25, 'TAT8190HI1J234567', '329 12-34', 'Tatra'     , '810'      , 'nakladni', 'zelena' , 6, 2014, 195000),
    (26, 'IVLMV12KL3M456789', '930 45-67', 'IVECO'     , 'LMV CZ5'  , 'takticke', 'zelena' , 4, 2019, 102000),
    (27, 'TDPAN34NO5P678901', '131 78-90', 'TDV'       , 'Pandur II', 'bojove'  , 'piskova', 8, 2023, 89000),
    (28, 'NXTTX56QR7S890123', '632 23-45', 'Nexter Systems', 'TITUS', 'takticke', 'piskova', 6, 2025, 38000),
    (29, 'KMDIN78TU9V012345', '233 56-78', 'KMW'       , 'Dingo 2'  , 'takticke', 'zelena' , 4, 2009, 215000),
    (30, 'ZTSDA90WX1Y234567', '934 89-01', 'ZTS'       , 'DANA'     , 'bojove'  , 'zelena' , 4, 2004, 268000);

INSERT OR IGNORE INTO ServisniPravidlo (typ_vozidla, komponenta, interval_dni)
VALUES 
    ('sluzebni', 'motor', 180),
    ('sluzebni', 'prevodovka', 180),
    ('sluzebni', 'brzdy', 90),
    ('sluzebni', 'svetla', 365),
    ('sluzebni', 'pneu', 180),
    ('sluzebni', 'diferencial', 240),
    ('sluzebni', 'napravy', 240),
    ('sluzebni', 'tlumice', 120),
    ('sluzebni', 'olej', 30),
    ('sluzebni', 'chladici kapalina', 60),

    ('nakladni', 'motor', 120),
    ('nakladni', 'prevodovka', 120),
    ('nakladni', 'brzdy', 60),
    ('nakladni', 'svetla', 365),
    ('nakladni', 'pneu', 120),
    ('nakladni', 'diferencial', 180),
    ('nakladni', 'napravy', 180),
    ('nakladni', 'tlumice', 90),
    ('nakladni', 'olej', 15),
    ('nakladni', 'chladici kapalina', 45),

    ('takticke', 'motor', 150),
    ('takticke', 'prevodovka', 150),
    ('takticke', 'brzdy', 75),
    ('takticke', 'svetla', 365),
    ('takticke', 'pneu', 150),
    ('takticke', 'diferencial', 210),
    ('takticke', 'napravy', 210),
    ('takticke', 'tlumice', 105),
    ('takticke', 'olej', 20),
    ('takticke', 'chladici kapalina', 50),

    ('bojove', 'motor', 100),
    ('bojove', 'prevodovka', 100),
    ('bojove', 'brzdy', 50),
    ('bojove', 'svetla', 365),
    ('bojove', 'pneu', 100),
    ('bojove', 'diferencial', 150),
    ('bojove', 'napravy', 150),
    ('bojove', 'tlumice', 75),
    ('bojove', 'olej', 10),
    ('bojove', 'chladici kapalina', 30);

INSERT OR IGNORE INTO KilometrovePravidlo (typ_vozidla, komponenta, interval_km)
VALUES 
    ('sluzebni', 'motor', 50000),
    ('sluzebni', 'prevodovka', 60000),
    ('sluzebni', 'brzdy', 30000),
    ('sluzebni', 'svetla', 100000),
    ('sluzebni', 'pneu', 40000),
    ('sluzebni', 'diferencial', 50000),
    ('sluzebni', 'napravy', 50000),
    ('sluzebni', 'tlumice', 30000),
    ('sluzebni', 'olej', 10000),
    ('sluzebni', 'chladici kapalina', 15000),

    ('nakladni', 'motor', 30000),
    ('nakladni', 'prevodovka', 30000),
    ('nakladni', 'brzdy', 20000),
    ('nakladni', 'svetla', 100000),
    ('nakladni', 'pneu', 25000),
    ('nakladni', 'diferencial', 35000),
    ('nakladni', 'napravy', 35000),
    ('nakladni', 'tlumice', 20000),
    ('nakladni', 'olej', 5000),
    ('nakladni', 'chladici kapalina', 10000),

    ('takticke', 'motor', 40000),
    ('takticke', 'prevodovka', 45000),
    ('takticke', 'brzdy', 25000),
    ('takticke', 'svetla', 100000),
    ('takticke', 'pneu', 35000),
    ('takticke', 'diferencial', 45000),
    ('takticke', 'napravy', 45000),
    ('takticke', 'tlumice', 25000),
    ('takticke', 'olej', 7500),
    ('takticke', 'chladici kapalina', 12000),

    ('bojove', 'motor', 25000),
    ('bojove', 'prevodovka', 25000),
    ('bojove', 'brzdy', 15000),
    ('bojove', 'svetla', 100000),
    ('bojove', 'pneu', 20000),
    ('bojove', 'diferencial', 30000),
    ('bojove', 'napravy', 30000),
    ('bojove', 'tlumice', 15000),
    ('bojove', 'olej', 3000),
    ('bojove', 'chladici kapalina', 7500);

INSERT OR IGNORE INTO ZivotnostVozidla (typ_vozidla, zivotnost_km)
VALUES 
    ('sluzebni', 1000000),
    ('nakladni', 300000),
    ('takticke', 400000),
    ('bojove', 250000);

INSERT OR IGNORE INTO VstupniServis (vozidlo_id, vstupni_datum)
VALUES 
    (1, '2026-01-01'),
    (2, '2025-12-20'),
    (3, '2025-12-15'),
    (4, '2025-11-08'),
    (5, '2025-11-30'),
    (6, '2025-12-01'),
    (7, '2025-11-25'),
    (8, '2025-12-05'),
    (9, '2025-12-15'),
    (10, '2025-11-10'),
    (11, '2025-11-15'),
    (12, '2025-12-10'),
    (13, '2025-11-20'),
    (14, '2025-12-05'),
    (15, '2025-11-25'),
    (16, '2025-12-15'),
    (17, '2025-11-18'),
    (18, '2025-12-02'),
    (19, '2025-11-22'),
    (20, '2025-12-08'),
    (21, '2025-11-12'),
    (22, '2025-12-18'),
    (23, '2025-11-28'),
    (24, '2025-12-12'),
    (25, '2025-11-16'),
    (26, '2025-12-22'),
    (27, '2025-11-14'),
    (28, '2025-12-06'),
    (29, '2025-11-24'),
    (30, '2025-12-16');

CREATE TABLE IF NOT EXISTS Zapujcka (
    zapujcka_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vozidlo_id INTEGER NOT NULL,
    datum_od TEXT NOT NULL,
    datum_do TEXT NOT NULL,
    FOREIGN KEY (vozidlo_id) REFERENCES Vozidlo(vozidlo_id)
);

CREATE TABLE IF NOT EXISTS MimoradnaUdalost (
    udalost_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vozidlo_id INTEGER NOT NULL,
    datum_hlaseni TEXT NOT NULL,
    datum_navratu TEXT NOT NULL,
    FOREIGN KEY (vozidlo_id) REFERENCES Vozidlo(vozidlo_id)
);

CREATE INDEX IF NOT EXISTS idx_servisni_zaznam_vozidlo_komponenta 
    ON ServisniZaznam(vozidlo_id, komponenta);

CREATE INDEX IF NOT EXISTS idx_zapujcka_vozidlo_datum 
    ON Zapujcka(vozidlo_id, datum_od, datum_do);

CREATE INDEX IF NOT EXISTS idx_mimoradna_udalost_vozidlo_datum 
    ON MimoradnaUdalost(vozidlo_id, datum_hlaseni, datum_navratu);

CREATE INDEX IF NOT EXISTS idx_vozidlo_typ 
    ON Vozidlo(typ_vozidla);

CREATE INDEX IF NOT EXISTS idx_servisni_pravidlo_lookup 
    ON ServisniPravidlo(typ_vozidla, komponenta);

CREATE INDEX IF NOT EXISTS idx_kilometrove_pravidlo_lookup 
    ON KilometrovePravidlo(typ_vozidla, komponenta);