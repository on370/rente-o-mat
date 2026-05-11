# Konzept: Vermögenswerte & Befristete Ausgaben (Phase 4)

> Zielgruppe dieses Dokuments: Coding Agent zur Implementierung.  
> Erstellt: 2026-05-08 | Build-Basis: 0044

---

## 1. Motivation & Abgrenzung

Aktuell hat der Rente-O-Mat zwei fundamentale Lücken:

1. **Vermögenswerte existieren nur als Zahl.** Es gibt ein `startvermoegen` und eine `kapitalrendite`, aber keine individuellen Assets. Der "Entnahmeplan (Vermögen)" als Einnahmetyp bucht Geld ins Budget, ohne ein Asset zu reduzieren ("Geld aus dem Nichts" – Audit W2).

2. **Ausgaben sind unbefristet.** Jede Ausgabe läuft von heute bis zum Tod. Realität: Kredite enden, Unterhalt endet, Kinder werden erwachsen (Audit W3).

Beide Features teilen sich ein UI-Pattern (Listen mit Start/Ende-Datum) und haben steuerliche Implikationen. Daher werden sie gemeinsam konzipiert.

---

## 2. Datenmodell

### 2.1 Vermögenswert (Asset)

```python
asset = {
    "id": "uuid4",           # Eindeutige ID
    "name": "Welt-ETF",      # Anzeigename
    "startwert": 50000.0,    # Kapital bei Simulationsstart (€)
    "rendite_pa": 5.0,       # Erwartete Rendite (% p.a.)
    "steuertyp": "abgeltung", # "abgeltung" | "steuerfrei" | "teilfreistellung"
    "teilfreistellung_pct": 30.0,  # Nur bei steuertyp="teilfreistellung" (Aktienfonds: 30%)
    "entnahme": {             # Optional: Verknüpfter Entnahmeplan
        "betrag_mtl": 500.0,  # Monatliche Entnahme (€)
        "start": 2032,        # Ab wann
        "ende": 2050,         # Bis wann (oder "erschoepfung")
        "modus": "fest"       # "fest" | "prozent" | "restlaufzeit"
    }
}
```

**Steuertypen erklärt:**
- `abgeltung`: 25% KapESt + Soli auf Gewinne, nach Sparerpauschbetrag (1.000€ Single). Standard für Depot/Tagesgeld.
- `steuerfrei`: Keine Steuer auf Entnahmen (z.B. bereits versteuertes Kapital, Immobilienverkauf nach 10 Jahren).
- `teilfreistellung`: Aktienfonds-ETF: 30% der Erträge sind steuerfrei (§ 20 Abs. 1 InvStG). Effektiver Steuersatz: 25% × 70% = 17,5%.

### 2.2 Befristete Ausgabe

```python
ausgabe_befristet = {
    "id": "uuid4",
    "name": "Immobilienkredit",
    "betrag_mtl": 1200.0,     # Monatliche Rate (€)
    "start": 2020,            # Läuft seit (für Anzeige)
    "ende": 2035,             # Endet in diesem Jahr
    "kategorie": "Wohnen",    # Zuordnung zur bestehenden Ausgabenkategorie
    "inflationsgebunden": False  # Kredit steigt nicht mit Inflation
}
```

**Wichtig:** Befristete Ausgaben sind ein **Subset** der bestehenden Ausgaben, kein Aufschlag. Wenn der Nutzer 1.200€ Wohnen eingibt und davon 800€ ein Kredit bis 2035 ist, dann sinken die Wohnkosten ab 2036 auf 400€ (+ Inflation auf den Restbetrag).

---

## 3. Engine-Integration

### 3.1 Vermögens-Simulation (Closed-Loop)

Die Engine muss pro Jahr folgende Schritte für jedes Asset ausführen:

