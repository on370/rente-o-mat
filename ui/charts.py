import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_sankey(labels, sources, targets, values, title, show_vals=True):
    """
    Erstellt ein professionelles Sankey-Diagramm mit dynamischer Farbgebung.
    Unterstützt jetzt auch spezifische Knoten für Soli und KiSt.
    """
    display_labels = []
    node_colors = []
    
    for i, label in enumerate(labels):
        in_s = sum([values[j] for j, t in enumerate(targets) if t == i])
        out_s = sum([values[j] for j, s in enumerate(sources) if s == i])
        v = max(in_s, out_s)
        display_labels.append(f"{label} ({v:.0f}€)" if show_vals else label)
        
        # Dynamische Farben für Ergebnis-Knoten und Steuern
        if "Überschuss" in label:
            node_colors.append("#28B463") # Grün
        elif "Unterdeckung" in label or "Abschlag" in label or "Beitragsverlust" in label:
            node_colors.append("#CB4335") # Kräftiges Rot
        elif "Steuern" in label or "Soli" in label or "KiSt" in label or "Abgeltungsteuer" in label:
            node_colors.append("#E74C3C") # Etwas helleres Rot für Steuern
        elif "Sozialabgaben" in label:
            node_colors.append("#F39C12") # Orange für SV
        else:
            node_colors.append("#2E86C1") # Standard Blau

    link_colors = []
    for t in targets:
        if "Abschlag" in labels[t] or "Beitragsverlust" in labels[t]:
            link_colors.append("rgba(203, 67, 53, 0.6)") # Leicht transparentes Rot
        else:
            link_colors.append("#E5E7E9")

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20, 
            thickness=25, 
            line=dict(width=0), 
            label=display_labels, 
            color=node_colors
        ),
        link=dict(
            source=sources, 
            target=targets, 
            value=values, 
            color=link_colors
        )
    )])

    fig.update_layout(
        title_text=title, 
        font=dict(size=13, color="black", family="Arial"), 
        template="plotly_white", 
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        separators=",."
    )
    return fig

