import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EchoBuilding AI - Energy Decision System",
    page_icon="⚡",
    layout="wide"
)

# --- TITLE & HEADER ---
st.title("⚡ EchoBuilding AI: Dairesel Bina Enerji İşletim Sistemi")
st.caption("NILM Tabanlı Hayalet Yük Tespiti & Pasif Gece Soğutması (Night-Purge) Reçete Paneli | Ankara / Türkiye")

st.markdown("---")

# --- SIDEBAR: CONTROL PANEL ---
st.sidebar.header("🏢 Bina & Konum Parametreleri")
building_type = st.sidebar.selectbox("Bina Tipi", ["Kamu Kompleksi", "Ticari Plaza / İş Merkezi", "Üniversite Kampüs Binası"])
location = st.sidebar.text_input("Şehir", "Ankara, TR")
sqm = st.sidebar.number_input("Toplam Alan (m²)", value=15000)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Simulation Settings")
use_live_weather = st.sidebar.checkbox("Canlı Hava Durumu API (Ankara)", value=True)

# API Key Simulation
openai_api_key = st.sidebar.text_input("OpenAI API Key (Opsiyonel)", type="password", help="Boş bırakılırsa kural tabanlı AI simülatörü çalışır.")

# --- MOCK DATA GENERATOR (NILM & Energy Consumption) ---
@st.cache_data
def load_energy_data():
    # freq='h' olarak düzeltildi
    dates = pd.date_range(start=datetime.datetime.now() - datetime.timedelta(days=1), periods=24, freq='h')
    base_load = [35, 32, 30, 28, 29, 31, 65, 120, 180, 210, 220, 215, 200, 210, 225, 230, 190, 110, 75, 55, 48, 42, 38, 36]
    phantom_load = [12, 12, 11, 11, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 12, 12, 12, 12, 12] # Mesai dışı israf
    
    df = pd.DataFrame({
        'Saat': [d.strftime('%H:00') for d in dates],
        'Top Tüketim (kWh)': base_load,
        'Hayalet Yük / İsraf (kWh)': phantom_load
    })
    return df

df_energy = load_energy_data()

# --- MAIN DASHBOARD LAYOUT ---
col1, col2, col3, col4 = st.columns(4)

total_today = df_energy['Top Tüketim (kWh)'].sum()
phantom_today = df_energy['Hayalet Yük / İsraf (kWh)'].sum()
waste_percentage = round((phantom_today / total_today) * 100, 1)
co2_saved_est = round((phantom_today * 0.8 * 0.42), 1) # kg CO2

col1.metric("Günlük Toplam Tüketim", f"{total_today:,} kWh")
col2.metric("NILM Tespiti: Hayalet Yük", f"{phantom_today} kWh", delta=f"%{waste_percentage} İsraf", delta_color="inverse")
col3.metric("Hedeflenen Günlük Tasarruf", f"{int(phantom_today * 0.8)} kWh", delta="-%80 İsraf Önleme")
col4.metric("Engellenecek Karbon", f"{co2_saved_est} kg CO₂", delta="Ağaç Denkliği: 3 Ağaç")

st.markdown("---")

# --- CHARTS & ANALYSIS ---
tab1, tab2 = st.tabs(["📊 Yük Ayrıştırma (NILM) & İsraf Analizi", "🌡️ Pasif Gece Soğutması (Night-Purge) Mantığı"])

with tab1:
    st.subheader("Bina Ana Pano Saatlik Elektrik Tüketimi (NILM Analizi)")
    st.bar_chart(df_energy.set_index('Saat')[['Top Tüketim (kWh)', 'Hayalet Yük / İsraf (kWh)']])
    st.info("💡 **NILM Teşhisi:** Gece 22:00 - 06:00 saatleri arasında HVAC havalandırma fanları ve kesintisiz güç kaynakları (UPS) atıl çalışmaya devam etmektedir.")

with tab2:
    st.subheader("Ankara Termal Kütle ve Dış Hava Sıcaklık Grafiği")
    hours = [f"{i:02d}:00" for i in range(24)]
    outside_temp = [14, 13, 12, 12, 11, 12, 15, 18, 22, 25, 27, 28, 29, 28, 27, 25, 22, 19, 17, 16, 15, 15, 14, 14]
    inside_temp = [23, 23, 22, 22, 22, 22, 23, 24, 25, 25, 26, 26, 26, 26, 26, 25, 25, 24, 24, 24, 23, 23, 23, 23]
    
    df_temp = pd.DataFrame({'Dış Hava (°C)': outside_temp, 'Bina İç Sıcaklık (°C)': inside_temp}, index=hours)
    st.line_chart(df_temp)
    st.success("✅ **Pasif Potansiyel:** Gece 01:00 - 05:00 arasında dış hava 11-12°C'ye düşmektedir. Gece havalandırması (Night-Purge) ile bina kütlesi bedavaya soğutulabilir.")

st.markdown("---")

# --- AI PRESCRIPTIVE DECISION ENGINE ---
st.subheader("🤖 AI Preskriptif Karar Destek ve Otonom Reçete Motoru")

def generate_ai_recipe():
    return """
    ### 📋 GÜNÜN OTONOM ENERJİ TASARRUF REÇETESİ
    **Tarih/Saat:** 21 Ekim 2026 | **Konum:** Ankara
    
    1. **Gece Soğutması Reçetesi (Night-Purge):**
       - **Aksiyon:** Bu gece saat 02:00 - 05:00 arasında HVAC gazlı soğutma kompresörlerini kapatın. 3. Kat ve Güney Cephe havalandırma kapaklarını %40 açıklıkla devreye sokun.
       - **Gerekçe:** Dış hava 11°C'ye düşmektedir. Beton kütleyi pasif soğutmak, yarın sabahki ilk çalıştırma yükünü %25 azaltacaktır.
    
    2. **Hayalet Yük Kapatma Reçetesi (NILM):**
       - **Aksiyon:** Mesai bitiminde (19:00) 2. Pano altındaki otonom olmayan aydınlatma ve güç gruplarını pasife alın.
    
    ---
    💰 **Tahmini Finansal Tasarruf:** 4.250 TL / Gün  
    🌱 **Engellenen CO₂ Emisyonu:** 142 kg  
    🔌 **BMS İletişim Protokolü:** BACnet/IP (WriteProperty -> AV:102 -> 40%)
    """

st.markdown(generate_ai_recipe())

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("✅ REÇETEYİ ONAYLA & BMS'E İLET", type="primary"):
        st.balloons()
        st.success("⚡ BACnet/IP Komutu Gönderildi! Bina Otomasyon Panosu Reçeteyi Uyguluyor...")