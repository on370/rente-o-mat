import plotly.graph_objects as go

def create_sankey(labels, sources, targets, values, title, show_vals=True):
    """
    Erstellt ein professionelles Sankey-Diagramm mit dynamischer Farbgebung.
    """
    display_labels = []
    node_colors = []
    
    for i, label in enumerate(labels):
        in_s = sum([values[j] for j, t in enumerate(targets) if t == i])
        out_s = sum([values[j] for j, s in enumerate(sources) if s == i])
        v = max(in_s, out_s)
        display_labels.append(f"{label} ({v:.0f}€)" if show_vals else label)
        
        # Dynamische Farben für Ergebnis-Knoten
        if "Überschuss" in label:
            node_colors.append("#28B463") # Grün
        elif "Unterdeckung" in label:
            node_colors.append("#CB4335") # Rot
        else:
            node_colors.append("#2E86C1") # Standard Blau

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
            color="#E5E7E9"
        )
    )])

    fig.update_layout(
        title_text=title, 
        font=dict(size=13, color="black", family="Arial"), 
        template="plotly_white", 
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_trend_chart(df, meilensteine):
    """
    Erstellt das gestapelte Flächendiagramm für den langfristigen Trend.
    """
    fig = go.Figure()
    
    # Einkommen & Bedarf
    fig.add_trace(go.Scatter(
        x=df["Jahr"], y=df["Netto-Einkommen"], 
        name="Netto-Einkommen", fill='tozeroy', 
        line=dict(color='#2E86C1')
    ))
    fig.add_trace(go.Scatter(
        x=df["Jahr"], y=df["Bedarf"], 
        name="Bedarf", 
        line=dict(color='#CB4335', width=3)
    ))
    
    # Meilensteine hinzufügen
    for m in meilensteine:
        fig.add_vline(x=m["jahr"], line_width=2, line_dash="dash", line_color=m["color"])
        fig.add_annotation(
            x=m["jahr"], y=1.05, yref="paper",
            text=f"{m['label']}<br>({m['jahr']})",
            showarrow=False, font=dict(color=m["color"], size=10),
            bgcolor="white", opacity=0.8
        )

    fig.update_layout(
        template="plotly_white", 
        hovermode="x unified", 
        yaxis_title="€ / Monat",
        margin=dict(t=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