```
Für jedes Asset a in assets:
    1. Rendite berechnen:
       gewinn = a.kapital * (a.rendite_pa / 100)
    
    2. Steuer auf Gewinn:
       if a.steuertyp == "abgeltung":
           steuerpflichtig = gewinn - anteiliger_sparerpauschbetrag
           steuer = berechne_abgeltungsteuer(steuerpflichtig)
       elif a.steuertyp == "teilfreistellung":
           steuerpflichtig = gewinn * (1 - a.teilfreistellung_pct/100) - anteil_sparerpb
           steuer = berechne_abgeltungsteuer(steuerpflichtig)
       else:
           steuer = 0
       
       a.kapital += gewinn - steuer
    
    3. Entnahme (falls aktiv in diesem Jahr):
       if a.entnahme and start <= jahr <= ende:
           entnahme_jahr = a.entnahme.betrag_mtl * 12
           tatsaechlich = min(entnahme_jahr, a.kapital)
           a.kapital -= tatsaechlich
           → tatsaechlich/12 fließt als Einnahme ins Budget (steuerfrei, da Kapitalrückzahlung)
    
    4. Überschuss-Reinvestition (optional, Phase 5):
       if gesamtueberschuss > 0 and a.ist_ziel_fuer_reinvestition:
           a.kapital += gesamtueberschuss * 12
```

**Entscheidung: Entnahmen sind steuerfrei im Einnahme-Fluss.** Begründung: Die Steuer wurde bereits auf den Gewinn des Assets berechnet (Schritt 2). Die Entnahme selbst ist eine Kapitalrückzahlung und kein steuerpflichtiges Einkommen. (Anders als bei einer Versicherungsrente mit Ertragsanteil.)

### 3.2 Befristete Ausgaben

Die Engine-Logik für Ausgaben (`engine.py` Z.269–277) muss erweitert werden:

```python
# Bestehende Logik (bleibt):
for k in params.get('ausgaben_kategorien', []):
    basis_ausgabe = params.get('ausgaben_input', {}).get(k, 0.0)
    infl_ausgabe = _dynamisiere_betrag(basis_ausgabe, aktuelles_jahr, jahr, inflation_rate)
    
    # NEU: Befristete Ausgaben abziehen, wenn sie ausgelaufen sind
    for ba in params.get('befristete_ausgaben', []):
        if ba['kategorie'] == k and jahr > ba['ende']:
            infl_ausgabe -= ba['betrag_mtl']  # Ohne Inflation, da z.B. Kreditrate fix
            infl_ausgabe = max(0, infl_ausgabe)  # Nie negativ
    
    if phase == "Rente":
        infl_ausgabe *= (params.get('anpassungsfaktor_input', {}).get(k, 100) / 100)
```

---

## 4. UI-Design

### 4.1 Sidebar: Neuer Expander "💎 Vermögenswerte"

Platzierung: Nach "💰 Einnahmequellen", vor "🏠 Haushaltsbuch".

**Listenansicht:** Wie bei Einnahmen – jedes Asset als kompakte Zeile mit Name, Wert, Edit/Delete-Buttons.

**Formular (Add/Edit):**
```
Name:           [Welt-ETF Depot          ]
Startwert (€):  [50.000                  ]
Rendite (% p.a.): [──●──────] 5.0%
Steuertyp:      [Abgeltungsteuer ▼]

☐ Entnahmeplan aktivieren
  Entnahme (€/mtl.): [500  ]
  Von Jahr:           [2032 ]
  Bis Jahr:           [2050 ]
```

### 4.2 Sidebar: Neuer Expander "⏱️ Befristete Ausgaben"

Platzierung: Direkt nach "🏠 Haushaltsbuch".

**Listenansicht:** Kompakte Zeilen mit Name, Betrag, Endjahr.

**Formular (Add/Edit):**
```
Name:           [Immobilienkredit        ]
Betrag (€/mtl.): [1.200                 ]
Endet im Jahr:  [2035                   ]
Kategorie:      [Wohnen ▼]
☐ Steigt mit Inflation
```

### 4.3 Tab 3: Vermögensentwicklung (Upgrade)

Aktuell zeigt Tab 3 eine einzelne Linie. Nach dem Umbau:
- **Stacked Area Chart** mit einer Fläche pro Asset.
- Sichtbares "Abschmelzen" einzelner Assets bei laufender Entnahme.
- Markierung des Zeitpunkts, an dem ein Asset erschöpft ist.

