import streamlit as st
from logic.engine import calculate_financials_for_year, generate_trend_data
from ui.sidebar import render_sidebar
from ui.charts import create_sankey, create_trend_chart, create_wealth_chart

st.set_page_config(page_title="Rente-O-Mat PRO", layout="wide")
st.title("🛡️ Rente-O-Mat: Präzisions-Planer")

# --- SIDEBAR & PARAMETER ---
p = render_sidebar()

# --- HAUPTBEREICH (TABS) ---
tab1, tab2, tab3 = st.tabs(["📊 Sankey-Analyse", "📈 Zeitliche Entwicklung", "💰 Vermögensentwicklung"])

# --- TAB 1: SANKEY ---
with tab1:
    # 1. Status Quo Analyse
    st.subheader("1. Status Quo (Aktivphase)")
    sq_labels, sq_sources, sq_targets, sq_values = [], [], [], []
    
    def add_sq(s, t, v):
        if v > 0.1:
            if s not in sq_labels: sq_labels.append(s)
            if t not in sq_labels: sq_labels.append(t)
            sq_sources.append(sq_labels.index(s))
            sq_targets.append(sq_labels.index(t))
            sq_values.append(v)
    
    a_sq_sum = sum(p['ausgaben_input'].values())
    d_sq = p['aktuelles_netto'] - a_sq_sum
    add_sq("Aktuelles Netto", "Haushalts-Budget", p['aktuelles_netto'])
    if d_sq > 0: add_sq("Haushalts-Budget", "Liquiditäts-Überschuss", d_sq)
    elif d_sq < 0: add_sq("Liquiditäts-Unterdeckung", "Haushalts-Budget", abs(d_sq))
    for k, v in p['ausgaben_input'].items(): add_sq("Haushalts-Budget", k, v)
    st.plotly_chart(create_sankey(sq_labels, sq_sources, sq_targets, sq_values, "Aktueller Cashflow", p['show_values']), use_container_width=True)

    # 2. Simulations-Analyse
    res = calculate_financials_for_year(p['betrachtungsjahr'], p)
    st.divider()
    
    # KENNZAHLEN DASHBOARD
    st.subheader(f"2. Simulation: {res['Phase']} ({p['betrachtungsjahr']})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Brutto", f"{res['Brutto']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Netto", f"{res['Netto-Einkommen']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Steuerlast", f"{res['Steuersatz']:.1f} %")
    
    ueberschuss = res['Überschuss/Defizit']
    ueberschuss_color = "normal" if ueberschuss >= 0 else "inverse"
    col4.metric("Überschuss", f"{ueberschuss:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"{ueberschuss:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), delta_color=ueberschuss_color)
    
    # SANKEY AUFBAU
    l_r, s_r, t_r, v_r = [], [], [], []
    def add_r(s, t, v):
        if v > 0.1:
            if s not in l_r: l_r.append(s)
            if t not in l_r: l_r.append(t)
            s_r.append(l_r.index(s))
            t_r.append(l_r.index(t))
            v_r.append(v)

    # Brutto-Aufschlüsselung
    if res['Phase'] == "Aktiv":
        add_r("Arbeitseinkommen", "Brutto", p['aktuelles_brutto'])
    elif res['Phase'] in ["ATZ(A)", "ATZ(P)"]: # K3 Fix: ATZ richtig abfragen
        h_br = p['aktuelles_brutto'] / 2
        auf = h_br * (p['atz_aufstockung_pct'] / 100)
        add_r("ATZ-Gehalt", "Brutto", h_br)
        add_r("AG-Aufstockung", "Brutto", auf)
    else: # Rente
        # Einnahmen dynamisiert aus res holen
        for e in p['einnahmen']:
            if p['betrachtungsjahr'] >= e["start"] and p['betrachtungsjahr'] <= e["ende"]:
                val = res.get(e["name"], e["betrag"]) # Dynamisierten Wert falls vorhanden
                add_r(e["name"], "Brutto", val)

    # Abzüge aufschlüsseln
    if res['EkSt'] > 0:
        add_r("Brutto", "Einkommensteuer", res['EkSt'])
    if res['Soli'] > 0:
        add_r("Brutto", "Soli", res['Soli'])
    if res['KiSt'] > 0:
        add_r("Brutto", "Kirchensteuer", res['KiSt'])
    
    # Kapitalerträge haben separate Abgeltungsteuer (in Steuern gesamt enthalten, aber hier als EkSt vereinfacht abgebildet)
    # Wenn wir es präzise machen wollen, könnten wir "Abgeltungsteuer" hinzufügen, aber die Engine berechnet es schon ein.
    # Da steuer_ekst in Engine.py um steuer_kapital erhöht wurde, ist es in Einkommensteuer enthalten.
    
    add_r("Brutto", "Sozialabgaben", res['Sozialabgaben'])
    add_r("Brutto", "Verfügbares Budget", res['Netto-Einkommen'])

    # Ausgaben und Überschuss
    if res['Überschuss/Defizit'] > 0:
        add_r("Verfügbares Budget", "Liquiditäts-Überschuss", res['Überschuss/Defizit'])
    elif res['Überschuss/Defizit'] < 0:
        add_r("Liquiditäts-Unterdeckung", "Verfügbares Budget", abs(res['Überschuss/Defizit']))

    # Einzelne Ausgaben (aus res['Bedarf'] berechnet in Engine, wir müssen sie hier analog inflationieren)
    for k in p['ausgaben_kategorien']:
        # Der genaue Betrag pro Kategorie wurde in engine.py berechnet, wir replizieren ihn hier für's Sankey
        basis_ausgabe = p['ausgaben_input'][k]
        jahr = p['betrachtungsjahr']
        jahre = jahr - p['aktuelles_jahr']
        if jahre > 0 and p['inflation_rate'] > 0:
            inflationierte_ausgabe = basis_ausgabe * (1 + p['inflation_rate'] / 100) ** jahre
        else:
            inflationierte_ausgabe = basis_ausgabe
            
        if res['Phase'] == "Rente":
            inflationierte_ausgabe *= (p['anpassungsfaktor_input'][k] / 100)
            
        add_r("Verfügbares Budget", k, inflationierte_ausgabe)
        
    st.plotly_chart(create_sankey(l_r, s_r, t_r, v_r, f"Cashflow Simulation {p['betrachtungsjahr']}", p['show_values']), use_container_width=True)

