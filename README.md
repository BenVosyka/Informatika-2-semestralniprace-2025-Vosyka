# Motorpool - Systém správy vozového parku

## Popis projektu

**Motorpool** je desktopová aplikace pro správu vozového parku vojenského útvaru. Systém umožňuje evidenci vozidel, plánování servisních úkonů, rezervace vozidel pro služební cesty a sledování plánovaných i mimořádných událostí. Aplikace pracuje se simulovaným časem, což umožňuje plynulou demonstraci funkčnosti.

### Proč vznikl tento projekt?

Projekt je semestrální prací z předmětu Informatika 2 s cílem vyvinout praktickou aplikaci pro správu vozového parku. Hlavní motivace zahrnují:

- **Motivace dostat se do čtvrtého semestru**: Když už to pan desátník dotáhl až sem, inženýrský titul zdá se být co by kamenem dohodil
- **Efektivní správa údržby**: Automatické sledování servisních intervalů dle času i kilometrů (km jen v testovací fázi)
- **Prevence kolizí**: Systém rezervací zajišťuje, že vozidlo nemůže být současně na více místech
- **Evidence škod**: Rychlé zaznamenání nehod a sledování oprav
- **Transparentnost**: Přehledné zobrazení stavu všech vozidel v reálném čase
- **Optimalizace výkonu**: Díky cachování a indexaci je systém rychlý i s desítkami vozidel a stovkami záznamů

## Hlavní funkce

### 1. **Správa vozidel**
- Evidence vozidel s detailními údaji (VIN, VPZ, výrobce, model, typ, barva, kilometry)
- Validace vstupů (VIN 17 znaků, VPZ formát `xxx xx-xx`)
- Kontrola unikátnosti VIN a VPZ
- Automatické vyřazení vozidel po dosažení maximálního kilometrového limitu
- Kategorie vozidel: služební, nákladní, taktické, bojové

### 2. **Servisní management**
- Automatické sledování 10 komponent (motor, převodovka, brzdy, světla, pneumatiky, diferenciál, nápravy, tlumiče, olej, chladicí kapalina)
- Individuální servisní intervaly pro každý typ vozidla (časové i kilometrové)
- Barevné rozlišení stavů:
  - 🟢 **OK** - vše v pořádku
  - 🟠 **PLÁNOVANÝ SERVIS** - blíží se termín servisu
  - 🔴 **POTŘEBA SERVISU** - překročen časový interval servisu
  - 🔴 **POŠKOZENÉ** - po mimořádné události
  - 🟠 **V OPRAVĚ** - aktivní oprava
- Hromadný servis všech vozidel nebo jednotlivých komponent
- Admin panel pro rychlé servisní úkony a demonstrace funkcí

### 3. **Plán výjezdů (Kalendář)**
- Vizuální kalendář pro plánování služebních cest (inspirace v DEPO)
- Rezervace vozidel na konkrétní dny
- Automatická detekce kolizí (vozidlo nelze rezervovat vícekrát)
- Zobrazení obsazenosti vozidel přímo v kalendáři
- Filtrování podle typu vozidla a VPZ
- Osobní údaje řidiče (hodnost, jméno, příjmení)

### 4. **Mimořádné události**
- Evidence nehod a havárií
- Omezené časové okno hlášení (±3 dny od aktuálního data)
- Automatické nastavení stavu vozidla na HAVAROVÁNO
- 4denní doba nedostupnosti vozidla po nehodě
- Automatické označení poškozených komponent (testováno - tbc)

### 5. **Simulovaný čas**
- Posun času vpřed pomocí tlačítek +1, +7 a +30
- Automatická aktualizace stavů vozidel při změně data
- Testování bez čekání na reálný čas

### 6. **Výkonnostní optimalizace**
- **Cache systém**: Zrychlení načítání stavů vozidel až 10×
- **6 databázových indexů**: Optimalizace dotazů na servisní záznamy, zápůjčky a události
- **Inteligentní aktualizace**: Pouze viditelná okna se překreslují
- **Batch operace**: Hromadné SQL operace místo jednotlivých dotazů

## Technologie

- **Jazyk**: Python 3.x
- **GUI**: tkinter (standardní knihovna)
- **Databáze**: SQLite3 (embedded)
- **Architektura**: 3vrstvá (GUI, business logika, datová vrstva)

### Struktura projektu

