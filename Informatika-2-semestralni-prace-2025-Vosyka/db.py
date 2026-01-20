import sqlite3
from datetime import datetime, timedelta, date

DB_SOUBOR = "motorpool.db"

def pripoj():
    return sqlite3.connect(DB_SOUBOR)

def inicializuj_db():
    with open("schema.sql") as f:
        sql = f.read()
    with pripoj() as conn:
        conn.executescript(sql)
        conn.commit()
    
    # Vždy nastav dnešní datum při spuštění
    nastav_datum(date.today())
    
    # Zpracuj vstupní servisy - rozšíř je na všechny komponenty
    zpracuj_vstupni_servisy()

# --- SIMULOVANY CAS ---

def ziskej_datum():
    with pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT aktualni_datum FROM SystemCas WHERE id=1")
        return datetime.strptime(cur.fetchone()[0], "%Y-%m-%d").date()

def nastav_datum(nove_datum):
    with pripoj() as conn:
        conn.execute(
            "UPDATE SystemCas SET aktualni_datum=? WHERE id=1",
            (nove_datum.strftime("%Y-%m-%d"),)
        )

def posun_dny(dny):
    dnes = ziskej_datum()
    nastav_datum(dnes + timedelta(days=dny))

# --- KILOMETRAZE ---

def ziskej_km_vozidla(vozidlo_id):
    """Vrátí aktuální kilometrážní stav vozidla"""
    with pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT aktualni_km FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        result = cur.fetchone()
        return result[0] if result else 0

def nastav_km_vozidla(vozidlo_id, km):
    """Nastavi aktuální kilometrážní stav vozidla"""
    with pripoj() as conn:
        conn.execute(
            "UPDATE Vozidlo SET aktualni_km=? WHERE vozidlo_id=?",
            (km, vozidlo_id)
        )
        conn.commit()

def posun_km(vozidlo_id, km):
    """Posune vozidlo o zadaný počet km"""
    aktualni = ziskej_km_vozidla(vozidlo_id)
    nastav_km_vozidla(vozidlo_id, aktualni + km)

def ziskej_zivotnost_vozidla(typ_vozidla):
    """Vrátí životnost vozidla v km pro daný typ"""
    with pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT zivotnost_km FROM ZivotnostVozidla WHERE typ_vozidla=?", (typ_vozidla,))
        result = cur.fetchone()
        return result[0] if result else 0



def zpracuj_vstupni_servisy():
    """Rozšíří vstupní servisy z tabulky VstupniServis na všechny komponenty vozidel"""
    import logika
    
    with pripoj() as conn:
        # Ziskej všechny vstupní servisy
        vstupni = conn.execute("SELECT vozidlo_id, vstupni_datum FROM VstupniServis").fetchall()
        
        for vozidlo_id, vstupni_datum in vstupni:
            # Ziskej typ vozidla a aktuální km
            vozidlo_data = conn.execute(
                "SELECT typ_vozidla, aktualni_km FROM Vozidlo WHERE vozidlo_id=?",
                (vozidlo_id,)
            ).fetchone()
            typ_vozidla, aktualni_km = vozidlo_data
            
            # Pro každou komponentu
            for komponenta in logika.KOMPONENTY:
                # Zkontroluj, zda už existuje záznam
                existing = conn.execute(
                    "SELECT zaznam_id FROM ServisniZaznam WHERE vozidlo_id=? AND komponenta=?",
                    (vozidlo_id, komponenta)
                ).fetchone()
                
                if not existing:
                    # Vytvoř nový záznam s vstupním datem a km
                    conn.execute(
                        "INSERT INTO ServisniZaznam (vozidlo_id, komponenta, posledni_servis, posledni_servis_km) VALUES (?, ?, ?, ?)",
                        (vozidlo_id, komponenta, vstupni_datum, aktualni_km)
                    )
        
        conn.commit()


# --- ZAPUJCKY ---

def vytvor_zapujcku(vozidlo_id, datum_od, datum_do):
    """Vytvoří novou zápůjčku vozidla"""
    with pripoj() as conn:
        conn.execute(
            "INSERT INTO Zapujcka (vozidlo_id, datum_od, datum_do) VALUES (?, ?, ?)",
            (vozidlo_id, datum_od.isoformat(), datum_do.isoformat())
        )
        conn.commit()

def ziskej_zapujcky_vozidla(vozidlo_id):
    """Vrátí všechny zápůjčky vozidla jako seznam (zapujcka_id, datum_od, datum_do)"""
    with pripoj() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT zapujcka_id, datum_od, datum_do FROM Zapujcka WHERE vozidlo_id=?",
            (vozidlo_id,)
        )
        result = []
        for row in cur.fetchall():
            result.append((row[0], date.fromisoformat(row[1]), date.fromisoformat(row[2])))
        return result

def je_vozidlo_zapujcene(vozidlo_id, kontrolni_datum=None):
    """Zkontroluje, zda je vozidlo zapůjčené k danému datu (nebo k aktuálnímu simulovanému datu)"""
    if kontrolni_datum is None:
        kontrolni_datum = ziskej_datum()
    
    zapujcky = ziskej_zapujcky_vozidla(vozidlo_id)
    for _, od, do in zapujcky:
        if od <= kontrolni_datum <= do:
            return True
    return False


# --- MIMORADNE UDALOSTI ---

def vytvor_udalost(vozidlo_id, datum_hlaseni):
    """Vytvoří mimořádnou událost a nastaví datum návratu (hlášení + 4 dny)"""
    from datetime import timedelta
    datum_navratu = datum_hlaseni + timedelta(days=4)
    
    with pripoj() as conn:
        conn.execute(
            "INSERT INTO MimoradnaUdalost (vozidlo_id, datum_hlaseni, datum_navratu) VALUES (?, ?, ?)",
            (vozidlo_id, datum_hlaseni.isoformat(), datum_navratu.isoformat())
        )
        conn.commit()

def ziskej_aktivni_udalost(vozidlo_id, kontrolni_datum=None):
    """Vrátí aktivní událost pro vozidlo (pokud existuje) jako tuple (datum_hlaseni, datum_navratu) nebo None"""
    if kontrolni_datum is None:
        kontrolni_datum = ziskej_datum()
    
    with pripoj() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT datum_hlaseni, datum_navratu 
               FROM MimoradnaUdalost 
               WHERE vozidlo_id = ? AND datum_hlaseni <= ? AND datum_navratu > ?
               ORDER BY datum_hlaseni DESC
               LIMIT 1""",
            (vozidlo_id, kontrolni_datum.isoformat(), kontrolni_datum.isoformat())
        )
        row = cur.fetchone()
        if row:
            return (date.fromisoformat(row[0]), date.fromisoformat(row[1]))
        return None

def zpracuj_navrat_z_udalosti(vozidlo_id, datum_navratu):
    """Provede všechny servisy vozidla k datu návratu z události"""
    import logika
    
    with pripoj() as conn:
        # Získej typ vozidla
        cur = conn.cursor()
        cur.execute("SELECT typ_vozidla FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        result = cur.fetchone()
        if not result:
            return
        typ_vozidla = result[0]
        
        # Získej aktuální km
        aktualni_km = ziskej_km_vozidla(vozidlo_id)
        
        # Proveď servis všech komponent
        for komponenta in logika.KOMPONENTY:
            conn.execute(
                "INSERT INTO ServisniZaznam (vozidlo_id, komponenta, posledni_servis, posledni_servis_km) VALUES (?, ?, ?, ?)",
                (vozidlo_id, komponenta, datum_navratu.isoformat(), aktualni_km)
            )
        
        conn.commit()
