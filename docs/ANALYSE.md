# 🔍 Rente-O-Mat: Umfassende Code-Review & PRD-Gap-Analyse

## Überblick

Alle 7 Quelldateien und 3 Markdown-Dokumente analysiert – als Python-Experte, als Kenner des deutschen Steuer-/Rentenrechts und aus Nutzersicht. Die Ergebnisse sind nach Schweregrad gegliedert.

---

## 🔴 KRITISCH – Fehler, die zu falschen Ergebnissen führen

### K1. Steuer-Tarif 2024 ist veraltet

**Datei:** `logic/taxes.py` (Z. 5–22)

Der EkSt-Tarif (§ 32a EStG) verwendet **Parameter von 2024**. Die App startet ab 2026 und simuliert bis Alter 95 (~2060). Seit 2025 gilt Grundfreibetrag 12.096€ (statt 11.604€).

**Auswirkung:** Steuer wird zu hoch berechnet – über 30 Jahre summieren sich Tausende Euro Abweichung.

**Fix:** Tarif-Tabelle nach Berechnungsjahr parametrisieren; für die Zukunft den zuletzt bekannten Tarif fortschreiben.

---

### K2. Sozialabgaben-Konstanten auf 2024 festgenagelt

**Datei:** `logic/engine.py` (Z. 20–28)

```python
BBG_KV_MONATLICH = 5175.0   # 2024 – VERALTET
BBG_RV_MONATLICH = 7550.0   # 2024 – VERALTET
```

2025: BBG_KV = 5.512,50 €, BBG_RV_West = 8.050 €. BBG steigen jährlich.

**Auswirkung:** SV-Beiträge systematisch falsch – in Aktiv- und Rentenphase.

---

### K3. ATZ-Phasen-Bug: `engine.py` vs. `app.py` ← **TRIVIAL ZU FIXEN!**

**Dateien:** `logic/engine.py` (Z. 4–18) vs. `app.py` (Z. 61)

- `engine.py` gibt `"ATZ(A)"` / `"ATZ(P)"` zurück
- `app.py` prüft `res['Phase'] == "ATZ"` → trifft **niemals** zu!
- ATZ-Fall fällt in den `else`-Zweig (Rente) → **Sankey zeigt Rentendaten statt ATZ-Daten**

```python
# BUG in app.py, Zeile 61:
elif res['Phase'] == "ATZ":          # ← matcht nie!

# FIX:
elif res['Phase'] in ["ATZ(A)", "ATZ(P)"]:
```

---

### K4. bAV wird falsch besteuert

**Datei:** `logic/engine.py` (Z. 74–76)

```python
if e["typ"] in ["Gesetzlich", "bAV"]:
    st_b += val * (r_ant / 100)   # ← FALSCH für bAV!
```

- **GRV:** Kohortenprinzip ✅
- **bAV:** 100% nachgelagert steuerpflichtig (§ 22 Nr. 5 EStG) – **kein** Kohortenprinzip!

**Fix:** bAV separat auf `st_b += val * 1.0` setzen.

---

### K5. Ausgaben-Anpassungsfaktor ignoriert ATZ(P)

`p == "Rente"` ist die einzige Bedingung für Ausgabenanpassung. In der ATZ-Passivphase (kein Pendeln, weniger Mobilität) sollten Anpassungen ebenfalls möglich sein. Im PRD nicht adressiert – Design-Entscheidung nötig.

---

## 🟠 HOCH – Erhebliche fachliche Mängel

### H1. Keine Inflation / Kaufkraftentwicklung

**Fehlt komplett.** Bei 2% Inflation verliert eine Rente von 2.200 € über 30 Jahre ~45% ihrer Kaufkraft. Die Aussage „ich bin versorgt" ist ohne Inflation **irreführend**.

Mindestens ein globaler Inflationsschieberegler (0–5%) sollte eingebaut werden, besser getrennt nach:
- Allgemeine Inflation (Ausgaben steigen)
- GRV-Rentenanpassung (~2% p.a.)
- bAV-Anpassung (§ 16 BetrAVG, ~1% p.a.)

---

### H2. Keine Rentenanpassung (Dynamisierung)

