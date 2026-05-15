from fpdf import FPDF
import pandas as pd
import datetime

def _L1(text):
    """Konvertiert Text in latin-1 für FPDF Standard-Fonts."""
    return text.encode('latin-1', 'replace').decode('latin-1')

class BriefingPDF(FPDF):
    def __init__(self, nutzer_name=""):
        super().__init__()
        self.nutzer_name = nutzer_name

    def header(self):
        # Dokument-Überschrift (Deutlich größer)
        self.set_font('helvetica', 'B', 18)
        self.set_text_color(41, 128, 185) # Blau
        
        titel = f"Rente-O-Mat | Persönliches Briefing für {self.nutzer_name}"
        self.cell(0, 10, _L1(titel), border=False, align='L')
        self.ln(15)

    def footer(self):
        # Seitennummerierung unten
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        
        # Generierungsdatum
        date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        self.cell(0, 10, _L1(f'Generiert am {date_str} | Seite {self.page_no()}/{{nb}}'), align='C')


import io

def create_briefing_pdf(params, df_timeline, chart_images=None):
    """
    Erstellt ein PDF-Dokument basierend auf den Simulationsdaten.
    chart_images: Dict mit PNG-Bytes { "sankey_aktiv": bytes, "sankey_rente": bytes, "trend_assets": bytes, ... }
    """
    name = params.get('nutzer_name', 'Nutzer')
    pdf = BriefingPDF(nutzer_name=name)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Farben & Schriften definieren
    pdf.set_draw_color(200, 200, 200)
    pdf.set_fill_color(245, 245, 245)
    
    # Disclaimer
    pdf.set_font("helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    disclaimer = "DISCLAIMER: Achtung, der Renten-Planer ist noch in der Entwicklung und kann fehlerhaft oder unvollständig sein. Alle Angaben müssen durch den/die Nutzer:in überprüft werden. Benutzung auf eigenes Risiko."
    pdf.multi_cell(0, 4, _L1(disclaimer))
    pdf.ln(5)

    # Relevante Daten extrahieren
    renten_jahre = df_timeline[df_timeline["Phase"] == "Rente"]
    erstes_rentenjahr = renten_jahre.iloc[0] if not renten_jahre.empty else None
    
    renten_jahr = int(params['rentenbeginn'])
    renten_alter = renten_jahr - params['geburtsjahr']
    
    letztes_jahr = df_timeline.iloc[-1]
    end_vermoegen = letztes_jahr.get("ASSET_VAL_Cash-Reserven (kum.)", 0)
    for col in df_timeline.columns:
        if col.startswith("ASSET_VAL_") and col != "ASSET_VAL_Cash-Reserven (kum.)":
            end_vermoegen += letztes_jahr.get(col, 0)
    
    # 1. Zusammenfassung (Etwas kleiner für Hierarchie)
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("1. Zusammenfassung"), ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(0, 8, _L1(f"Gewählter Rentenbeginn: {renten_jahr} (Alter {renten_alter} Jahre)"), ln=True)
    pdf.cell(0, 8, _L1(f"Projiziertes Endvermögen (Alter 95): {end_vermoegen:,.0f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    
    if erstes_rentenjahr is not None:
        rentenlücke = erstes_rentenjahr["Bedarf"] - erstes_rentenjahr["Netto-Einkommen"]
        abschlag_eur = erstes_rentenjahr.get("Rentenabschlag", 0) * 12
        bedarf_summe = renten_jahre['Bedarf'].sum() * 12
        
        pdf.cell(0, 8, _L1(f"Finanzlücke 1. Rentenjahr: {rentenlücke:,.0f} Euro monatlich").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 8, _L1(f"Kumulierter Gesamtbedarf (Ruhestand): {bedarf_summe:,.0f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 8, _L1(f"Rentenabschlag: ca. {abschlag_eur:,.0f} Euro / Jahr").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    
    pdf.ln(5)
    
    # 2. Status Quo
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("2. Status Quo (Aktivphase)"), ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    a_sq_sum = sum(params['ausgaben_input'].values())
    d_sq = params['aktuelles_netto'] - a_sq_sum
    
    pdf.cell(0, 8, _L1(f"Monatliches Nettoeinkommen: {params['aktuelles_netto']:,.2f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    pdf.cell(0, 8, _L1(f"Monatliche Ausgaben: {a_sq_sum:,.2f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    
    # Sankey Aktivbild
    if chart_images and "sankey_aktiv" in chart_images:
        img_data = io.BytesIO(chart_images["sankey_aktiv"])
        pdf.image(img_data, x=10, y=pdf.get_y() + 2, w=180)
        pdf.set_y(pdf.get_y() + 95) # Platz für das Bild lassen (Annahme: w=180 -> h~90)
    
    pdf.ln(10)

    # 3. Deep Dive
    pdf.add_page()
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("3. Deep Dive: Erstes volles Rentenjahr"), ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    
    if erstes_rentenjahr is not None:
        j = int(erstes_rentenjahr['Jahr'])
        b = erstes_rentenjahr['Brutto']
        sv = erstes_rentenjahr['Sozialabgaben']
        n = erstes_rentenjahr['Netto-Einkommen']
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, _L1(f"Berechnungsjahr: {j}"), ln=True)
        pdf.set_font("helvetica", "", 11)
        
        pdf.cell(0, 8, _L1(f"Netto-Einkommen: {n:,.2f} Euro (Brutto: {b:,.2f} Euro)").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 8, _L1(f"Abzug Sozialversicherung (KV/PV): - {sv:,.2f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        
        # Sankey Rentenbild
        if chart_images and "sankey_rente" in chart_images:
            img_data = io.BytesIO(chart_images["sankey_rente"])
            pdf.image(img_data, x=10, y=pdf.get_y() + 2, w=180)
            pdf.set_y(pdf.get_y() + 95)
            
    pdf.ln(10)

    # 4. Zeitliche Entwicklung (Trends)
    if chart_images and ("trend_assets" in chart_images or "trend_income" in chart_images):
        pdf.add_page()
        pdf.set_font("helvetica", "B", 13)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 10, _L1("4. Zeitliche Entwicklung (Trends)"), ln=True)
        
        if "trend_assets" in chart_images:
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, _L1("Vermoegensentwicklung"), ln=True)
            img_data = io.BytesIO(chart_images["trend_assets"])
            pdf.image(img_data, x=10, y=pdf.get_y(), w=180)
            pdf.set_y(pdf.get_y() + 100)
            
        if "trend_income" in chart_images:
            pdf.ln(5)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 8, _L1("Einnahmen und Ausgaben"), ln=True)
            img_data = io.BytesIO(chart_images["trend_income"])
            pdf.image(img_data, x=10, y=pdf.get_y(), w=180)
            pdf.set_y(pdf.get_y() + 100)

    # Output als Bytes
    return bytes(pdf.output())