```
motorpool/
├── main.py          # GUI aplikace (1475 řádků)
├── db.py            # Databázová vrstva (CRUD operace)
├── logika.py        # Business logika (stavy vozidel, validace)
├── schema.sql       # DDL schema + testovací data
├── motorpool.db     # SQLite databáze (generována automaticky)
├── spustit.bat      # Windows spouštěč
└── README.md        # Tento soubor
```

## Instalace a spuštění

### Požadavky
- Python 3.7 nebo novější
- Žádné externí závislosti (vše je ve standardní knihovně)

### Spuštění (Windows)
```bash
spustit.bat
```

### Spuštění (Linux/Mac)
```bash
python main.py
```

### První spuštění
Při prvním spuštění se automaticky:
1. Vytvoří databáze `motorpool.db`
2. Inicializují tabulky podle `schema.sql`
3. Naplní testovací data (30 vozidel)
4. Vygenerují servisní záznamy pro všechny komponenty

## Ovládání

### Hlavní okno
- **Přidat vozidlo**: Formulář pro přidání nového vozidla
- **Admin panel**: Hromadné servisní operace
- **Plán výjezdů**: Kalendář pro rezervace
- **Mimořádná událost**: Hlášení nehody
- **Zavřít databázi**: Ukončení aplikace
- **Filtry**: Typ vozidla a stav (dostupné, v servisu, havarované, atd.)
- **Tlačítka**: Změna simulovaného data

### Detaily vozidla (dvojklik na vozidlo)
- Kompletní informace o vozidle
- Přehled všech 10 komponent s barevným označením
- Tlačítko **Servis komponenty**: Provede servis vybrané komponenty
- Aktuální najeté kilometry a rok výroby

### Plán zápůjček vozidel
- **Výběr vozidla**: Filtrování podle typu a VPZ
- **Výběr datového rozsahu**: Označení dnů pro rezervaci
- **Pole Od-Do**: Zobrazení rozsahu vybraných dnů
- **Potvrdit rezervaci**: Uložení zápůjčky
- **Šipky < >**: Přepínání měsíců

## Databázové schema

### Klíčové tabulky
- **Vozidlo**: Evidence vozidel
- **ServisniZaznam**: Historie servisů komponent
- **ServisniPravidlo**: Časové intervaly servisu
- **KilometrovePravidlo**: Kilometrové intervaly servisu
- **Zapujcka**: Rezervace vozidel
- **MimoradnaUdalost**: Nehody a havárie
- **SystemCas**: Simulovaný čas
- **VstupniServis**: Datum uvedení vozidla do provozu
- **ZivotnostVozidla**: Maximální kilometry pro každý typ

### Indexy pro výkon
```sql
idx_servisni_zaznam_vozidlo_komponenta
idx_zapujcka_vozidlo_datum
idx_mimoradna_udalost_vozidlo_datum
idx_vozidlo_typ
idx_servisni_pravidlo_lookup
idx_kilometrove_pravidlo_lookup
```

## Testovací data

Databáze obsahuje 30 testovacích vozidel:
- **11× Toyota Hilux** (zelená, služební)
- **5× Škoda Fabia** (černá/bílá, služební)
- **5× Land Rover Defender** (zelená/písková, taktické)
- **12× Tatra 815-7 / 810** (zelená, nákladní)
- **5× IVECO LMV CZ5** (zelená/písková, ta0ktické)
- **5× TDV Pandur II** (zelená/písková, bojové)
- **5× Nexter TITUS** (zelená/písková, taktické)
- **5× KMW Dingo 2** (zelená/písková, taktické)
- **5× ZTS DANA** (zelená/písková, bojové)

Některá vozidla mají najeté kilometry nad limit a jsou automaticky vyřazena (DEAKTIVOVÁNO).

## Historie verzí

### Verze 1.0 (Současná verze) - Finální vydání
**Datum**: Leden 2026  
**Změny**:
-  Nahrazení filtru "Přítomnost" za vyhledávání podle VPZ
-  Prodloužení hlavního okna na 1050×600 px
-  Změna stavu testovacích dat (30 vozidel, 8 vyřazených)
-  Stabilní verze připravená k nasazení

### Verze 0.95 - Rozšíření testovacích dat
**Datum**: Leden 2026  
**Změny**:
-  Rozšíření testovací skupiny z 10 na 30 vozidel
-  Automatické vytvoření VstupniServis záznamů pro všechna vozidla
-  Proporční zastoupení všech výrobců a typů
-  Nastavení 8 vozidel nad kilometrový limit pro testování vyřazení

