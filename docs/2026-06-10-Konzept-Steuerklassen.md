# Konzept: Steuerklasse & Kinderfreibeträge im Rente-O-Mat (v2)

## Motivation

R-O-M fragt bisher weder Steuerklasse noch Kinderfreibeträge ab. Beide beeinflussen die monatliche Lohnsteuer und damit das simulierte Netto. Jeder Arbeitnehmer kennt seine Steuerklasse — sie steht auf jedem Gehaltszettel. Andere Brutto-Netto-Rechner fragen sie standardmäßig ab.

---

## Neue UI-Elemente

Im Expander **"💶 Erwerbseinnahmen"** (nach dem Brutto-Input):

```python
steuerklasse = st.selectbox(
    "Steuerklasse",
    options=[1, 2, 3, 4, 5],
    index=0,  # Default: StKl 1
    key="steuerklasse_key",
    help="Deine Lohnsteuerklasse (steht auf deinem Gehaltszettel). "
         "StKl 1: Ledig | StKl 2: Alleinerziehend | "
         "StKl 3: Verheiratet (Allein-/Besserverdiener) | "
         "StKl 4: Verheiratet (beide ähnlich) | "
         "StKl 5: Verheiratet (Geringverdiener-Partner)"
)

kinderfreibetrag = st.number_input(
    "Kinderfreibeträge (lt. Lohnsteuerbescheinigung)",
    min_value=0.0, max_value=10.0, step=0.5,
    value=0.0,
    key="kinderfreibetrag_key",
    help="Anzahl der Kinderfreibeträge (z.B. 0.5 pro Kind bei Steuerklasse 4). "
         "Steht auf deiner Lohnsteuerbescheinigung. "
         "Beeinflusst Solidaritätszuschlag und Kirchensteuer."
)

# Partner-Einkommen nur bei StKl 3/5 relevant (für Splittingtarif in Rentenphase)
partner_einkommen = 0.0
if steuerklasse in [3, 4, 5]:
    partner_einkommen = st.number_input(
        "Brutto Partner/in (mtl., optional)",
        min_value=0.0, step=100.0,
        key="partner_einkommen_key",
        help="Für den Splittingtarif in der Rentenphase. "
             "Falls leer: Simulation geht von Einzelveranlagung in der Rente aus."
    )
```

---

## Auswirkung der Steuerklasse auf die Berechnung

### Aktivphase (Lohnsteuer)

| StKl | EkSt-Berechnung | Besonderheiten |
|---|---|---|
| **1** | Grundtarif | Standard (aktuell) |
| **2** | Grundtarif − Entlastungsbetrag | +4.260€ Freibetrag für Alleinerziehende |
| **3** | Splittingtarif | `2 * ekst(zvE / 2)` |
| **4** | Grundtarif | Identisch zu StKl 1 |
| **5** | Grundtarif ohne Grundfreibetrag | `ekst(zvE + GF) − ekst(GF)` (Näherung) |

### Rentenphase

In der Rentenphase gibt es keine Lohnsteuerklassen. Es gilt:
- **Ledig / getrennt veranlagt**: Grundtarif (wie bisher)
- **Verheiratet (StKl 3/4/5)**: Splittingtarif (wenn Partner-Einkommen bekannt)

### Kinderfreibetrag

Der KiFB (2026: 9.312€ pro Kind, Hälfte = 4.656€) beeinflusst:
- **Soli**: Reduziert die Bemessungsgrundlage → kann unter Freigrenze drücken
- **KiSt**: Reduziert die Bemessungsgrundlage
- **EkSt**: **NICHT direkt** (Günstigerprüfung KiFB vs. Kindergeld am Jahresende)

```python
# Kinderfreibetrag 2026: 6.612€ + 2.700€ BEA = 9.312€ pro Kind
KINDERFREIBETRAG = {2026: 9312}

def berechne_soli_mit_kifb(ekst_jahr, kifb_anzahl, zve, jahr):
    """Soli mit Kinderfreibetrag-Abzug."""
    kifb_betrag = kifb_anzahl * KINDERFREIBETRAG.get(jahr, 9312)
    zve_soli = max(0, zve - kifb_betrag)
    ekst_soli = berechne_einkommensteuer(zve_soli, jahr)
    return berechne_soli(ekst_soli, jahr=jahr)
```

---

## Implementierungsplan

### 1. [taxes.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/taxes.py)

