import streamlit as st
from ui.sidebar import render_sidebar
from ui.charts import create_sankey, create_trend_chart, create_wealth_chart, create_break_even_chart
from logic.engine import calculate_financials_for_year, generate_trend_data, calculate_break_even_data
from config import FULL_VERSION, DATENSCHUTZ_INFO

st.set_page_config(page_title="Rente-O-Mat PRO", layout="wide")

# --- WELCOME DIALOG & DISCLAIMER ---
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False

if not st.session_state.disclaimer_accepted:
    st.title("🛡️ Willkommen beim Rente-O-Mat")
    st.subheader(f"Version {FULL_VERSION}")
    st.warning("""
    **DISCLAIMER:** Achtung, der Renten-Planer ist noch in der Entwicklung und kann fehlerhaft oder unvollständig sein. 
    Alle Angaben müssen durch den/die Nutzer:in überprüft werden. Benutzung auf eigenes Risiko.
    """)
    st.info(DATENSCHUTZ_INFO)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ Einverstanden", width='stretch'):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

st.title("🛡️ Rente-O-Mat: Der Renten-Planer")
st.caption(FULL_VERSION)

# --- SIDEBAR & PARAMETER ---
p = render_sidebar()

# --- DATEN-GENERIERUNG (Zentral für alle Tabs) ---
jahre_liste = list(range(p['aktuelles_jahr'], p['geburtsjahr'] + 96))
df_timeline = generate_trend_data(jahre_liste, p)

# --- HAUPTBEREICH (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Sankey-Analyse", "📈 Zeitliche Entwicklung", "💰 Vermögensentwicklung", "⚖️ Strategie-Check"])

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
    st.plotly_chart(create_sankey(sq_labels, sq_sources, sq_targets, sq_values, "Aktueller Cashflow", p['show_values']), width='stretch')

    # 2. Simulations-Analyse
    st.subheader(f"2. Simulation (Jahr {p['betrachtungsjahr']})")
    # K2 Fix: Wir nehmen die Zeile aus dem zentralen DataFrame für dieses Jahr
    res = df_timeline[df_timeline["Jahr"] == p['betrachtungsjahr']].iloc[0].to_dict()
    
    # KENNZAHLEN DASHBOARD
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Brutto", f"{res['Brutto']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Netto", f"{res['Netto-Einkommen']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), 
                help="Das Netto wird auf Basis des zu versteuernden Einkommens (zvE) berechnet. Dabei werden Vorsorgeaufwendungen (SV-Beiträge) und Pauschbeträge (Werbungskosten 1.230€) automatisch abgezogen. Individuelle Freibeträge sind nicht berücksichtigt.")
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
    for e in p['einnahmen']:
        if res['Jahr'] >= e.get("start", 0) and res['Jahr'] <= e.get("ende", 9999):
            val = res.get(e["name"], 0.0)
            if val > 0:
                add_r(e["name"], "Brutto", val)
    
    # Falls wir in der Aktivphase sind und kein Gehalt in den Einnahmen steht (sondern über p['aktuelles_brutto'])
    if res['Phase'] == "Aktiv" and "Gehalt" in res:
         add_r("Arbeitseinkommen", "Brutto", res["Gehalt"])
    elif res['Phase'] in ["ATZ(A)", "ATZ(P)"]:
         if "Gehalt (ATZ)" in res: add_r("ATZ-Gehalt", "Brutto", res["Gehalt (ATZ)"])
         if "Aufstockung" in res: add_r("AG-Aufstockung", "Brutto", res["Aufstockung"])

    # Abzüge aufschlüsseln
    if res.get('Beitragsverlust', 0) > 0:
        add_r("Brutto", "Beitragsverlust", res['Beitragsverlust'])
    if res.get('Rentenabschlag', 0) > 0:
        add_r("Brutto", "Rentenabschlag", res['Rentenabschlag'])
    if res['EkSt'] > 0:
        add_r("Brutto", "Einkommensteuer", res['EkSt'])
    if res['Soli'] > 0:
        add_r("Brutto", "Soli", res['Soli'])
    if res['KiSt'] > 0:
        add_r("Brutto", "Kirchensteuer", res['KiSt'])
    
    add_r("Brutto", "Netto-Einkommen", res['Netto-Einkommen'])
    add_r("Netto-Einkommen", "Verfügbares Budget", res['Netto-Einkommen'])
    
    if res['Überschuss/Defizit'] > 0:
        add_r("Verfügbares Budget", "Liquiditäts-Überschuss", res['Überschuss/Defizit'])
    elif res['Überschuss/Defizit'] < 0:
        add_r("Liquiditäts-Unterdeckung", "Verfügbares Budget", abs(res['Überschuss/Defizit']))

    # Einzelne Ausgaben (aus res['EXP_...'] direkt aus der Engine)
    for k in p['ausgaben_kategorien']:
        val = res.get(f"EXP_{k}", 0.0)
        if val > 0:
            add_r("Verfügbares Budget", k, val)
        
    st.plotly_chart(create_sankey(l_r, s_r, t_r, v_r, f"Cashflow Simulation {p['betrachtungsjahr']}", p['show_values']), width='stretch')