### Verze 0.90 - Velká optimalizace výkonu
**Datum**: Leden 2025  
**Změny**:
-  Implementace cache systému pro stavy vozidel (5-10× rychlejší)
-  Přidání 6 databázových indexů (2-5× rychlejší dotazy)
-  Refaktoring SQL dotazů (50-100× rychlejší hromadné operace)
-  Optimalizace aktualizace oken (kontrola `winfo_exists()`)
-  Přepis `admin_servis()` z O(N×M) na O(1) složitost
-  Optimalizace `hromadny_servis_komponenty()` pomocí batch UPDATE+INSERT
-  Zjednodušení `aplikuj_filtr()` pomocí dictionary lookup

### Verze 0.80 - UI refinements
**Datum**: Prosinec 2025  
**Změny**:
-  Změna velikosti kalendářního okna (660×660 → 750×750)
-  Oprava hodnosti "nrmt." → "nrtm."
-  Přidání osobních údajů do kalendáře (hodnost, jméno, příjmení)
-  Změna názvu komponenty "chladici" → "chladici kapalina"
-  Zmenšení bloků v kalendáři (width 8→6, height 3→2)

### Verze 0.70 - Vylepšení formulářů
**Datum**: Prosinec 2025  
**Změny**:
-  Validace VIN (17 znaků, A-Z 0-9, kontrola unikátnosti)
-  Validace VPZ (formát xxx xx-xx, pouze čísla, auto-formátování)
-  Combobox pro výrobce (12 přednastavených výrobců)
-  Combobox pro typ vozidla (readonly, 4 typy)
-  Automatické převedení VIN na velká písmena
-  Kontrola duplicit VIN/VPZ v databázi

### Verze 0.60 - Stavy komponent při nehodě
**Datum**: Prosinec 2025  
**Změny**:
-  Přidání stavů komponent "POŠKOZENÉ" a "V OPRAVĚ"
-  Barevné označení (crashed=#FF4444, repair=#FFA07A)
-  Propojení stavu vozidla (HAVAROVÁNO) se stavem komponent
-  Automatické nastavení POŠKOZENÉ při vytvoření nehody
-  Automatický přechod POŠKOZENÉ → V OPRAVĚ → OK

### Verze 0.50 - Omezení hlášení nehod
**Datum**: Prosinec 2025  
**Změny**:
-  Omezení výběru data nehody na ±3 dny od aktuálního data
-  Změna ze spinboxů na combobox s předvyplněnými daty
-  Zamezení hlášení nehod v budoucnosti nebo vzdálené minulosti
-  Validace rozsahu při potvrzení nehody

### Verze 0.40 - Databázové schema
**Datum**: Listopad 2025  
**Změny**:
- 🗄️ Vytvoření kompletního databázového schematu
- 📋 9 tabulek (Vozidlo, ServisniZaznam, ServisniPravidlo, KilometrovePravidlo, Zapujcka, MimoradnaUdalost, SystemCas, VstupniServis, ZivotnostVozidla)
-  10 komponent pro každé vozidlo
-  Časové a kilometrové intervaly pro 4 typy vozidel
-  Testovací data (původně 10 vozidel)

### Verze 0.30 - Kalendář a rezervace
**Datum**: Listopad 2025  
**Změny**:
-  Vizuální kalendář pro plánování služebních cest
-  Detekce kolizí při rezervaci
-  Barevné označení obsazených dnů
-  Navigace mezi měsíci
-  Formulář pro vytvoření zápůjčky

### Verze 0.20 - Admin panel a servis
**Datum**: Listopad 2025  
**Změny**:
-  Admin panel pro hromadné servisní operace
-  Servis všech vozidel najednou
-  Servis konkrétní komponenty u všech vozidel
-  Detaily vozidla s přehledem komponent
-  Barevné rozlišení stavů komponent

### Verze 0.10 - Základní funkce
**Datum**: Říjen 2025  
**Změny**:
-  Základní architektura (main.py, db.py, logika.py)
-  Hlavní okno s tabulkou vozidel
-  Formulář pro přidání vozidla
-  Filtry podle typu a stavu
-  Simulovaný čas s posuvem
-  Barevné tagy pro stavy vozidel

---

## Autor

**Benjamin Vosyka**  
Semestrální práce - Informatika 2  
Zima 2025/2026

## Licence

Tento projekt je vytvořen pro vzdělávací účely.