Alle Einnahmen sind über den gesamten Zeitraum **konstant**. GRV steigt real ~2% p.a., bAV mind. 1%. Das Tool unterschätzt systematisch die GRV und überschätzt die Kaufkraft privater Renten.

---

### H3. Kein Solidaritätszuschlag

Soli ist seit 2021 für die meisten entfallen, aber: ab ~17.500 € Jahressteuer wird er weiterhin erhoben (5,5%). Bei 6.000 € Brutto/Monat (72k€/Jahr) in der Aktivphase ist der Soli relevant.

---

### H4. Kirchensteuer fehlt

Für ~50% der deutschen Bevölkerung relevant: 8% oder 9% der EkSt (je nach Bundesland). Minimaler Implementierungsaufwand, großer Effekt auf die Genauigkeit.

---

### H5. Kein Ehegattensplitting

Großteil der Zielgruppe (Rentenplaner 55+) ist verheiratet. Splitting (§ 32a Abs. 5 EStG) kann Steuerlast massiv senken.

**Ohne Splitting ist das Tool für Verheiratete kaum nutzbar** – die Steuerbelastung wird systematisch zu hoch angesetzt.

---

### H6. SV in der Rentenphase stark vereinfacht / teilweise falsch

**Datei:** `logic/engine.py` (Z. 83–85)

```python
sv = min(brutto, BBG_KV_MONATLICH) * (RATE_KV_AN + 0.034)
```

Probleme:
1. **PV-Satz 3,4% ist für Kinderlose** – mit Kindern gestaffelt (ab 2024: -0,25% je Kind)
2. **Private Renten** unterliegen i.d.R. keiner KVdR-Beitragspflicht
3. **bAV** → voller KV+PV-Satz (AN+AG!), aber nur oberhalb Freibetrag (176,75 €/Monat in 2024)
4. Einheitlicher Satz auf Gesamt-Brutto statt differenziert pro Einkommensquelle

---

### H7. Ertragsanteil Private Rente pauschal 18%

**Datei:** `logic/engine.py` (Z. 78)

```python
st_b += val * 0.18  # Ertragsanteil – NUR für Alter 65 korrekt!
```

Ertragsanteil nach § 22 EStG hängt vom Alter bei Rentenbeginn ab:

| Alter | Ertragsanteil |
|-------|--------------|
| 60    | 22%          |
| 63    | 20%          |
| 65    | 18%          |
| 67    | 17%          |

---

### H8. Kapitalerträge: Typ vorhanden, Abgeltungssteuer-Logik fehlt

Typ `"Kapital"` in der Sidebar → fällt in `engine.py` in den `else`-Zweig → 100% progressiv versteuert. **Richtig:** Abgeltungsteuer 25% + Soli + KiSt, mit Sparerpauschbetrag 1.000 €/2.000 €.

---

## 🟡 MITTEL – Funktionale Mängel & UX

### M1. Kein `__init__.py` in den Packages

`logic/`, `ui/`, `data/` haben keine `__init__.py`. Funktioniert nur durch Streamlit-Pfad-Hack, bricht in anderen Kontexten.

### M2. `requirements.txt` fehlt

`numpy` (im PRD erwähnt) fehlt in README und nirgendwo eine definierte Abhängigkeitsverwaltung.

### M3. Sidebar-Reihenfolge kontraintuitiv

Meilensteine (Rentenbeginn, ATZ) werden **nach** dem Zeitstrahl-Slider gerendert, obwohl der Slider von diesen Werten abhängt.

**Bessere Reihenfolge:** Profil → Meilensteine → Finanzen → Einnahmen → Haushaltsbuch → Zeitstrahl

### M4. `aktuelles_jahr` auf 2026 hardcoded

```python
aktuelles_jahr = 2026   # ← Fix: datetime.now().year
```

### M5. Default-Rentenbeginn 2031 willkürlich

Sollte `geburtsjahr + 67` sein (Regelaltersgrenze ab Jahrgang 1964).

### M6. Keine kumulative Vermögensentwicklung

Das Trend-Chart zeigt nur Jahresscheiben. Die Kernfrage „Reicht mein Geld bis zum Lebensende?" braucht eine **Kurve des kumulierten Vermögens** (inkl. Anfangsvermögen + Rendite).