### 4.4 Sankey-Integration

Im Simulations-Sankey (Tab 1):
- Entnahmen aus Assets erscheinen als eigene Einnahme-Knoten: `"Entnahme: Welt-ETF"` → `"Brutto"` (bzw. direkt → `"Netto-Einkommen"`, da steuerfrei).
- Befristete Ausgaben, die in einem Jahr noch laufen, sind im Ausgaben-Teil sichtbar. Nach Ablauf verschwinden sie.

---

## 5. Persistenz (Export/Import)

Das JSON-Format muss erweitert werden:

```json
{
  "version": 3,
  "assets": [
    {"name": "Welt-ETF", "startwert": 50000, "rendite_pa": 5.0, ...}
  ],
  "befristete_ausgaben": [
    {"name": "Immobilienkredit", "betrag_mtl": 1200, "ende": 2035, ...}
  ],
  ...bestehende Felder...
}
```

Rückwärtskompatibilität: Import von v2-Dateien muss weiterhin funktionieren (leere Arrays als Default).

---

## 6. Implementierungsreihenfolge

### Phase A: Datenmodell & Engine (kein UI)
1. `logic/engine.py`: Asset-Simulation in `calculate_financials_for_year()` einbauen
2. `logic/engine.py`: Befristete Ausgaben in der Ausgaben-Schleife berücksichtigen
3. `data/persistence.py`: Export/Import für v3-Format erweitern

### Phase B: Sidebar-UI
4. `ui/sidebar.py`: Expander "💎 Vermögenswerte" mit CRUD-Formular
5. `ui/sidebar.py`: Expander "⏱️ Befristete Ausgaben" mit CRUD-Formular
6. Rückgabe-Dictionary `p` um `assets` und `befristete_ausgaben` erweitern

### Phase C: Visualisierung
7. `ui/charts.py`: `create_wealth_chart()` auf Stacked Area umstellen
8. `app.py`: Sankey-Logik um Asset-Entnahmen erweitern
9. `app.py`: Tab 3 mit neuen Asset-Daten versorgen

### Phase D: Polish & Verifikation
10. Verifikation: Bilanzprüfung (Entnahme reduziert Asset, erhöht Budget)
11. Build-ID inkrementieren, TODO.md aktualisieren

---

## 7. Steuerrechtliche Sonderfälle (Referenz)

| Szenario | Steuer auf Gewinn | Steuer auf Entnahme |
|----------|-------------------|---------------------|
| ETF-Depot (Aktienfonds) | 25% KapESt auf 70% des Gewinns (30% TFS) | Keine (Kapitalrückzahlung) |
| Tagesgeld/Festgeld | 25% KapESt auf vollen Gewinn | Keine |
| Immobilienverkauf (<10 J.) | Privates Veräußerungsgeschäft (persönl. Steuersatz) | N/A |
| Immobilienverkauf (>10 J.) | Steuerfrei | Keine |
| bAV-Einmalzahlung | Fünftelregelung (bereits implementiert) | SV über 120 Monate (bereits implementiert) |
| Riester/Rürup | Nachgelagerte Besteuerung | Voller persönlicher Steuersatz |

> [!NOTE]
> **Für v1 dieses Features** implementieren wir nur die drei Steuertypen `abgeltung`, `teilfreistellung` und `steuerfrei`. Riester/Rürup wird als separates Feature in einer späteren Phase behandelt.

---

## 8. Abgrenzung: Was wird NICHT implementiert

- **Reinvestition von Überschüssen** → Phase 5
- **Riester/Rürup-Verträge** → Eigenes Feature (nachgelagerte Besteuerung)
- **Immobilien als Asset** → Zu komplex (Mieteinnahmen, Abschreibung, Nebenkosten)
- **Mehrere Währungen** → Nicht relevant für Zielgruppe
- **FIFO-Berechnung für Teilverkäufe** → Zu granular, wir nehmen Durchschnittsbesteuerung an
