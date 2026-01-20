from datetime import date
import db

KOMPONENTY = ["motor", "prevodovka", "brzdy", "svetla", "pneu", "diferencial", "napravy", "tlumice", "olej", "chladici kapalina"]

def ziskej_interval(typ_vozidla, komponenta):
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT interval_dni
            FROM ServisniPravidlo
            WHERE typ_vozidla=? AND komponenta=?
        """, (typ_vozidla, komponenta))
        return cur.fetchone()[0]

def ziskej_interval_km(typ_vozidla, komponenta):
    """Vrátí intervalový počet km pro servis komponenty"""
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT interval_km
            FROM KilometrovePravidlo
            WHERE typ_vozidla=? AND komponenta=?
        """, (typ_vozidla, komponenta))
        result = cur.fetchone()
        return result[0] if result else None


def ziskej_posledni_servis(vozidlo_id, komponenta):
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT posledni_servis, posledni_servis_km
            FROM ServisniZaznam
            WHERE vozidlo_id=? AND komponenta=?
            ORDER BY posledni_servis DESC
            LIMIT 1
        """, (vozidlo_id, komponenta))
        row = cur.fetchone()
        if row:
            datum = date.fromisoformat(row[0])
            km = row[1] if row[1] is not None else 0
            return (datum, km)
        return None


def zapis_servis(vozidlo_id, komponenta, km=None):
    """Zapíše servis komponenty s aktuálním datem a km (pokud zadáno)"""
    dnes = db.ziskej_datum()
    if km is None:
        km = db.ziskej_km_vozidla(vozidlo_id)
    
    with db.pripoj() as conn:
        conn.execute("""
            INSERT INTO ServisniZaznam (vozidlo_id, komponenta, posledni_servis, posledni_servis_km)
            VALUES (?, ?, ?, ?)
        """, (vozidlo_id, komponenta, dnes.isoformat(), km))


def komponenta_ok(vozidlo_id, typ_vozidla, komponenta):
    """Vrátí True pokud je komponenta v pořádku (pokud splňuje jak časové tak km intervaly)"""
    posledni = ziskej_posledni_servis(vozidlo_id, komponenta)
    if not posledni:
        return False
    
    posledni_datum, posledni_km = posledni

    # Kontrola časového intervalu
    interval_dni = ziskej_interval(typ_vozidla, komponenta)
    dnes = db.ziskej_datum()
    cas_ok = (dnes - posledni_datum).days <= interval_dni
    
    # Kontrola km intervalu
    aktualni_km = db.ziskej_km_vozidla(vozidlo_id)
    interval_km = ziskej_interval_km(typ_vozidla, komponenta)
    
    km_ok = True
    if interval_km and (aktualni_km - posledni_km) > interval_km:
        km_ok = False
    
    return cas_ok and km_ok


def vozidlo_pojizdne(vozidlo_id):
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT typ_vozidla FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        typ = cur.fetchone()[0]

    for k in KOMPONENTY:
        if not komponenta_ok(vozidlo_id, typ, k):
            return False
    return True

def ziskej_stav_vozidla(vozidlo_id):
    """
    Vrátí stav vozidla: "DOSTUPNE", "PLANOVANY SERVIS", "NEDOSTUPNE", "DEAKTIVOVANO", "SLUZEBNI CESTA", "HAVAROVANO" nebo "V OPRAVE"
    """
    # Kontrola mimořádné události
    aktivni_udalost = db.ziskej_aktivni_udalost(vozidlo_id)
    if aktivni_udalost:
        datum_hlaseni, datum_navratu = aktivni_udalost
        dnes = db.ziskej_datum()
        
        # Den hlášení = HAVAROVANO
        if dnes == datum_hlaseni:
            return "HAVAROVANO"
        # Dny mezi hlášením a návratem (3 dny) = V OPRAVE
        elif datum_hlaseni < dnes < datum_navratu:
            return "V OPRAVE"
    
    # Kontrola zápůjčky
    if db.je_vozidlo_zapujcene(vozidlo_id):
        return "SLUZEBNI CESTA"
    
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT typ_vozidla, aktualni_km FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        result = cur.fetchone()
        if not result:
            return "NEZNAMO"
        typ, aktualni_km = result
    
    # Kontrola životnosti vozidla
    zivotnost = db.ziskej_zivotnost_vozidla(typ)
    if zivotnost and aktualni_km >= zivotnost:
        return "DEAKTIVOVANO"
    
    dnes = db.ziskej_datum()
    je_neco_planovano = False
    je_neco_v_minulosti = False
    
    for komponenta in KOMPONENTY:
        posledni = ziskej_posledni_servis(vozidlo_id, komponenta)
        
        # Pokud není servis vůbec proveden
        if not posledni:
            je_neco_v_minulosti = True
            continue
        
        posledni_datum, posledni_km = posledni
        
        # Pokud je servis v budoucnosti, je naplánován
        if posledni_datum > dnes:
            je_neco_planovano = True
        # Pokud je servis v minulosti a vypršel interval
        elif not komponenta_ok(vozidlo_id, typ, komponenta):
            je_neco_v_minulosti = True
    
    # Logika určování stavu
    if je_neco_v_minulosti:
        return "NEDOSTUPNE"
    elif je_neco_planovano:
        return "PLANOVANY SERVIS"
    else:
        return "DOSTUPNE"


def ziskej_stav_komponenty(vozidlo_id, komponenta):
    """
    Vrátí stav komponenty: "POSKOZENE", "V OPRAVE", "PLANOVANY SERVIS", "POTŘEBA SERVISU" nebo "OK"
    """
    # Nejdříve zkontroluj stav vozidla
    stav_vozidla = ziskej_stav_vozidla(vozidlo_id)
    
    # Pokud je vozidlo havarované, komponenty jsou poškozené
    if stav_vozidla == "HAVAROVANO":
        return "POSKOZENE"
    
    # Pokud je vozidlo v opravě, komponenty jsou v opravě
    if stav_vozidla == "V OPRAVE":
        return "V OPRAVE"
    
    # Jinak použij standardní logiku pro komponenty
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT typ_vozidla FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        result = cur.fetchone()
        if not result:
            return "NEZNAMO"
        typ_vozidla = result[0]
    
    dnes = db.ziskej_datum()
    posledni = ziskej_posledni_servis(vozidlo_id, komponenta)
    
    if not posledni:
        return "POTŘEBA SERVISU"
    
    posledni_datum, posledni_km = posledni
    
    # Zkontroluj, zda je servis naplánován v budoucnosti
    if posledni_datum > dnes:
        return "PLANOVANY SERVIS"
    
    # Zkontroluj, zda je komponenta OK
    if not komponenta_ok(vozidlo_id, typ_vozidla, komponenta):
        return "POTŘEBA SERVISU"
    
    return "OK"


def kontrola_platnosti_servisu_do_data(vozidlo_id, cilove_datum):
    """
    Zkontroluje, zda všechny komponenty vozidla budou v pořádku až do cílového data.
    Vrací tuple (bool, list) - (je_ok, seznam_problematickych_komponent)
    """
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT typ_vozidla FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        result = cur.fetchone()
        if not result:
            return False, ["Vozidlo nenalezeno"]
        typ = result[0]
    
    problematicke_komponenty = []
    
    for komponenta in KOMPONENTY:
        posledni = ziskej_posledni_servis(vozidlo_id, komponenta)
        
        if not posledni:
            problematicke_komponenty.append(f"{komponenta} (žádný servis)")
            continue
        
        posledni_datum, posledni_km = posledni
        interval_dni = ziskej_interval(typ, komponenta)
        
        # Vypočítej, kdy vyprší platnost servisu
        from datetime import timedelta
        datum_vyprseni = posledni_datum + timedelta(days=interval_dni)
        
        # Pokud vyprší před cílovým datem, je problém
        if datum_vyprseni < cilove_datum:
            problematicke_komponenty.append(f"{komponenta} (vyprší {datum_vyprseni.strftime('%d.%m.%Y')})")
    
    return len(problematicke_komponenty) == 0, problematicke_komponenty


def ziskej_datum_nejblizsiho_vyprseni_servisu(vozidlo_id):
    """
    Vrátí datum nejbližšího vypršení servisu některé komponenty vozidla.
    Pokud není servis žádné komponenty, vrací None.
    """
    with db.pripoj() as conn:
        cur = conn.cursor()
        cur.execute("SELECT typ_vozidla FROM Vozidlo WHERE vozidlo_id=?", (vozidlo_id,))
        result = cur.fetchone()
        if not result:
            return None
        typ = result[0]
    
    nejblizsi_vyprseni = None
    
    for komponenta in KOMPONENTY:
        posledni = ziskej_posledni_servis(vozidlo_id, komponenta)
        
        if not posledni:
            continue
        
        posledni_datum, posledni_km = posledni
        interval_dni = ziskej_interval(typ, komponenta)
        
        # Vypočítej, kdy vyprší platnost servisu
        from datetime import timedelta
        datum_vyprseni = posledni_datum + timedelta(days=interval_dni)
        
        # Sleduj nejbližší vypršení
        if nejblizsi_vyprseni is None or datum_vyprseni < nejblizsi_vyprseni:
            nejblizsi_vyprseni = datum_vyprseni
    
    return nejblizsi_vyprseni
