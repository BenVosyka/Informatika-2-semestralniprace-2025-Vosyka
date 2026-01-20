import tkinter as tk
from tkinter import ttk, messagebox
import db
import logika
from datetime import date
import calendar

db.inicializuj_db()

otevena_detaily_okna = {}
otevena_servis_okna = {}   # {(vozidlo_id, komponenta): okno}
aktualizuj_detaily_funkce = {}  # {vozidlo_id: aktualizuj_detaily_funkce}
otevena_pridani_okna = None
otevren_admin_panel = None
otevren_kalendar = None
aktualizuj_kalendar_funkce = None  # Funkce pro aktualizaci kalendáře

# --- Filtr ---
filtr_typ = "vše"
filtr_stav = "vše"
vsechna_vozidla = []

_cache_stavy_vozidel = {}
_cache_timestamp = None

def vymaz_cache():
    """Vymaže cache stavů vozidel"""
    global _cache_stavy_vozidel, _cache_timestamp
    _cache_stavy_vozidel = {}
    _cache_timestamp = db.ziskej_datum()

def ziskej_stav_vozidla_cached(vozidlo_id):
    """Vrátí stav vozidla s cachováním"""
    current_date = db.ziskej_datum()
    
    if _cache_timestamp != current_date:
        vymaz_cache()
    
    if vozidlo_id not in _cache_stavy_vozidel:
        _cache_stavy_vozidel[vozidlo_id] = logika.ziskej_stav_vozidla(vozidlo_id)
    
    return _cache_stavy_vozidel[vozidlo_id]

def aktualizuj():
    """Aktualizuje hlavní seznam vozidel"""
    datum_label.config(text=f"Datum: {db.ziskej_datum().strftime('%d-%m-%Y')}")
    vymaz_cache()

    for row in strom.get_children():
        strom.delete(row)

    with db.pripoj() as conn:
        vozidla = conn.execute("""
            SELECT vozidlo_id, vpz, vyrobce, model, typ_vozidla
            FROM Vozidlo
        """).fetchall()

    global vsechna_vozidla
    vsechna_vozidla = vozidla
    
    aplikuj_filtr()

def aplikuj_filtr():
    """Aplikuje filtr na seznam vozidel - optimalizováno"""
    for row in strom.get_children():
        strom.delete(row)
    
    for v in vsechna_vozidla:
        if filtr_typ != "vše" and v[4] != filtr_typ:
            continue
        
        stav = ziskej_stav_vozidla_cached(v[0])
        
        if filtr_stav != "vše" and stav != filtr_stav:
            continue
        
        tag_map = {
            "DEAKTIVOVANO": "dead",
            "PLANOVANY SERVIS": "planned",
            "SLUZEBNI CESTA": "borrowed",
            "HAVAROVANO": "crashed",
            "V OPRAVE": "repair",
            "DOSTUPNE": "ok"
        }
        tag = tag_map.get(stav, "bad")
        
        strom.insert("", "end", values=(v[1], v[2], v[3], v[4], stav),
                     tags=(tag,))

def na_zmenu_typu(event):
    global filtr_typ
    filtr_typ = combo_typ.get()
    aplikuj_filtr()

def na_zmenu_stavu(event):
    global filtr_stav
    filtr_stav = combo_stav.get()
    aplikuj_filtr()

def posun(dny):
    """Posune čas o zadaný počet dní - optimalizováno"""
    db.posun_dny(dny)
    vymaz_cache()
    
    dnes = db.ziskej_datum()
    with db.pripoj() as conn:
        ukoncene_udalosti = conn.execute(
            "SELECT vozidlo_id, datum_navratu FROM MimoradnaUdalost WHERE datum_navratu = ?",
            (dnes.isoformat(),)
        ).fetchall()
        
        for vozidlo_id, datum_navratu_str in ukoncene_udalosti:
            from datetime import date as dt_date
            datum_navratu = dt_date.fromisoformat(datum_navratu_str)
            db.zpracuj_navrat_z_udalosti(vozidlo_id, datum_navratu)
    
    aktualizuj()
    
    for vozidlo_id in list(aktualizuj_detaily_funkce.keys()):
        try:
            okno = otevena_detaily_okna.get(vozidlo_id)
            if okno and okno.winfo_exists():
                aktualizuj_detaily_funkce[vozidlo_id]()
        except:
            if vozidlo_id in aktualizuj_detaily_funkce:
                del aktualizuj_detaily_funkce[vozidlo_id]
    
    if aktualizuj_kalendar_funkce is not None:
        try:
            if otevren_kalendar and otevren_kalendar.winfo_exists():
                aktualizuj_kalendar_funkce()
        except:
            pass

def admin_servis():
    """Admin servis - nastaví všechny komponenty všech vozidel na dnešní datum"""
    if not messagebox.askyesno("Admin servis", "Opravdu chceš nastavit všechny komponenty všech vozidel na dnešní servis?"):
        return
    
    try:
        dnes = db.ziskej_datum()
        
        with db.pripoj() as conn:
            conn.execute("""
                UPDATE ServisniZaznam
                SET posledni_servis = ?,
                    posledni_servis_km = (SELECT aktualni_km FROM Vozidlo WHERE Vozidlo.vozidlo_id = ServisniZaznam.vozidlo_id)
                WHERE EXISTS (SELECT 1 FROM Vozidlo WHERE Vozidlo.vozidlo_id = ServisniZaznam.vozidlo_id)
            """, (dnes.isoformat(),))
            
            conn.commit()
        
        messagebox.showinfo("Úspěch", "Všechna vozidla byla odsouhlasena!")
        vymaz_cache()
        aktualizuj()
    except Exception as e:
        messagebox.showerror("Chyba", f"Chyba při servisu: {str(e)}")

def hromadny_servis_komponenty(komponenta):
    """Provede hromadný servis jedné komponenty pro všechna vozidla - optimalizováno"""
    if not komponenta or komponenta == "":
        messagebox.showerror("Chyba", "Musíš vybrat komponentu!")
        return
    
    if not messagebox.askyesno("Hromadný servis", f"Opravdu chceš nastavit servis komponenty '{komponenta}' pro všechna vozidla?"):
        return
    
    try:
        dnes = db.ziskej_datum()
        
        with db.pripoj() as conn:
            conn.execute("""
                UPDATE ServisniZaznam
                SET posledni_servis = ?,
                    posledni_servis_km = (SELECT aktualni_km FROM Vozidlo WHERE Vozidlo.vozidlo_id = ServisniZaznam.vozidlo_id)
                WHERE komponenta = ?
            """, (dnes.isoformat(), komponenta))
            
            conn.execute("""
                INSERT INTO ServisniZaznam (vozidlo_id, komponenta, posledni_servis, posledni_servis_km)
                SELECT v.vozidlo_id, ?, ?, v.aktualni_km
                FROM Vozidlo v
                WHERE NOT EXISTS (
                    SELECT 1 FROM ServisniZaznam s 
                    WHERE s.vozidlo_id = v.vozidlo_id AND s.komponenta = ?
                )
            """, (komponenta, dnes.isoformat(), komponenta))
            
            conn.commit()
        
        messagebox.showinfo("Úspěch", f"Servis komponenty '{komponenta}' byl provéden pro všechna vozidla!")
        vymaz_cache()
        aktualizuj()
    except Exception as e:
        messagebox.showerror("Chyba", f"Chyba při servisu: {str(e)}")