def create_trend_chart(df, meilensteine, show_tax_rate=False):
    """
    Erstellt ein gestapeltes Balkendiagramm für das Brutto-Einkommen (aufgeschlüsselt nach Quellen)
    und Linien für Bedarf, Netto-Einkommen sowie optional den Steuersatz.
    """
    # Subplots erstellen (zweite Y-Achse für Steuersatz)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 1. Gestapelte Balken für Einkommensquellen
    exclude_cols = ["Jahr", "Phase", "Brutto", "EkSt", "Soli", "KiSt", "Steuern", "Steuersatz", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit", "Rentenabschlag", "Beitragsverlust", "Steuerpflichtiger_Rentenanteil", "Netto-GRV", "Kapitalzuwachs_Sonder"]
    income_cols = [c for c in df.columns if c not in exclude_cols and not c.startswith("EXP_")]
    
    # Professionelle Farbpalette für Einkommensquellen (Türkis/Blau-Töne)
    color_sequence = ["#1ABC9C", "#2E86C1", "#17A589", "#2471A3", "#138D75", "#1F618D"]
    
    for i, col in enumerate(income_cols):
        fig.add_trace(
            go.Bar(
                x=df["Jahr"], y=df[col], name=col, 
                marker=dict(color=color_sequence[i % len(color_sequence)], line=dict(width=0))
            ),
            secondary_y=False
        )
        
    # Rentenabschlag & Beitragsverlust als schraffierte Balken on top darstellen (potenzielles Einkommen)
    if "Rentenabschlag" in df.columns and df["Rentenabschlag"].sum() > 0:
        fig.add_trace(
            go.Bar(
                x=df["Jahr"], y=df["Rentenabschlag"], name="Rentenabschlag (0,3%/Mon.)", 
                marker=dict(
                    color="rgba(203, 67, 53, 0.1)", 
                    line=dict(color="#CB4335", width=2),
                    pattern=dict(shape="/", fgcolor="#CB4335", fillmode="overlay")
                )
            ),
            secondary_y=False
        )
    
    if "Beitragsverlust" in df.columns and df["Beitragsverlust"].sum() > 0:
        fig.add_trace(
            go.Bar(
                x=df["Jahr"], y=df["Beitragsverlust"], name="Beitragsverlust (fehlende EP)", 
                marker=dict(
                    color="rgba(203, 67, 53, 0.05)", 
                    line=dict(color="#E74C3C", width=1),
                    pattern=dict(shape="x", fgcolor="#E74C3C", fillmode="overlay")
                )
            ),
            secondary_y=False
        )
    
    # 2. Linie für Bedarf
    fig.add_trace(
        go.Scatter(x=df["Jahr"], y=df["Bedarf"], name="Bedarf (Ausgaben)", line=dict(color='#CB4335', width=3)),
        secondary_y=False
    )

    # 3. Linie für Netto-Einkommen
    fig.add_trace(
        go.Scatter(x=df["Jahr"], y=df["Netto-Einkommen"], name="Netto-Einkommen", line=dict(color='#28B463', width=3, dash='dash')),
        secondary_y=False
    )
    
    # 4. Optionale Linie für Steuersatz
    if show_tax_rate:
        fig.add_trace(
            go.Scatter(x=df["Jahr"], y=df["Steuersatz"], name="Steuersatz (%)", line=dict(color='#8E44AD', width=2, dash='dot')),
            secondary_y=True
        )
    
    # Meilensteine hinzufügen
    for m in meilensteine:
        fig.add_vline(x=m["jahr"], line_width=2, line_dash="dash", line_color=m["color"])
        fig.add_annotation(
            x=m["jahr"], y=1.1, yref="paper",
            text=f"{m['label']}<br>{m['jahr']}",
            showarrow=False, font=dict(color=m["color"], size=10),
            bgcolor="white", opacity=0.9
        )

    # Layout-Optimierung
    fig.update_layout(
        template="plotly_white", 
        hovermode="x unified", 
        barmode='stack',
        bargap=0.15,
        margin=dict(t=100),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        separators=",."
    )
    
    fig.update_yaxes(title_text="Euro pro Monat", secondary_y=False)
    if show_tax_rate:
        fig.update_yaxes(title_text="Steuersatz (%)", secondary_y=True, range=[0, 50])
        
    return fig

def create_wealth_chart(df, startvermoegen=0.0, kapitalrendite=0.0):
    """
    Erstellt eine kumulative Kurve für die Vermögensentwicklung.
    Startet explizit beim Startvermögen am heutigen Tag.
    """
    jahre_raw = df["Jahr"].tolist()
    ueberschuesse = df["Überschuss/Defizit"].tolist()
    kapitalzuwaechse = df["Kapitalzuwachs_Sonder"].tolist() if "Kapitalzuwachs_Sonder" in df.columns else [0]*len(jahre_raw)
    
    # Wir fügen den echten Startpunkt (heute) hinzu
    jahre = [jahre_raw[0]]
    vermoegen = [startvermoegen]
    akt_vermoegen = startvermoegen
    
    for i, (u, kz) in enumerate(zip(ueberschuesse, kapitalzuwaechse)):
        # Rendite und Cashflow des Jahres berechnen
        # Wir nehmen an, der Cashflow fließt über das Jahr verteilt ein (vereinfacht: am Ende)
        akt_vermoegen = akt_vermoegen * (1 + kapitalrendite / 100)
        akt_vermoegen += u * 12
        akt_vermoegen += kz
        
        # Der berechnete Wert ist der Stand zum ENDE des Jahres i
        # Das ist gleichzeitig der Stand zum BEGINN des nächsten Jahres
        jahre.append(jahre_raw[i] + 1)
        vermoegen.append(akt_vermoegen)
        
    fig = go.Figure()
    
    # Fläche unter der Kurve
    fig.add_trace(
        go.Scatter(
            x=jahre, 
            y=vermoegen, 
            name="Vermögen",
            fill='tozeroy',
            line=dict(color='#2E86C1', width=3),
            fillcolor='rgba(46, 134, 193, 0.2)'
        )
    )
    
    # Rote Null-Linie
    fig.add_hline(y=0, line_width=2, line_color="#CB4335", line_dash="dash")
    
    fig.update_layout(
        title="Kumulative Vermögensentwicklung (inkl. Rendite & Cashflow)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(t=50, b=20, l=20, r=20),
        yaxis_title="Vermögen in Euro",
        xaxis_title="Jahr (Stand jeweils zum 01.01.)",
        separators=",."
    )
    
    return fig


def create_break_even_chart(df, be_alter):
    """
    Erstellt ein Liniendiagramm zum Vergleich der kumulierten Rentenzahlungen.
    """
    fig = go.Figure()
    
    # Szenario A (Früher)
    fig.add_trace(go.Scatter(
        x=df["Alter"], y=df["Kumuliert_A"], 
        name="Wunsch-Termin (Früher)", 
        line=dict(color='#2E86C1', width=3)
    ))
    
    # Szenario B (Später)
    fig.add_trace(go.Scatter(
        x=df["Alter"], y=df["Kumuliert_B"], 
        name="Regelaltersgrenze (Später)", 
        line=dict(color='#28B463', width=3)
    ))
    
    # Break-Even Marker
    if be_alter:
        fig.add_vline(x=be_alter, line_dash="dash", line_color="red")
        fig.add_annotation(
            x=be_alter, y=df[df["Alter"] == be_alter]["Kumuliert_A"].values[0],
            text=f"Break-Even mit {be_alter} Jahren",
            showarrow=True, arrowhead=1, ax=50, ay=30,
            bgcolor="white", bordercolor="red"
        )
    
    fig.update_layout(
        title="Vergleich kumulierter Netto-Rentenbezug",
        xaxis_title="Alter",
        yaxis_title="Summe ausgezahlter Renten (€)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        separators=",."
    )
    
    return fig