# --- TAB 2: TREND ---
with tab2:
    st.subheader("Finanzielle Entwicklung bis Alter 95")
    show_tax_rate = st.checkbox("Effektiven Steuersatz anzeigen (%)", value=False)
    
    jahre = list(range(p['aktuelles_jahr'], p['geburtsjahr'] + 96))
    df_trend = generate_trend_data(jahre, p)
    
    # Meilensteine vorbereiten
    meilensteine = []
    if p['atz_simulieren']:
        atz_mitte = p['atz_start'] + (p['atz_dauer'] / 2)
        meilensteine.append({"jahr": p['atz_start'], "label": "ATZ(A)", "color": "#F39C12"})
        meilensteine.append({"jahr": atz_mitte, "label": "ATZ(P)", "color": "#F1C40F"})
    
    meilensteine.append({"jahr": p['rentenbeginn'], "label": "Rentenbeginn", "color": "#28B463"})
    for e in p['einnahmen']:
        if e["start"] > p['aktuelles_jahr'] and e["start"] != p['rentenbeginn']:
            meilensteine.append({"jahr": e["start"], "label": f"Start: {e['name']}", "color": "#8E44AD"})

    st.plotly_chart(create_trend_chart(df_trend, meilensteine, show_tax_rate=show_tax_rate), use_container_width=True)
    
    with st.expander("Datentabelle anzeigen"):
        st.dataframe(df_trend.style.format("{:.2f}€", subset=["Brutto", "Steuern", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit"]).format("{:.1f}%", subset=["Steuersatz"]), use_container_width=True)

# --- TAB 3: VERMÖGEN ---
with tab3:
    st.subheader("Kumulative Vermögensentwicklung")
    st.info(f"Startvermögen: **{p['startvermoegen']:,.2f} €** | Angenommene Kapitalrendite: **{p['kapitalrendite']:.1f} % p.a.**".replace(",", "X").replace(".", ",").replace("X", "."))
    
    # df_trend haben wir schon im tab2 generiert, aber falls tab2 nicht gerendert wurde, 
    # generieren wir es sicherheitshalber nochmal wenn es nicht existiert
    if 'df_trend' not in locals():
        jahre = list(range(p['aktuelles_jahr'], p['geburtsjahr'] + 96))
        df_trend = generate_trend_data(jahre, p)
        
    st.plotly_chart(create_wealth_chart(df_trend, p['startvermoegen'], p['kapitalrendite']), use_container_width=True)