def zavrit_databazi():
    if messagebox.askyesno("Zavřít databázi", "Opravdu chcete zavřít databázi?\n\nPřijdete o neuloženou práci!"):
        okno.quit()

def otevri_kalendar():
    """Otevře kalendářové okno pro rezervace vozidel"""
    global otevren_kalendar, aktualizuj_kalendar_funkce
    
    if otevren_kalendar is not None:
        try:
            otevren_kalendar.lift()
            otevren_kalendar.focus()
        except:
            otevren_kalendar = None
            aktualizuj_kalendar_funkce = None
        else:
            return
    
    # Označit, že se okno vytváří
    class Sentinel: pass
    otevren_kalendar = Sentinel()
    
    kalendar_okno = tk.Toplevel(okno)
    kalendar_okno.title("Plánování služebních výjezdů")
    kalendar_okno.geometry("660x750")
    
    otevren_kalendar = kalendar_okno
    
    def on_closing():
        global otevren_kalendar, aktualizuj_kalendar_funkce
        otevren_kalendar = None
        aktualizuj_kalendar_funkce = None
        kalendar_okno.destroy()
    
    kalendar_okno.protocol("WM_DELETE_WINDOW", on_closing)
    
    dnes = [db.ziskej_datum()]
    zobrazeny_mesic = [dnes[0].month]
    zobrazeny_rok = [dnes[0].year]
    vybrane_dny = []
    
    mesice = ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
              "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]
    
    osobni_udaje_frame = tk.Frame(kalendar_okno)
    osobni_udaje_frame.pack(pady=10, padx=20)
    
    tk.Label(osobni_udaje_frame, text="Osobní údaje žadatele:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=5)
    
    tk.Label(osobni_udaje_frame, text="Hodnost:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5)
    combo_hodnost = ttk.Combobox(osobni_udaje_frame, values=["O.Z.","voj.", "svob.","des.", "čet.", "rtn.", "rtm.", "nrtm.", "prap.", "nprap.", "por.", "npor.", "kpt."], 
                                  state="readonly", width=10)
    combo_hodnost.grid(row=1, column=1, padx=5)
    combo_hodnost.current(0)
    
    tk.Label(osobni_udaje_frame, text="Jméno:", font=("Arial", 10)).grid(row=1, column=2, sticky="e", padx=5)
    entry_jmeno = tk.Entry(osobni_udaje_frame, width=15)
    entry_jmeno.grid(row=1, column=3, padx=5)
    
    tk.Label(osobni_udaje_frame, text="Příjmení:", font=("Arial", 10)).grid(row=1, column=4, sticky="e", padx=5)
    entry_prijmeni = tk.Entry(osobni_udaje_frame, width=15)
    entry_prijmeni.grid(row=1, column=5, padx=5)
    
    vybor_vozidla_frame = tk.Frame(kalendar_okno)
    vybor_vozidla_frame.pack(pady=15, padx=20)
    
    tk.Label(vybor_vozidla_frame, text="Vybrat vozidlo:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=5)
    
    tk.Label(vybor_vozidla_frame, text="Typ:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5)
    combo_typ_vozidla = ttk.Combobox(vybor_vozidla_frame, values=["vše", "sluzebni", "nakladni", "takticke", "bojove"], 
                                      state="readonly", width=12)
    combo_typ_vozidla.grid(row=1, column=1, padx=5)
    combo_typ_vozidla.set("vše")
    
    tk.Label(vybor_vozidla_frame, text="VPZ:", font=("Arial", 10)).grid(row=1, column=2, sticky="e", padx=5)
    entry_vpz_filtr = tk.Entry(vybor_vozidla_frame, width=15)
    entry_vpz_filtr.grid(row=1, column=3, padx=5)
    
    tk.Label(vybor_vozidla_frame, text="Vozidlo:", font=("Arial", 10)).grid(row=1, column=4, sticky="e", padx=5)
    combo_vozidlo = ttk.Combobox(vybor_vozidla_frame, state="readonly", width=25)
    combo_vozidlo.grid(row=1, column=5, padx=5)
    
    vozidla_seznam = {}
    vybrane_vozidlo = [None]
    
    def aktualizuj_seznam_vozidel():
        """Aktualizuje seznam vozidel podle vybraného typu a VPZ"""
        zvoleny_typ = combo_typ_vozidla.get()
        vpz_filtr = entry_vpz_filtr.get().strip().lower()
        
        with db.pripoj() as conn:
            if zvoleny_typ == "vše":
                vozidla = conn.execute("""
                    SELECT vozidlo_id, vpz, typ_vozidla, vyrobce, model
                    FROM Vozidlo
                    ORDER BY vyrobce, model
                """).fetchall()
            else:
                vozidla = conn.execute("""
                    SELECT vozidlo_id, vpz, typ_vozidla, vyrobce, model
                    FROM Vozidlo
                    WHERE typ_vozidla = ?
                    ORDER BY vyrobce, model
                """, (zvoleny_typ,)).fetchall()
        
        # Filtruj podle VPZ a stavu
        dostupna_vozidla = []
        vozidla_seznam.clear()
        
        for vozidlo_id, vpz, typ_vozidla, vyrobce, model in vozidla:
            stav = logika.ziskej_stav_vozidla(vozidlo_id)
            
            if stav not in ["DOSTUPNE", "SLUZEBNI CESTA"]:
                continue
            
            if vpz_filtr and vpz_filtr not in vpz.lower():
                continue
            
            formatovany_text = f"{vyrobce} {model}"
            dostupna_vozidla.append(formatovany_text)
            vozidla_seznam[formatovany_text] = (vozidlo_id, vpz)
        
        combo_vozidlo['values'] = dostupna_vozidla
        if dostupna_vozidla:
            combo_vozidlo.current(0)
            vybrane_vozidlo[0] = vozidla_seznam[dostupna_vozidla[0]][0]
        else:
            combo_vozidlo.set("")
            vybrane_vozidlo[0] = None
    
    def na_zmenu_typu_vozidla(event):
        """Handler pro změnu typu vozidla"""
        aktualizuj_seznam_vozidel()
    
    def na_zmenu_vpz(event):
        """Handler pro změnu VPZ filtru"""
        aktualizuj_seznam_vozidel()
    
    def na_zmenu_vozidla(event):
        """Handler pro změnu vybraného vozidla"""
        formatovany_text = combo_vozidlo.get()
        if formatovany_text in vozidla_seznam:
            vybrane_vozidlo[0] = vozidla_seznam[formatovany_text][0]
            vybrane_dny.clear()
            aktualizuj_pole_od_do()
            prekresli_kalendar()
    
    combo_typ_vozidla.bind("<<ComboboxSelected>>", na_zmenu_typu_vozidla)
    entry_vpz_filtr.bind("<KeyRelease>", na_zmenu_vpz)
    combo_vozidlo.bind("<<ComboboxSelected>>", na_zmenu_vozidla)
    
    aktualizuj_seznam_vozidel()
    
    ucel_frame = tk.Frame(kalendar_okno)
    ucel_frame.pack(pady=10, padx=20)
    
    tk.Label(ucel_frame, text="Bezservisová vyjímka pro zápůjčku:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
    
    checkbox_frame = tk.Frame(ucel_frame)
    checkbox_frame.pack(anchor="w")
    
    var_vycvik = tk.BooleanVar()
    var_osobni_servis = tk.BooleanVar()
    var_delsi_14_dni = tk.BooleanVar()
    
    def toggle_vycvik():
        if var_vycvik.get():
            var_osobni_servis.set(False)
            var_delsi_14_dni.set(False)
    
    def toggle_osobni_servis():
        if var_osobni_servis.get():
            var_vycvik.set(False)
            var_delsi_14_dni.set(False)
    
    def toggle_delsi_14_dni():
        if var_delsi_14_dni.get():
            var_vycvik.set(False)
            var_osobni_servis.set(False)
    
    tk.Checkbutton(checkbox_frame, text="Výcvik", variable=var_vycvik, font=("Arial", 10), command=toggle_vycvik).pack(side="left", padx=10)
    tk.Checkbutton(checkbox_frame, text="Osobní servis", variable=var_osobni_servis, font=("Arial", 10), command=toggle_osobni_servis).pack(side="left", padx=10)
    tk.Checkbutton(checkbox_frame, text="Delší 14 dnů", variable=var_delsi_14_dni, font=("Arial", 10), command=toggle_delsi_14_dni).pack(side="left", padx=10)
    
    nav_frame = tk.Frame(kalendar_okno)
    nav_frame.pack(pady=10)
    
    nadpis_label = tk.Label(nav_frame, 
                           text=f"{mesice[zobrazeny_mesic[0]-1]} {zobrazeny_rok[0]}", 
                           font=("Arial", 16, "bold"),
                           width=20)
    
    def aktualizuj_pole_od_do():
        """Aktualizuje textová pole podle vybraných dnů"""
        if not vybrane_dny:
            entry_od.config(state="normal")
            entry_do.config(state="normal")
            entry_od.delete(0, tk.END)
            entry_do.delete(0, tk.END)
            entry_od.config(state="readonly")
            entry_do.config(state="readonly")
        else:
            vybrane_dny.sort()
            entry_od.config(state="normal")
            entry_do.config(state="normal")
            entry_od.delete(0, tk.END)
            entry_do.delete(0, tk.END)
            entry_od.insert(0, vybrane_dny[0].strftime("%d.%m.%Y"))
            entry_do.insert(0, vybrane_dny[-1].strftime("%d.%m.%Y"))
            entry_od.config(state="readonly")
            entry_do.config(state="readonly")
    
    def klikni_na_den(den, mesic, rok):
        """Handler pro kliknutí na den v kalendáři"""
        from datetime import date as dt_date, timedelta
        kliknute_datum = dt_date(rok, mesic, den)
        
        # Kontrola, zda není v minulosti
        if kliknute_datum < dnes[0]:
            messagebox.showwarning("Varování", "Nelze vybrat den v minulosti!", parent=kalendar_okno)
            return
        
        # Kontrola, zda není vozidlo již zapůjčené v tento den
        if vybrane_vozidlo[0] is not None:
            zapujcky = db.ziskej_zapujcky_vozidla(vybrane_vozidlo[0])
            for _, datum_od, datum_do in zapujcky:
                if datum_od <= kliknute_datum <= datum_do:
                    messagebox.showwarning("Varování", 
                        f"Vozidlo je již zapůjčené v termínu {datum_od.strftime('%d.%m.%Y')} - {datum_do.strftime('%d.%m.%Y')}!",
                        parent=kalendar_okno)
                    return
        
        if kliknute_datum in vybrane_dny:
            vybrane_dny.remove(kliknute_datum)
        else:
            vybrane_dny.append(kliknute_datum)
        
        if len(vybrane_dny) >= 2:
            vybrane_dny.sort()
            prvni_den = vybrane_dny[0]
            posledni_den = vybrane_dny[-1]
            
            if vybrane_vozidlo[0] is not None:
                zapujcky = db.ziskej_zapujcky_vozidla(vybrane_vozidlo[0])
                aktualni_den = prvni_den
                while aktualni_den <= posledni_den:
                    for _, datum_od, datum_do in zapujcky:
                        if datum_od <= aktualni_den <= datum_do:
                            messagebox.showwarning("Varování", 
                                f"Vozidlo je již zapůjčené v termínu {datum_od.strftime('%d.%m.%Y')} - {datum_do.strftime('%d.%m.%Y')}!\n"
                                f"Nelze vybrat rozsah, který obsahuje obsazený den.",
                                parent=kalendar_okno)
                            # Odstraň poslední přidaný den
                            if kliknute_datum in vybrane_dny:
                                vybrane_dny.remove(kliknute_datum)
                            aktualizuj_pole_od_do()
                            prekresli_kalendar()
                            return
                    aktualni_den += timedelta(days=1)
            
            aktualni_den = prvni_den
            while aktualni_den <= posledni_den:
                if aktualni_den not in vybrane_dny:
                    vybrane_dny.append(aktualni_den)
                aktualni_den += timedelta(days=1)
            
            vybrane_dny.sort()
        
        aktualizuj_pole_od_do()
        prekresli_kalendar()
    
    def prekresli_kalendar():
        """Překreslí kalendář s aktuálně zobrazovaným měsícem"""
        from datetime import date as dt_date
        
        nadpis_label.config(text=f"{mesice[zobrazeny_mesic[0]-1]} {zobrazeny_rok[0]}")
        cal = calendar.monthcalendar(zobrazeny_rok[0], zobrazeny_mesic[0])
        obsazene_dny = set()
        datum_vyprseni_servisu = None
        if vybrane_vozidlo[0] is not None:
            zapujcky = db.ziskej_zapujcky_vozidla(vybrane_vozidlo[0])
            for _, datum_od, datum_do in zapujcky:
                from datetime import timedelta
                aktualni_den = datum_od
                while aktualni_den <= datum_do:
                    obsazene_dny.add(aktualni_den)
                    aktualni_den += timedelta(days=1)
            
            datum_vyprseni_servisu = logika.ziskej_datum_nejblizsiho_vyprseni_servisu(vybrane_vozidlo[0])
        
        for widget in kalendar_frame.winfo_children():
            if widget.grid_info().get('row', 0) > 0:
                widget.destroy()
        
        for row_idx, tyden in enumerate(cal, start=1):
            for col_idx, den in enumerate(tyden):
                if den == 0:
                    btn = tk.Button(kalendar_frame, text="", width=6, height=2, 
                                   state="disabled", bg="#E0E0E0")
                else:
                    datum_dne = dt_date(zobrazeny_rok[0], zobrazeny_mesic[0], den)
                    
                    je_dnes = (den == dnes[0].day and 
                              zobrazeny_mesic[0] == dnes[0].month and 
                              zobrazeny_rok[0] == dnes[0].year)
                    je_vybrany = datum_dne in vybrane_dny
                    je_minulost = datum_dne < dnes[0]
                    je_obsazeny = datum_dne in obsazene_dny
                    je_po_vyprseni_servisu = False
                    if datum_vyprseni_servisu is not None and datum_dne > datum_vyprseni_servisu:
                        je_po_vyprseni_servisu = True
                    
                    if je_obsazeny:
                        barva = "#FF6B6B"
                        state = "disabled"
                    elif je_vybrany:
                        barva = "#90EE90"
                        state = "normal"
                    elif je_po_vyprseni_servisu:
                        barva = "#FFB6B6"
                        state = "normal"
                    elif je_dnes:
                        barva = "#ADD8E6"
                        state = "normal"
                    elif je_minulost:
                        barva = "#F0F0F0"
                        state = "normal"
                    else:
                        barva = "white"
                        state = "normal"
                    
                    btn = tk.Button(kalendar_frame, text=str(den), width=6, height=2,
                                   bg=barva, relief="raised", state=state,
                                   command=lambda d=den, m=zobrazeny_mesic[0], r=zobrazeny_rok[0]: klikni_na_den(d, m, r))
                
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)
    
    def aktualizuj_kalendar_z_venci():
        """Aktualizuje kalendář při změně simulovaného data"""
        dnes[0] = db.ziskej_datum()
        zobrazeny_mesic[0] = dnes[0].month
        zobrazeny_rok[0] = dnes[0].year
        prekresli_kalendar()
    
    def predchozi_mesic():
        """Přepne na předchozí měsíc"""
        zobrazeny_mesic[0] -= 1
        if zobrazeny_mesic[0] < 1:
            zobrazeny_mesic[0] = 12
            zobrazeny_rok[0] -= 1
        prekresli_kalendar()
    
    def nasledujici_mesic():
        """Přepne na následující měsíc"""
        zobrazeny_mesic[0] += 1
        if zobrazeny_mesic[0] > 12:
            zobrazeny_mesic[0] = 1
            zobrazeny_rok[0] += 1
        prekresli_kalendar()
    
    btn_predchozi = tk.Button(nav_frame, text="◄", command=predchozi_mesic, 
                             font=("Arial", 14, "bold"), width=3)
    btn_predchozi.pack(side="left", padx=10)
    
    nadpis_label.pack(side="left", padx=10)
    
    btn_nasledujici = tk.Button(nav_frame, text="►", command=nasledujici_mesic,
                                font=("Arial", 14, "bold"), width=3)
    btn_nasledujici.pack(side="left", padx=10)
    
    kalendar_frame = tk.Frame(kalendar_okno)
    kalendar_frame.pack(padx=20, pady=10)
    
    dny_tydne = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
    for col, den in enumerate(dny_tydne):
        label = tk.Label(kalendar_frame, text=den, font=("Arial", 10, "bold"), width=8)
        label.grid(row=0, column=col, padx=2, pady=2)
    
    vybrane_frame = tk.Frame(kalendar_okno)
    vybrane_frame.pack(pady=20, padx=20)
    
    tk.Label(vybrane_frame, text="Vybrané dny:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=5)
    
    tk.Label(vybrane_frame, text="Od:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5)
    entry_od = tk.Entry(vybrane_frame, width=15, font=("Arial", 10), state="readonly")
    entry_od.grid(row=1, column=1, padx=5)
    
    tk.Label(vybrane_frame, text="Do:", font=("Arial", 10)).grid(row=1, column=2, sticky="e", padx=5)
    entry_do = tk.Entry(vybrane_frame, width=15, font=("Arial", 10), state="readonly")
    entry_do.grid(row=1, column=3, padx=5)
    
    def potvrdit_zapujcku():
        """Uloží zápůjčku do databáze"""
        if vybrane_vozidlo[0] is None:
            messagebox.showerror("Chyba", "Není vybráno žádné vozidlo!", parent=kalendar_okno)
            return
        
        if not vybrane_dny:
            messagebox.showerror("Chyba", "Nejsou vybrány žádné dny!", parent=kalendar_okno)
            return
        
        vybrane_dny.sort()
        datum_od = vybrane_dny[0]
        datum_do = vybrane_dny[-1]
        
        formatovany_text = combo_vozidlo.get()
        if formatovany_text in vozidla_seznam:
            vozidlo_id, vpz = vozidla_seznam[formatovany_text]
        else:
            messagebox.showerror("Chyba", "Nepodařilo se určit vozidlo!", parent=kalendar_okno)
            return
        
        je_vycvik = var_vycvik.get()
        je_osobni_servis = var_osobni_servis.get()
        je_delsi_14_dni = var_delsi_14_dni.get()
        
        if not je_osobni_servis:
            je_ok, problemy = logika.kontrola_platnosti_servisu_do_data(vybrane_vozidlo[0], datum_do)
            
            if not je_ok:
                if je_vycvik or je_delsi_14_dni:
                    typ_cesty = "výcvik" if je_vycvik else "cesta delší než 14 dní"
                    odpoved = messagebox.askyesno(
                        f"Varování - {typ_cesty.capitalize()}",
                        f"Vozidlu vypršejí tyto servisní komponenty během zápůjčky:\n" + 
                        "\n".join(problemy) + 
                        f"\n\nJedná se o {typ_cesty} - pokračovat i přesto?",
                        parent=kalendar_okno
                    )
                    if not odpoved:
                        return
                else:
                    messagebox.showerror(
                        "Chyba - Platnost servisu",
                        f"Vozidlo nelze zapůjčit, protože během zápůjčky vyprší platnost těchto komponent:\n" +
                        "\n".join(problemy) +
                        "\n\nZaškrtněte 'Výcvik', 'Delší 14 dnů' (s potvrzením) nebo 'Osobní servis' (pokud během cesty plánujete servisní prohlídku).",
                        parent=kalendar_okno
                    )
                    return
        
        try:
            db.vytvor_zapujcku(vybrane_vozidlo[0], datum_od, datum_do)
            messagebox.showinfo("Úspěch", 
                f"Zápůjčka byla vytvořena!\n"
                f"Vozidlo: {formatovany_text} (VPZ: {vpz})\n"
                f"Datum: {datum_od.strftime('%d.%m.%Y')} - {datum_do.strftime('%d.%m.%Y')}",
                parent=kalendar_okno)
            
            vybrane_dny.clear()
            aktualizuj_pole_od_do()
            prekresli_kalendar()
            aktualizuj()
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se vytvořit zápůjčku:\n{e}", parent=kalendar_okno)
    
    btn_potvrdit = tk.Button(vybrane_frame, text="Potvrdit zápůjčku", 
                            command=potvrdit_zapujcku, bg="#D3D3D3", 
                            font=("Arial", 11, "bold"), width=20, height=2)
    btn_potvrdit.grid(row=2, column=0, columnspan=4, pady=15)
    
    prekresli_kalendar()
    aktualizuj_kalendar_funkce = aktualizuj_kalendar_z_venci

def otevri_mimoradnou_udalost():
    """Otevře formulář pro hlášení mimořádné události"""
    udalost_okno = tk.Toplevel(okno)
    udalost_okno.title("Hlášení mimořádné události")
    udalost_okno.geometry("500x570")
    
    tk.Label(udalost_okno, text="Hlášení mimořádné události", font=("Arial", 14, "bold")).pack(pady=10)
    
    form_frame = tk.Frame(udalost_okno)
    form_frame.pack(pady=10, padx=20, fill="both")
    
    tk.Label(form_frame, text="Osobní údaje hlasitele:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
    
    tk.Label(form_frame, text="Hodnost:", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    combo_hodnost = ttk.Combobox(form_frame, values=["O.Z.","voj.", "svob.","des.", "čet.", "rtn.", "rtm.", "nrtm.", "prap.", "nprap.", "por.", "npor.", "kpt."], 
                                  state="readonly", width=27)
    combo_hodnost.grid(row=1, column=1, padx=5, pady=5)
    combo_hodnost.current(0)
    
    tk.Label(form_frame, text="Jméno:", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=5, pady=5)
    entry_jmeno = tk.Entry(form_frame, width=30)
    entry_jmeno.grid(row=2, column=1, padx=5, pady=5)
    
    tk.Label(form_frame, text="Příjmení:", font=("Arial", 10)).grid(row=3, column=0, sticky="e", padx=5, pady=5)
    entry_prijmeni = tk.Entry(form_frame, width=30)
    entry_prijmeni.grid(row=3, column=1, padx=5, pady=5)
    
    tk.Label(form_frame, text="Datum a čas události:", font=("Arial", 11, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(15, 10))
    
    tk.Label(form_frame, text="Datum:", font=("Arial", 10)).grid(row=5, column=0, sticky="e", padx=5, pady=5)
    datum_frame = tk.Frame(form_frame)
    datum_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
    
    dnes = db.ziskej_datum()
    
    from datetime import timedelta
    mozne_dny = []
    for i in range(-3, 4):
        datum = dnes + timedelta(days=i)
        mozne_dny.append(datum.strftime('%d.%m.%Y'))
    
    combo_datum = ttk.Combobox(datum_frame, values=mozne_dny, state="readonly", width=15)
    combo_datum.pack(side="left", padx=2)
    combo_datum.current(3)
    
    tk.Label(form_frame, text="Čas:", font=("Arial", 10)).grid(row=6, column=0, sticky="e", padx=5, pady=5)
    cas_frame = tk.Frame(form_frame)
    cas_frame.grid(row=6, column=1, sticky="w", padx=5, pady=5)
    
    spinbox_hodina = tk.Spinbox(cas_frame, from_=0, to=23, width=5, format="%02.0f")
    spinbox_hodina.pack(side="left", padx=2)
    tk.Label(cas_frame, text=":").pack(side="left")
    spinbox_minuta = tk.Spinbox(cas_frame, from_=0, to=59, width=5, format="%02.0f")
    spinbox_minuta.pack(side="left", padx=2)
    
    tk.Label(form_frame, text="Typ události:", font=("Arial", 11, "bold")).grid(row=7, column=0, columnspan=2, sticky="w", pady=(15, 10))
    
    var_nehoda = tk.BooleanVar()
    tk.Checkbutton(form_frame, text="Nehoda", variable=var_nehoda, font=("Arial", 10)).grid(row=8, column=0, columnspan=2, sticky="w", padx=5, pady=5)
    
    tk.Label(form_frame, text="Vozidlo:", font=("Arial", 11, "bold")).grid(row=9, column=0, columnspan=2, sticky="w", pady=(15, 10))
    
    tk.Label(form_frame, text="Vyberte vozidlo:", font=("Arial", 10)).grid(row=10, column=0, sticky="e", padx=5, pady=5)
    combo_vozidlo = ttk.Combobox(form_frame, state="readonly", width=30)
    combo_vozidlo.grid(row=10, column=1, padx=5, pady=5)
    
    vozidla_seznam = {}
    with db.pripoj() as conn:
        vozidla = conn.execute("""
            SELECT vozidlo_id, vpz, vyrobce, model
            FROM Vozidlo
            ORDER BY vpz
        """).fetchall()
    
    dostupna_vozidla = []
    for vozidlo_id, vpz, vyrobce, model in vozidla:
        stav = logika.ziskej_stav_vozidla(vozidlo_id)
        if stav in ["DOSTUPNE", "SLUZEBNI CESTA"]:
            formatovany_text = f"{vpz} - {vyrobce} {model}"
            dostupna_vozidla.append(formatovany_text)
            vozidla_seznam[formatovany_text] = vozidlo_id
    
    combo_vozidlo['values'] = dostupna_vozidla
    if dostupna_vozidla:
        combo_vozidlo.current(0)
    
    def potvrdit_udalost():
        if not entry_jmeno.get() or not entry_prijmeni.get():
            messagebox.showerror("Chyba", "Vyplňte jméno a příjmení!", parent=udalost_okno)
            return
        
        if not var_nehoda.get():
            messagebox.showerror("Chyba", "Zaškrtněte typ události!", parent=udalost_okno)
            return
        
        if not combo_vozidlo.get():
            messagebox.showerror("Chyba", "Vyberte vozidlo!", parent=udalost_okno)
            return
        
        try:
            from datetime import date as dt_date, timedelta
            
            vybrany_text = combo_datum.get()
            den, mesic, rok = vybrany_text.split('.')
            datum_udalosti = dt_date(int(rok), int(mesic), int(den))
            
            formatovany_text = combo_vozidlo.get()
            vozidlo_id = vozidla_seznam[formatovany_text]
            
            db.vytvor_udalost(vozidlo_id, datum_udalosti)
            
            messagebox.showinfo("Úspěch", 
                f"Mimořádná událost byla zaregistrována!\n"
                f"Vozidlo: {formatovany_text}\n"
                f"Stav vozidla byl změněn na HAVAROVANO.\n"
                f"Předpokládaný návrat: {(datum_udalosti + db.timedelta(days=4)).strftime('%d.%m.%Y')}",
                parent=udalost_okno)
            
            aktualizuj()
            udalost_okno.destroy()
            
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se vytvořit událost:\n{e}", parent=udalost_okno)
    
    btn_frame = tk.Frame(udalost_okno)
    btn_frame.pack(pady=20)
    
    tk.Button(btn_frame, text="Potvrdit", command=potvrdit_udalost, bg="#D3D3D3", 
             font=("Arial", 11, "bold"), width=15, height=2).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Zrušit", command=udalost_okno.destroy, bg="#f7b7b7", 
             font=("Arial", 11, "bold"), width=15, height=2).pack(side="left", padx=10)

def otevri_admin_panel():
    global otevren_admin_panel
    
    if otevren_admin_panel is not None:
        try:
            otevren_admin_panel.lift()
            otevren_admin_panel.focus()
        except:
            otevren_admin_panel = None
        else:
            return
    
    class Sentinel: pass
    otevren_admin_panel = Sentinel()
    
    admin_okno = tk.Toplevel(okno)
    admin_okno.title("Panel dozorčího vozového parku")
    admin_okno.geometry("400x500")
    
    otevren_admin_panel = admin_okno
    
    def on_closing():
        global otevren_admin_panel
        otevren_admin_panel = None
        admin_okno.destroy()
    
    admin_okno.protocol("WM_DELETE_WINDOW", on_closing)
    
    nadpis = tk.Label(admin_okno, text="Panel dozorčího vozového parku", font=("Arial", 14, "bold"))
    nadpis.pack(pady=15)
    
    frame_cas = ttk.LabelFrame(admin_okno, text="Simulace času", padding=15)
    frame_cas.pack(fill="x", padx=20, pady=10)
    
    ttk.Label(frame_cas, text="Posunout systémový čas:").pack(anchor="w", pady=5)
    
    frame_cas_tlacitka = ttk.Frame(frame_cas)
    frame_cas_tlacitka.pack(fill="x", pady=5)
    
    tk.Button(frame_cas_tlacitka, text="+1 den", command=lambda: posun(1), bg="#D3D3D3", width=12).pack(side="left", padx=5)
    tk.Button(frame_cas_tlacitka, text="+7 dní", command=lambda: posun(7), bg="#D3D3D3", width=12).pack(side="left", padx=5)
    tk.Button(frame_cas_tlacitka, text="+30 dní", command=lambda: posun(30), bg="#D3D3D3", width=12).pack(side="left", padx=5)
    
    frame_servis = ttk.LabelFrame(admin_okno, text="Hromadný servis", padding=15)
    frame_servis.pack(fill="x", padx=20, pady=10)
    
    ttk.Label(frame_servis, text="Označit všechny komponenty jako servisované:").pack(anchor="w", pady=5)
    
    tk.Button(frame_servis, text="Provést hromadný servis", command=admin_servis, bg="#D3D3D3", width=30).pack(pady=5)
    
    frame_servis_komponenta = ttk.LabelFrame(admin_okno, text="Hromadný servis komponenty", padding=15)
    frame_servis_komponenta.pack(fill="x", padx=20, pady=10)
    
    ttk.Label(frame_servis_komponenta, text="Vybrat komponentu:").pack(anchor="w", pady=5)
    
    combo_komponenta = ttk.Combobox(frame_servis_komponenta, values=logika.KOMPONENTY, state="readonly", width=30)
    combo_komponenta.pack(fill="x", pady=5)
    combo_komponenta.set("")
    
    def prov_servis_komponenty():
        komponenta = combo_komponenta.get()
        hromadny_servis_komponenty(komponenta)
    
    tk.Button(frame_servis_komponenta, text="Provést servis vybrané komponenty", command=prov_servis_komponenty, bg="#D3D3D3", width=30).pack(pady=5)

def otevri_detaily_vozidla(event):
    selected = strom.selection()
    if not selected:
        return
    
    item = selected[0]
    vpz = strom.item(item, "values")[0]
    
    with db.pripoj() as conn:
        vozidlo = conn.execute(
            "SELECT vozidlo_id, vpz, vyrobce, model, typ_vozidla, vin FROM Vozidlo WHERE vpz=?",
            (vpz,)
        ).fetchone()
    
    if not vozidlo:
        return
    
    vozidlo_id, vpz, vyrobce, model, typ_vozidla, vin = vozidlo
    
    # Pokud je okno již otevřeno, dej mu focus
    if vozidlo_id in otevena_detaily_okna:
        window = otevena_detaily_okna[vozidlo_id]
        if window is not None:
            try:
                window.lift()
                window.focus()
            except:
                del otevena_detaily_okna[vozidlo_id]
        return
    
    # Přidej sentinel, aby další klik věděl, že se okno právě otvírá
    otevena_detaily_okna[vozidlo_id] = None
    
    # Vytvori nove okno
    detaily_okno = tk.Toplevel(okno)
    detaily_okno.title(f"Detaily vozidla - {vpz}")
    detaily_okno.geometry("550x400")
    
    # Zaregistruj okno
    otevena_detaily_okna[vozidlo_id] = detaily_okno
    
    # Odeberi okno ze slovníku, když se zavře
    def on_closing():
        if vozidlo_id in otevena_detaily_okna:
            del otevena_detaily_okna[vozidlo_id]
        if vozidlo_id in aktualizuj_detaily_funkce:
            del aktualizuj_detaily_funkce[vozidlo_id]
        aktualizuj()  # Obnovit hlavní okno
        detaily_okno.destroy()
    
    detaily_okno.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Nadpis s km
    with db.pripoj() as conn:
        vozidlo_data = conn.execute(
            "SELECT aktualni_km FROM Vozidlo WHERE vozidlo_id=?",
            (vozidlo_id,)
        ).fetchone()
        aktualni_km = vozidlo_data[0] if vozidlo_data else 0
    
    nadpis = tk.Label(detaily_okno, text=f"{vyrobce} {model} ({vpz} - {vin}) | {aktualni_km} km", font=("Arial", 12, "bold"))
    nadpis.pack(pady=10)
    
    # Tabulka komponent
    frame_komponenty = ttk.Frame(detaily_okno)
    frame_komponenty.pack(fill="both", expand=True, padx=10, pady=10)
    
    strom_komponenty = ttk.Treeview(frame_komponenty, columns=("komponenta", "posledni_servis", "dalsi_servis", "stav"), show="headings", height=10)
    
    strom_komponenty.heading("komponenta", text="Komponenta")
    strom_komponenty.heading("posledni_servis", text="Poslední servis")
    strom_komponenty.heading("dalsi_servis", text="Příští servis")

    strom_komponenty.heading("stav", text="Stav")
    
    strom_komponenty.column("komponenta", width=100)
    strom_komponenty.column("posledni_servis", width=120)
    strom_komponenty.column("dalsi_servis", width=120)
    strom_komponenty.column("stav", width=80)
    
    strom_komponenty.tag_configure("ok", background="#b7f7b7")
    strom_komponenty.tag_configure("warning", background="#FFFF99")
    strom_komponenty.tag_configure("bad", background="#f7b7b7")
    strom_komponenty.tag_configure("planned", background="#FFA500")
    strom_komponenty.tag_configure("crashed", background="#FF4444")
    strom_komponenty.tag_configure("repair", background="#FFA07A")
    
    strom_komponenty.pack(fill="both", expand=True)
    
    def otevri_servis_komponenty(event):
        selected_komp = strom_komponenty.selection()
        if not selected_komp:
            return
        
        item = selected_komp[0]
        komponenta = strom_komponenty.item(item, "values")[0]
        
        # Pokud je okno již otevřeno, dej mu focus
        servis_key = (vozidlo_id, komponenta)
        if servis_key in otevena_servis_okna:
            window = otevena_servis_okna[servis_key]
            if window is not None:
                try:
                    window.lift()
                    window.focus()
                except:
                    del otevena_servis_okna[servis_key]
            return
        
        # Přidej sentinel
        otevena_servis_okna[servis_key] = None
        
        # Okno pro servis
        servis_okno = tk.Toplevel(detaily_okno)
        servis_okno.title(f"Servis - {komponenta}")
        servis_okno.geometry("400x200")
        
        # Zaregistruj okno
        otevena_servis_okna[servis_key] = servis_okno
        
        # Odeberi okno ze slovníku, když se zavře
        def on_closing_servis():
            if servis_key in otevena_servis_okna:
                del otevena_servis_okna[servis_key]
            servis_okno.destroy()
        
        servis_okno.protocol("WM_DELETE_WINDOW", on_closing_servis)
        
        # Nadpis
        nadpis_servis = tk.Label(servis_okno, text=f"Servis komponenty: {komponenta}", font=("Arial", 11, "bold"))
        nadpis_servis.pack(pady=10)
        
        # Frame pro data
        frame_data = ttk.Frame(servis_okno)
        frame_data.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(frame_data, text="Datum servisu:").grid(row=0, column=0, sticky="w", pady=5)
        entry_datum = ttk.Entry(frame_data, width=30)
        entry_datum.grid(row=0, column=1, pady=5)
        entry_datum.insert(0, db.ziskej_datum().strftime('%d-%m-%Y'))
        
        ttk.Label(frame_data, text="(formát: DD-MM-YYYY)").grid(row=1, column=1, sticky="w")
        
        def provest_servis():
            try:
                dnes = db.ziskej_datum()
                logika.zapis_servis(vozidlo_id, komponenta)
                messagebox.showinfo("Úspěch", f"Servis {komponenta} proveden na {dnes.strftime('%d-%m-%Y')}")
                aktualizuj_detaily()
                aktualizuj()  # Obnovit hlavní okno
                servis_okno.destroy()
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba: {str(e)}")
        
        def naplanovani_servis():
            try:
                datum_str = entry_datum.get().strip()
                datum = __import__('datetime').datetime.strptime(datum_str, '%d-%m-%Y').date()
                aktualni_km = db.ziskej_km_vozidla(vozidlo_id)
                
                with db.pripoj() as conn:
                    # Zkontroluj, zda už existuje záznam
                    existing = conn.execute("""
                        SELECT zaznam_id FROM ServisniZaznam
                        WHERE vozidlo_id=? AND komponenta=?
                    """, (vozidlo_id, komponenta)).fetchone()
                    
                    if existing:
                        conn.execute("""
                            UPDATE ServisniZaznam
                            SET posledni_servis=?, posledni_servis_km=?
                            WHERE vozidlo_id=? AND komponenta=?
                        """, (datum.isoformat(), aktualni_km, vozidlo_id, komponenta))
                    else:
                        conn.execute("""
                            INSERT INTO ServisniZaznam (vozidlo_id, komponenta, posledni_servis, posledni_servis_km)
                            VALUES (?, ?, ?, ?)
                        """, (vozidlo_id, komponenta, datum.isoformat(), aktualni_km))
                    
                    conn.commit()
                
                messagebox.showinfo("Úspěch", f"Servis {komponenta} naplánován na {datum.strftime('%d-%m-%Y')}")
                aktualizuj_detaily()
                aktualizuj()  # Obnovit hlavní okno
                servis_okno.destroy()
            except ValueError:
                messagebox.showerror("Chyba", "Neplatný formát data! Použij DD-MM-YYYY")
            except Exception as e:
                messagebox.showerror("Chyba", f"Chyba: {str(e)}")
        
        # Tlačítka
        frame_buttons = ttk.Frame(servis_okno)
        frame_buttons.pack(pady=10)
        
        tk.Button(frame_buttons, text="Provést servis", command=provest_servis, bg="#b7f7b7", width=18).pack(side="left", padx=5)
        tk.Button(frame_buttons, text="Naplánovat servis", command=naplanovani_servis, bg="#87ceeb", width=18).pack(side="left", padx=5)
    
    # Event na dvojklik v tabulce komponent
    strom_komponenty.bind("<Double-1>", otevri_servis_komponenty)
    
    def aktualizuj_detaily():
        for row in strom_komponenty.get_children():
            strom_komponenty.delete(row)
        
        dnes = db.ziskej_datum()
        aktualni_km = db.ziskej_km_vozidla(vozidlo_id)
        
        for komponenta in logika.KOMPONENTY:
            posledni = logika.ziskej_posledni_servis(vozidlo_id, komponenta)
            interval = logika.ziskej_interval(typ_vozidla, komponenta)
            
            if posledni:
                posledni_datum, posledni_km = posledni
                posledni_text = posledni_datum.strftime('%d-%m-%Y')
            else:
                posledni_datum = None
                posledni_text = "Nikdy"
            
            # Vypočítej nejzažší termín
            if posledni_datum:
                nejnezsi_termin = posledni_datum + __import__('datetime').timedelta(days=interval)
                nejnezsi_termin_text = nejnezsi_termin.isoformat()
                # Vypočítej zbývající dny
                zbyvajici_dny = (nejnezsi_termin - dnes).days
            else:
                nejnezsi_termin_text = "Nikdy"
                zbyvajici_dny = None
            
            # Získej stav komponenty z logiky
            stav_text = logika.ziskej_stav_komponenty(vozidlo_id, komponenta)
            
            # Urči tag podle stavu
            if stav_text == "POSKOZENE":
                tag = "crashed"
            elif stav_text == "V OPRAVE":
                tag = "repair"
            elif stav_text == "PLANOVANY SERVIS":
                tag = "planned"
            elif stav_text == "POTŘEBA SERVISU":
                tag = "bad"
            elif zbyvajici_dny is not None and zbyvajici_dny <= 7:
                tag = "warning"
            else:
                tag = "ok"
            
            strom_komponenty.insert("", "end", values=(komponenta, posledni_text, nejnezsi_termin_text, stav_text),
                                   tags=(tag,))
    
    # Naplni tabulku daty
    aktualizuj_detaily()
    
    # Ulož referenci na aktualizuj_detaily funkci
    aktualizuj_detaily_funkce[vozidlo_id] = aktualizuj_detaily

def otevri_pridani_vozidla():
    global otevena_pridani_okna
    
    # Pokud je okno již otevřeno, dej mu focus
    if otevena_pridani_okna is not None:
        try:
            otevena_pridani_okna.lift()
            otevena_pridani_okna.focus()
        except:
            otevena_pridani_okna = None
        else:
            return
    
    # Označit, že se okno vytváří
    class Sentinel: pass
    otevena_pridani_okna = Sentinel()
    
    # Vytvoří nové okno pro přidání vozidla
    pridani_okno = tk.Toplevel(okno)
    pridani_okno.title("Přidat nové vozidlo")
    pridani_okno.geometry("400x500")
    
    # Zaregistruj okno
    otevena_pridani_okna = pridani_okno
    
    # Odeberi okno ze proměnné, když se zavře
    def on_closing():
        global otevena_pridani_okna
        otevena_pridani_okna = None
        pridani_okno.destroy()
    
    pridani_okno.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Nadpis
    nadpis = tk.Label(pridani_okno, text="Přidat nové vozidlo", font=("Arial", 12, "bold"))
    nadpis.pack(pady=10)
    
    # Formulář
    frame_form = ttk.Frame(pridani_okno)
    frame_form.pack(fill="both", expand=True, padx=10, pady=10)
    
    # VIN
    ttk.Label(frame_form, text="VIN:").grid(row=0, column=0, sticky="w", pady=5)
    entry_vin = ttk.Entry(frame_form, width=40)
    entry_vin.grid(row=0, column=1, pady=5)
    
    # VPZ
    ttk.Label(frame_form, text="VPZ:").grid(row=1, column=0, sticky="w", pady=5)
    entry_vpz = ttk.Entry(frame_form, width=40)
    entry_vpz.grid(row=1, column=1, pady=5)
    
    # Funkce pro automatické formátování VPZ - pouze číslice
    def format_vpz(event):
        text = entry_vpz.get().replace(" ", "").replace("-", "")
        # Filtruj pouze číslice
        text = ''.join(c for c in text if c.isdigit())
        if len(text) > 7:
            text = text[:7]
        if len(text) >= 3:
            formatted = text[:3]
            if len(text) >= 5:
                formatted += " " + text[3:5] + "-" + text[5:]
            elif len(text) > 3:
                formatted += " " + text[3:]
            entry_vpz.delete(0, tk.END)
            entry_vpz.insert(0, formatted)
    
    entry_vpz.bind("<KeyRelease>", format_vpz)
    
    # Vyrobce
    ttk.Label(frame_form, text="Vyrobce:").grid(row=2, column=0, sticky="w", pady=5)
    vyrobci = ["Toyota", "Land Rover", "Skoda", "Tatra", "IVECO", "TDV", "Nexter Systems", "KMW", "ZTS", "Mercedes-Benz", "Volkswagen", "Avia"]
    combo_vyrobce = ttk.Combobox(frame_form, values=sorted(vyrobci), width=37)
    combo_vyrobce.grid(row=2, column=1, pady=5)
    
    # Model
    ttk.Label(frame_form, text="Model:").grid(row=3, column=0, sticky="w", pady=5)
    entry_model = ttk.Entry(frame_form, width=40)
    entry_model.grid(row=3, column=1, pady=5)
    
    # Typ vozidla
    ttk.Label(frame_form, text="Typ vozidla:").grid(row=4, column=0, sticky="w", pady=5)
    combo_typ = ttk.Combobox(frame_form, values=["sluzebni", "nakladni", "takticke", "bojove"], state="readonly", width=37)
    combo_typ.grid(row=4, column=1, pady=5)
    combo_typ.current(0)
    
    # Barva
    ttk.Label(frame_form, text="Barva:").grid(row=5, column=0, sticky="w", pady=5)
    entry_barva = ttk.Entry(frame_form, width=40)
    entry_barva.grid(row=5, column=1, pady=5)
    
    ttk.Label(frame_form, text="Počet kol:").grid(row=6, column=0, sticky="w", pady=5)
    entry_kola = ttk.Entry(frame_form, width=40)
    entry_kola.grid(row=6, column=1, pady=5)
    
    ttk.Label(frame_form, text="Rok:").grid(row=7, column=0, sticky="w", pady=5)
    entry_rok = ttk.Entry(frame_form, width=40)
    entry_rok.grid(row=7, column=1, pady=5)
    
    ttk.Label(frame_form, text="Najeté km:").grid(row=8, column=0, sticky="w", pady=5)
    entry_km = ttk.Entry(frame_form, width=40)
    entry_km.grid(row=8, column=1, pady=5)
    
    def ulozit_vozidlo():
        try:
            vin = entry_vin.get().strip().upper()
            vpz = entry_vpz.get().strip().upper()
            vyrobce = combo_vyrobce.get().strip()
            model = entry_model.get().strip()
            typ_vozidla = combo_typ.get().strip()
            barva = entry_barva.get().strip()
            pocet_kol = int(entry_kola.get().strip()) if entry_kola.get().strip() else None
            rok = int(entry_rok.get().strip()) if entry_rok.get().strip() else None
            aktualni_km = int(entry_km.get().strip()) if entry_km.get().strip() else 0
            
            if not vin or not vpz or not vyrobce or not model or not typ_vozidla:
                tk.messagebox.showerror("Chyba", "Všechna povinná pole musí být vyplněna!", parent=pridani_okno)
                return
            
            import re
            if len(vin) != 17:
                tk.messagebox.showerror("Chyba", "VIN musí mít přesně 17 znaků!", parent=pridani_okno)
                return
            if not re.match(r'^[A-Z0-9]{17}$', vin):
                tk.messagebox.showerror("Chyba", "VIN může obsahovat pouze velká písmena (A-Z) a číslice (0-9)!", parent=pridani_okno)
                return
            
            if not re.match(r'^[0-9]{3} [0-9]{2}-[0-9]{2}$', vpz):
                tk.messagebox.showerror("Chyba", "VPZ musí být ve formátu 'xxx xx-xx' a obsahovat pouze číslice (např. '212 97-56')!", parent=pridani_okno)
                return
            
            with db.pripoj() as conn:
                existujici_vin = conn.execute("SELECT COUNT(*) FROM Vozidlo WHERE vin = ?", (vin,)).fetchone()[0]
                if existujici_vin > 0:
                    tk.messagebox.showerror("Chyba", "Vozidlo s tímto VIN již existuje!", parent=pridani_okno)
                    return
                
                existujici_vpz = conn.execute("SELECT COUNT(*) FROM Vozidlo WHERE vpz = ?", (vpz,)).fetchone()[0]
                if existujici_vpz > 0:
                    tk.messagebox.showerror("Chyba", "Vozidlo s tímto VPZ již existuje!", parent=pridani_okno)
                    return
                
                conn.execute("""
                    INSERT INTO Vozidlo (vin, vpz, vyrobce, model, typ_vozidla, barva, pocet_kol, rok, aktualni_km)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (vin, vpz, vyrobce, model, typ_vozidla, barva, pocet_kol, rok, aktualni_km))
                conn.commit()
            
            tk.messagebox.showinfo("Úspěch", "Vozidlo bylo úspěšně přidáno!", parent=pridani_okno)
            
            pridani_okno.destroy()
            aktualizuj()
        except ValueError:
            tk.messagebox.showerror("Chyba", "Počet kol, rok a km musí být čísla!", parent=pridani_okno)
        except Exception as e:
            tk.messagebox.showerror("Chyba", f"Chyba při ukládání: {str(e)}", parent=pridani_okno)
    
    frame_buttons = ttk.Frame(pridani_okno)
    frame_buttons.pack(pady=10)
    
    tk.Button(frame_buttons, text="Uložit", command=ulozit_vozidlo, bg="#b7f7b7", width=15).pack(side="left", padx=5)
    tk.Button(frame_buttons, text="Zrušit", command=pridani_okno.destroy, bg="#f7b7b7", width=15).pack(side="left", padx=5)

okno = tk.Tk()
okno.title("Databáze vozového parku")
okno.geometry("1050x600")

datum_label = tk.Label(okno, font=("Arial", 14))
datum_label.pack(pady=10)

frame_buttons = tk.Frame(okno)
frame_buttons.pack()

tk.Button(frame_buttons, text="Přidat vozidlo", command=otevri_pridani_vozidla, bg="#D3D3D3", width=15).pack(side="left", padx=5)
tk.Button(frame_buttons, text="Admin panel", command=otevri_admin_panel, bg="#D3D3D3", width=15).pack(side="left", padx=5)
tk.Button(frame_buttons, text="Plán výjezdů", command=otevri_kalendar, bg="#D3D3D3", width=15).pack(side="left", padx=5)
tk.Button(frame_buttons, text="Mimořádná událost", command=otevri_mimoradnou_udalost, bg="#D3D3D3", width=18).pack(side="left", padx=5)
tk.Button(frame_buttons, text="Zavřít databázi", command=zavrit_databazi, bg="#f7b7b7", width=15).pack(side="left", padx=5)

frame_filtr = tk.Frame(okno)
frame_filtr.pack(pady=5)

tk.Label(frame_filtr, text="Filtrovat dle typu:").pack(side="left", padx=5)
combo_typ = ttk.Combobox(frame_filtr, values=["vše", "sluzebni", "nakladni", "takticke", "bojove"], state="readonly", width=15)
combo_typ.pack(side="left", padx=5)
combo_typ.set("vše")
combo_typ.bind("<<ComboboxSelected>>", na_zmenu_typu)

tk.Label(frame_filtr, text="Filtrovat dle stavu:").pack(side="left", padx=5)
combo_stav = ttk.Combobox(frame_filtr, values=["vše", "DOSTUPNE", "PLANOVANY SERVIS", "SLUZEBNI CESTA", "HAVAROVANO", "V OPRAVE", "NEDOSTUPNE", "DEAKTIVOVANO"], state="readonly", width=20)
combo_stav.pack(side="left", padx=5)
combo_stav.set("vše")
combo_stav.bind("<<ComboboxSelected>>", na_zmenu_stavu)

strom = ttk.Treeview(okno, columns=("vpz", "vyrobce", "model", "typ", "stav"), show="headings")

strom.heading("vpz", text="VPZ")
strom.heading("vyrobce", text="Vyrobce")
strom.heading("model", text="Model")
strom.heading("typ", text="Typ")
strom.heading("stav", text="Stav")

strom.tag_configure("ok", background="#b7f7b7")
strom.tag_configure("bad", background="#f7b7b7")
strom.tag_configure("planned", background="#FFA500")
strom.tag_configure("borrowed", background="#FFD700")
strom.tag_configure("crashed", background="#FF4444")
strom.tag_configure("repair", background="#FFA07A")
strom.tag_configure("dead", background="#D3D3D3")

strom.pack(fill="both", expand=True, padx=10, pady=10)

strom.bind("<Double-1>", otevri_detaily_vozidla)

aktualizuj()
okno.mainloop()