### M7. Keine Eingabevalidierung

- Rentenbeginn vor aktuellem Jahr möglich
- ATZ-Dauer > verbleibende Arbeitszeit möglich
- Einnahmen: Ende < Start möglich
- Negative Beträge werden akzeptiert
- Geburtsjahr kann in der Zukunft liegen

### M8. NaN-Behandlung im Trend-Chart fehlt

Einkommensquellen mit unterschiedlichen Gültigkeitszeiträumen erzeugen `NaN` in Spalten → Plotly zeigt Lücken in gestapelten Balken.

---

## 🟢 NICE-TO-HAVE – Was die Nutzerin vermissen wird

| ID | Feature | Warum wichtig |
|----|---------|--------------|
| N1 | Anfangsvermögen / Startvermögen + Rendite | Vermögensentwicklung erst damit sinnvoll |
| N2 | Sonderzahlungen (Abfindung, LV, Erbschaft) | Typische Übergangsereignisse |
| N3 | Szenario-Vergleich (z.B. Rente 63 vs. 67) | Kernentscheidung der Planung |
| N4 | Rentenabschläge/-zuschläge (0,3%/Monat) | Ohne das ist „Wann in Rente?" nicht beantwortbar |
| N5 | GRV aus Entgeltpunkten berechnen | Präzisere Eingabe statt Schätzwert |
| N6 | Hinterbliebenenabsicherung (Witwenrente) | Für Verheiratete hochrelevant |
| N7 | Grundrentenzuschlag | Für lange Beitragszeiten mit niedrigem Einkommen |
| N8 | PDF-Export | Für Steuer-/Finanzberater-Gespräch |
| N9 | Sensitivitätsanalyse / Best-Worst-Case | „Was wenn Inflation 3% statt 2%?" |
| N10 | GKV vs. PKV | Völlig andere KV-Logik im Alter |

---

## 📊 Gesamtbewertung

| Prio | ID | Thema | Aufwand |
|------|----|-------|---------|
| 🔴 | K1 | EkSt-Tarif veraltet | Mittel |
| 🔴 | K2 | SV-Konstanten nicht dynamisiert | Mittel |
| 🔴 | K3 | ATZ-Phase-String-Bug | **Trivial** |
| 🔴 | K4 | bAV-Besteuerung falsch | Gering |
| 🔴 | K5 | Ausgaben-Anpassung ATZ(P) | Gering |
| 🟠 | H1 | Keine Inflation | Mittel |
| 🟠 | H2 | Keine Rentenanpassung | Mittel |
| 🟠 | H3 | Kein Soli | Gering |
| 🟠 | H4 | Keine Kirchensteuer | Gering |
| 🟠 | H5 | Kein Ehegattensplitting | Mittel |
| 🟠 | H6 | SV-Rente vereinfacht | Hoch |
| 🟠 | H7 | Ertragsanteil pauschal | Gering |
| 🟠 | H8 | Abgeltungssteuer fehlt | Mittel |
| 🟡 | M1 | Keine `__init__.py` | Trivial |
| 🟡 | M2 | Keine `requirements.txt` | Trivial |
| 🟡 | M3 | Sidebar-Reihenfolge | Gering |
| 🟡 | M4 | Jahr hardcoded | Trivial |
| 🟡 | M5 | Default-Rentenbeginn | Trivial |
| 🟡 | M6 | Kumulative Vermögenskurve | Mittel |
| 🟡 | M7 | Keine Eingabevalidierung | Gering |
| 🟡 | M8 | NaN im Trend-Chart | Gering |
| 🟢 | N1–N10 | Vermögen, Szenarien, PDF... | Hoch |

---

> **Kernaussage:** Das Grundgerüst (Streamlit + Sankey + Trend) ist solide, die Modularisierung gut. Aber: kritischer Bug K3 (ATZ-Sankey funktioniert gar nicht), mehrere fachlich falsche Berechnungen (K1, K2, K4, H6, H7) und fehlende Kern-Features (Inflation, Splitting, Rentenabschläge). In der jetzigen Form wäre eine Nutzerin, die darauf basierend Entscheidungen trifft, **schlecht beraten**.