# --- TAB 2: TREND ---
with tab2:
    st.subheader("Finanzielle Entwicklung bis Alter 95")
    show_tax_rate = st.checkbox("Effektiven Steuersatz anzeigen (%)", value=False)
    
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

    st.plotly_chart(create_trend_chart(df_timeline, meilensteine, show_tax_rate=show_tax_rate), width='stretch')
    
    with st.expander("Datentabelle anzeigen"):
        st.dataframe(df_timeline.style.format("{:.2f}€", subset=["Brutto", "Steuern", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit"]).format("{:.1f}%", subset=["Steuersatz"]), width='stretch')

# --- TAB 3: VERMÖGEN ---
with tab3:
    st.subheader("Kumulative Vermögensentwicklung")
    st.info(f"Startvermögen: **{p['startvermoegen']:,.2f} €** | Angenommene Kapitalrendite: **{p['kapitalrendite']:.1f} % p.a.**".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.plotly_chart(create_wealth_chart(df_timeline, p['startvermoegen'], p['kapitalrendite']), width='stretch')

# --- TAB 4: STRATEGIE ---
with tab4:
    st.subheader("Wann lohnt sich der spätere Renteneintritt?")
    st.info("""
    Diese Analyse vergleicht deinen gewählten Rentenbeginn mit dem gesetzlichen Regelrenteneintritt. 
    Dargestellt wird die Summe der bis zum jeweiligen Alter ausgezahlten Netto-Rentenbeträge (gesetzliche Rente).
    """)
    
    
    try:
        df_be, be_jahr, be_alter = calculate_break_even_data(p)
        
        if be_jahr:
            col1, col2 = st.columns(2)
            col1.metric("Break-Even Alter", f"{be_alter} Jahre")
            col2.metric("Break-Even Jahr", f"{be_jahr}")
            
            st.success(f"Ab dem Jahr **{be_jahr}** (Alter **{be_alter}**) hast du durch die höhere monatliche Regelrente insgesamt mehr Geld erhalten als durch den früheren, aber geringeren Rentenbezug.")
        else:
            st.warning("Kein Break-Even-Punkt innerhalb der Simulation (bis Alter 100) gefunden. Ein früherer Eintritt scheint in diesem Szenario langfristig vorteilhafter oder der Unterschied ist zu gering.")

        st.plotly_chart(create_break_even_chart(df_be, be_alter), width='stretch')
    except Exception as e:
        st.error(f"Fehler bei der Strategie-Berechnung: {e}")
        st.info("Dies kann an fehlenden Daten in einer importierten Datei liegen. Bitte prüfe deine Eingaben in der Sidebar.")

# --- FOOTER & DISCLAIMER ---
st.divider()
st.caption(f"{FULL_VERSION} | **DISCLAIMER:** Achtung, der Renten-Planer ist noch in der Entwicklung und kann fehlerhaft oder unvollständig sein. Alle Angaben müssen durch den/die Nutzer:in überprüft werden. Benutzung auf eigenes Risiko.")