Neue Funktionen:

```python
KINDERFREIBETRAG = {2024: 9312, 2025: 9312, 2026: 9312}
ENTLASTUNGSBETRAG_ALLEINERZIEHEND = 4260  # §24b EStG

def berechne_lohnsteuer(zve, jahr, steuerklasse=1):
    """Monatliche Lohnsteuer nach Steuerklasse."""
    t = _get_tarif(jahr)
    
    if steuerklasse in [1, 4]:
        return berechne_einkommensteuer(zve, jahr)
    
    elif steuerklasse == 2:
        # Grundtarif + Entlastungsbetrag
        zve_korr = max(0, zve - ENTLASTUNGSBETRAG_ALLEINERZIEHEND)
        return berechne_einkommensteuer(zve_korr, jahr)
    
    elif steuerklasse == 3:
        # Splittingtarif
        return 2 * berechne_einkommensteuer(zve / 2, jahr)
    
    elif steuerklasse == 5:
        # Kein Grundfreibetrag → Steuer auf verschobenes Einkommen
        gf = t["grundfreibetrag"]
        return berechne_einkommensteuer(zve + gf, jahr) - berechne_einkommensteuer(gf, jahr)
    
    return berechne_einkommensteuer(zve, jahr)

def berechne_zuschlagsteuern(ekst_jahr, zve, kinderfreibetraege, kirchensteuer_satz, jahr, splitting=False):
    """Berechnet Soli und KiSt unter Berücksichtigung der Kinderfreibeträge."""
    kifb_betrag = kinderfreibetraege * KINDERFREIBETRAG.get(jahr, 9312)
    zve_zuschlag = max(0, zve - kifb_betrag)
    ekst_zuschlag = berechne_einkommensteuer(zve_zuschlag, jahr)
    
    soli = berechne_soli(ekst_zuschlag, splitting=splitting, jahr=jahr)
    kist = berechne_kirchensteuer(ekst_zuschlag, kirchensteuer_satz)
    return soli, kist
```

### 2. [engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py)

Im Aktiv-Block (ca. Z.246):

```python
steuerklasse = params.get('steuerklasse', 1)
kinderfreibetraege = params.get('kinderfreibetraege', 0.0)

# EkSt nach Steuerklasse
steuer_ekst = berechne_lohnsteuer(zve_jahr, jahr, steuerklasse) / 12

# Soli und KiSt mit Kinderfreibetrag
soli_jahr, kist_jahr = berechne_zuschlagsteuern(
    steuer_ekst * 12, zve_jahr, kinderfreibetraege, 
    kirchensteuer_satz, jahr, splitting=(steuerklasse == 3)
)
soli = soli_jahr / 12
kist = kist_jahr / 12
```

### 3. [sidebar.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py)

UI-Eingabefelder (siehe oben) + Return-Dict erweitern:

```python
"steuerklasse": steuerklasse,
"kinderfreibetraege": kinderfreibetrag,
"partner_einkommen": partner_einkommen,
```

### 4. Persistenz

Default-Werte in Session-State:
```python
"steuerklasse_key": 1,
"kinderfreibetrag_key": 0.0,
"partner_einkommen_key": 0.0,
```

---

## Offene Frage an den User

> [!IMPORTANT]
> **Die Netto-Diskrepanz (623€) kann NICHT allein durch die Steuerklasse erklärt werden.** StKl 4 = Grundtarif = exakt das, was R-O-M aktuell berechnet. Selbst mit KiSt (9%) und Soli ergibt sich ein simuliertes Netto von **~4.630€** vs. Dein echtes **4.129€**.
>
> Die verbleibenden ~500€ müssen aus einer anderen Quelle stammen:
> - Zusätzliche Posten auf dem Gehaltszettel (VWL, Firmenticket, Jobrad, etc.)?
> - Nachberechnung / Rückforderung aus Vormonat?
> - Gehaltszettel-Brutto ≠ das eingegebene Brutto (z.B. wegen geldwerter Vorteile)?
>
> **Tipp:** Vergleiche einmal Zeile für Zeile den aktuellen Gehaltszettel mit der R-O-M-Berechnung. Die SV-Aufschlüsselung (KV/PV/RV/ALV) habe ich ja bereits implementiert — aktiviere die Checkbox "Sozialabgaben aufschlüsseln" und prüfe jeden einzelnen Posten gegen den Gehaltszettel.
