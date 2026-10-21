import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EchoBuilding AI - Energy Decision System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR HIGH VISIBILITY & UI ENHANCEMENTS ---
st.markdown("""
    <style>
    .recipe-card {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
        padding: 24px;
        border-radius: 14px;
        border-left: 6px solid #00d26a;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .recipe-card h4 {
        color: #0f5132 !important;
        margin-top: 0;
        font-size: 20px;
    }
    .recipe-card p, .recipe-card li {
        color: #2b2b2b !important;
        font-size: 15px;
    }
    .impact-badge-green {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 18px;
        display: inline-block;
        margin-right: 12px;
        border: 1px solid #badbcc;
    }
    .impact-badge-blue {
        background-color: #cff4fc;
        color: #055160;
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 18px;
        display: inline-block;
        border: 1px solid #b6effb;
    }
    .chat-box {
        background-color: #e8f5e9 !important;
        border: 1px solid #c8e6c9;
        border-radius: 10px;
        padding: 15px;
        color: #1b5e20 !important;
        font-size: 15px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

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
st.sidebar.header("⚙️ Simülasyon Ayarları")
use_live_weather = st.sidebar.checkbox("Canlı Hava Durumu API (Ankara)", value=True)
selected_day = st.sidebar.date_input("Analiz Tarihi", datetime.date.today())

# --- MOCK DATA GENERATOR (NILM & Energy Consumption) ---
@st.cache_data
def load_energy_data():
    dates = pd.date_range(start=datetime.datetime.now() - datetime.timedelta(days=1), periods=24, freq='h')
    base_load = [35, 32, 30, 28, 29, 31, 65, 120, 180, 210, 220, 215, 200, 210, 225, 230, 190, 110, 75, 55, 48, 42, 38, 36]
    phantom_load = [12, 12, 11, 11, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 12, 12, 12, 12, 12]
    
    df = pd.DataFrame({
        'Saat': [d.strftime('%H:00') for d in dates],
        'Top Tüketim (kWh)': base_load,
        'Hayalet Yük / İsraf (kWh)': phantom_load
    })
    return df

df_energy = load_energy_data()

# --- DYNAMIC CALCULATIONS (TAM UYUMLU MATEMATİK) ---
total_today = df_energy['Top Tüketim (kWh)'].sum()
phantom_today = df_energy['Hayalet Yük / İsraf (kWh)'].sum()
waste_percentage = round((phantom_today / total_today) * 100, 1)

# NILM + Night Purge Toplam Tasarrufu
night_purge_kwh_save = 220  # Gece kompresör kapatıp soğutmaktan gelen kWh tasarruf
total_kwh_saved = int((phantom_today * 0.8) + night_purge_kwh_save)

# Karbon Faktörü (0.42 kg CO2 / kWh) & Finansal Faktör (4.25 TL / kWh)
co2_saved_total = round(total_kwh_saved * 0.42, 1)
tl_saved_total = int(total_kwh_saved * 4.25)

# --- MAIN DASHBOARD METRICS ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("Günlük Toplam Tüketim", f"{total_today:,} kWh")
col2.metric("NILM Tespiti: Hayalet Yük", f"{phantom_today} kWh", delta=f"%{waste_percentage} İsraf Mevcut", delta_color="inverse")
col3.metric("Hedeflenen Günlük Tasarruf", f"{total_kwh_saved} kWh", delta="%80 İsraf + Night-Purge", delta_color="normal")
col4.metric("Engellenecek Karbon", f"{co2_saved_total} kg CO₂", delta="Ağaç Denkliği: 6 Ağaç", delta_color="normal")

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

st.markdown(f"""
<div class="recipe-card">
    <h4>📋 GÜNÜN OTONOM ENERJİ TASARRUF REÇETESİ</h4>
    <p><b>Konum:</b> Ankara, Türkiye | <b>Sistem Durumu:</b> BMS Bağlantısı Aktif (BACnet/IP Gateway)</p>
    <ul>
        <li><b>🌙 Gece Soğutması Reçetesi (Night-Purge):</b> Bu gece saat 02:00 - 05:00 arasında HVAC kompresörlerini kapatın. 3. Kat ve Güney Cephe havalandırma kapaklarını %40 açıklıkla devreye sokun.</li>
        <li><b>🔌 Hayalet Yük Kapatma Reçetesi (NILM):</b> Mesai bitiminde (19:00) 2. Pano altındaki otonom olmayan aydınlatma ve güç gruplarını pasife alın.</li>
    </ul>
    <br>
    <div>
        <span class="impact-badge-green">💰 Günlük Tasarruf: {tl_saved_total:,} TL</span>
        <span class="impact-badge-blue">🌱 Karbon Engelleme: {co2_saved_total} kg CO₂</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns([1, 2])

with col_btn1:
    if st.button("✅ REÇETEYİ ONAYLA & BMS'E İLET", type="primary", use_container_width=True):
        st.balloons()
        
        # BMS Terminal Log Simulation
        st.markdown("##### 🔌 BACnet/IP Terminal Logları:")
        log_box = st.empty()
        log_text = "> Connecting to Gateway 192.168.1.50:47808...\n"
        log_box.code(log_text)
        time.sleep(0.4)
        
        log_text += "> Authentication Successful (Priority 8 - Manual Override)\n"
        log_box.code(log_text)
        time.sleep(0.4)
        
        log_text += "> Writing Property: BACnet.Analog_Value.102 -> PresentValue = 40.0%\n"
        log_box.code(log_text)
        time.sleep(0.4)
        
        log_text += "> SUCCESS: Command executed by BMS. Night-Purge Enabled."
        log_box.code(log_text, language="bash")
        
        st.success("⚡ Reçete Başarıyla Uygulandı! Bina otomasyon ağı otonom konfigüre edildi.")

# --- RELIABLE & INTERACTIVE AI ASSISTANT ---
st.markdown("---")
st.subheader("💬 AI Bina Yöneticisi Asistanı (Soru - Cevap)")
st.caption("Reçetenin gerekçesi, konfor etkisi ve maliyet hesabı hakkında yapay zeka analizini inceleyin:")

selected_question = st.selectbox(
    "Bir soru seçin veya merak ettiğiniz konuyu inceleyin:",
    [
        "--- Lütfen bir soru seçin ---",
        "❓ Neden gece 02:00 - 05:00 saatleri seçildi?",
        "❓ Gece havalandırması bina içi termal konforu düşürür mü?",
        "❓ Finansal tasarruf hesabı neye dayanıyor?",
        "❓ Eski BMS sistemimiz bu reçeteyi nasıl uygulayacak?"
    ]
)

if selected_question == "❓ Neden gece 02:00 - 05:00 saatleri seçildi?":
    st.markdown("""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        OpenWeather API verilerine göre Ankara'da dış ortam sıcaklığı gece saat 02:00 - 05:00 arasında minimum seviyeye (11°C) düşmektedir. Binanın betonarme kütlesini bu saatlerde doğal havayla soğutmak, sabah klimanın ilk çalıştırma pik yükünü %25 azaltmaktadır.
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ Gece havalandırması bina içi termal konforu düşürür mü?":
    st.markdown("""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        Hayır, ASHRAE 55 standartlarına göre konfor olumsuz etkilenmez. Gece soğutması sadece bina beton kütlesini 21°C seviyesinde tutar. Mesai başlangıcı olan 08:00'de iç ortam sıcaklığı ideal termal konfor bandında (22.5°C) dengelenir.
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ Finansal tasarruf hesabı neye dayanıyor?":
    st.markdown(f"""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        Bu reçete ile yüksek elektrik çeken gazlı soğutma kompresörleri çalıştırılmadan sadece düşük güçlü havalandırma fanlarıyla pasif soğutma yapılır. Günlük toplam {total_kwh_saved} kWh elektrik tüketimi engellenerek {tl_saved_total:,} TL ve {co2_saved_total} kg CO₂ doğrudan tasarruf edilir.
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ Eski BMS sistemimiz bu reçeteyi nasıl uygulayacak?":
    st.markdown("""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        Geliştirdiğimiz hafif IoT Yazılım Köprüsü (Gateway), eski veya yeni tüm BMS sistemlerinin kullandığı evrensel BACnet/Modbus dilini konuşur. 'REÇETEYİ ONAYLA' butonuna bastığınızda komut otonom olarak vanalara enjekte edilir.
    </div>
    """, unsafe_allow_html=True)
