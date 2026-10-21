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
st.caption("NILM Tabanlı Hayalet Yük Tespiti & Pasif Gece Soğutması (Night-Purge) Reçete Paneli")

st.markdown("---")

# --- SIDEBAR: CONTROL PANEL ---
st.sidebar.header("🏢 Bina & Konum Parametreleri")
building_type = st.sidebar.selectbox("Bina Tipi", ["Ticari Plaza / İş Merkezi", "Kamu Kompleksi", "Üniversite Kampüs Binası"])
location = st.sidebar.selectbox("Şehir (İklim İstasyonu)", ["Ankara", "Erzurum", "İstanbul", "İzmir", "Antalya"])
sqm = st.sidebar.number_input("Toplam Alan (m²)", value=15000, step=1000)

st.sidebar.markdown("---")
st.sidebar.header("📅 Analiz & Zaman Ayarları")
selected_day = st.sidebar.date_input("Analiz Tarihi", datetime.date.today())

st.sidebar.info("🛰️ **Canlı OpenWeather Entegrasyonu:** Aktif (Sürekli İklim Verisi Akışı)")

# --- DYNAMIC PARAMETERS BASED ON INPUTS & DATE ---
scale_factor = sqm / 15000.0

# Tarihe Bağlı Çarpanlar (Hafta sonu mesai olmaması veya gün farkı etkisi)
day_seed = selected_day.day + selected_day.month * 31
is_weekend = selected_day.weekday() >= 5
date_load_factor = 0.4 if is_weekend else (0.9 + (day_seed % 20) / 100.0) # Hafta sonu tüketim %60 düşer

# Bina Tipine Göre Hayalet Yük / İsraf Çarpanı
b_type_multiplier = {
    "Ticari Plaza / İş Merkezi": 1.2,
    "Kamu Kompleksi": 1.0,
    "Üniversite Kampüs Binası": 0.85
}[building_type]

# Şehre Göre Gece Sıcaklık Profili ve Night-Purge Verim Çarpanı (Tarihe göre ufak dalgalanma)
weather_profiles = {
    "Ankara":  {"temps": [14, 13, 12, 12, 11, 12, 15, 18, 22, 25, 27, 28, 29, 28, 27, 25, 22, 19, 17, 16, 15, 15, 14, 14], "np_mult": 1.0},
    "Erzurum": {"temps": [7, 6, 5, 5, 4, 5, 8, 12, 16, 19, 21, 22, 22, 21, 19, 16, 13, 10, 9, 8, 8, 7, 7, 7], "np_mult": 1.35},
    "İstanbul":{"temps": [18, 17, 17, 16, 16, 17, 19, 22, 24, 26, 27, 27, 28, 27, 26, 24, 23, 21, 20, 19, 19, 18, 18, 18], "np_mult": 0.8},
    "İzmir":   {"temps": [21, 20, 19, 19, 18, 19, 22, 25, 28, 30, 32, 33, 33, 32, 31, 29, 27, 25, 24, 23, 22, 22, 21, 21], "np_mult": 0.6},
    "Antalya": {"temps": [24, 23, 22, 22, 21, 22, 25, 28, 31, 33, 35, 36, 36, 35, 34, 32, 30, 28, 27, 26, 25, 25, 24, 24], "np_mult": 0.4}
}

city_weather = weather_profiles[location]
# Tarihe göre sıcaklığı biraz çeşitlendiriyoruz
temp_shift = (day_seed % 5) - 2
outside_temp = [t + temp_shift for t in city_weather["temps"]]
np_mult = city_weather["np_mult"]

# --- MOCK DATA GENERATOR (NILM & Energy Consumption) ---
@st.cache_data
def load_energy_data(factor, b_mult, d_factor, date_val):
    dates = pd.date_range(start=datetime.datetime.combine(date_val, datetime.time(0, 0)), periods=24, freq='h')
    base_load = [int(x * factor * d_factor) for x in [35, 32, 30, 28, 29, 31, 65, 120, 180, 210, 220, 215, 200, 210, 225, 230, 190, 110, 75, 55, 48, 42, 38, 36]]
    
    # Hafta sonu hayalet yük oransal olarak daha belirginleşir
    p_factor = 1.4 if is_weekend else 1.0
    phantom_load = [int(x * factor * b_mult * p_factor) for x in [12, 12, 11, 11, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 12, 12, 12, 12, 12]]
    
    df = pd.DataFrame({
        'Saat': [d.strftime('%H:00') for d in dates],
        'Top Tüketim (kWh)': base_load,
        'Hayalet Yük / İsraf (kWh)': phantom_load
    })
    return df

df_energy = load_energy_data(scale_factor, b_type_multiplier, date_load_factor, selected_day)

# --- DETAYLI DİNAMİK MATEMATİKSEL TASARRUF HESABI ---
total_today = df_energy['Top Tüketim (kWh)'].sum()
phantom_today = df_energy['Hayalet Yük / İsraf (kWh)'].sum()
waste_percentage = round((phantom_today / total_today) * 100, 1) if total_today > 0 else 0

# 1. NILM Tasarrufu (Hayalet Yükün %80'i)
nilm_kwh_save = int(phantom_today * 0.8)
nilm_tl_save = int(nilm_kwh_save * 4.25)
nilm_co2_save = round(nilm_kwh_save * 0.42, 1)

# 2. Night-Purge (Gece Soğutması) Tasarrufu
np_kwh_save = int(220 * scale_factor * np_mult * (0.3 if is_weekend else 1.0))
np_tl_save = int(np_kwh_save * 4.25)
np_co2_save = round(np_kwh_save * 0.42, 1)

# 3. Toplamlar
total_kwh_saved = nilm_kwh_save + np_kwh_save
total_tl_saved = nilm_tl_save + np_tl_save
total_co2_saved = round(nilm_co2_save + np_co2_save, 1)

# --- MAIN DASHBOARD METRICS ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("Günlük Toplam Tüketim", f"{total_today:,} kWh", help=f"{selected_day.strftime('%d.%m.%Y')} Tarihli Tüketim")
col2.metric("NILM Tespiti: Hayalet Yük", f"{phantom_today:,} kWh", delta=f"%{waste_percentage} İsraf Mevcut", delta_color="inverse")
col3.metric("Hedeflenen Toplam Tasarruf", f"{total_kwh_saved:,} kWh", delta=f"NILM: {nilm_kwh_save} kWh | Purge: {np_kwh_save} kWh", delta_color="normal")
col4.metric("Engellenecek Toplam Karbon", f"{total_co2_saved:,} kg CO₂", delta=f"NILM: {nilm_co2_save}kg | Purge: {np_co2_save}kg", delta_color="normal")

st.markdown("---")

# --- CHARTS & ANALYSIS ---
tab1, tab2 = st.tabs(["📊 Yük Ayrıştırma (NILM) & İsraf Analizi", "🌡️ Pasif Gece Soğutması (Night-Purge) Mantığı"])

with tab1:
    day_type_str = "Hafta Sonu (Düşük Mesai)" if is_weekend else "Hafta İçi Mesai"
    st.subheader(f"{building_type} Saatlik Elektrik Tüketimi ({selected_day.strftime('%d.%m.%Y')} - {day_type_str})")
    st.bar_chart(df_energy.set_index('Saat')[['Top Tüketim (kWh)', 'Hayalet Yük / İsraf (kWh)']])
    st.info(f"💡 **NILM Teşhisi:** {selected_day.strftime('%d.%m.%Y')} tarihinde gece mesai dışı atıl çalışan cihazların kapatılmasıyla günde **{nilm_kwh_save:,} kWh ({nilm_tl_save:,} TL / {nilm_co2_save:,} kg CO₂)** tasarruf elde edilir.")

with tab2:
    st.subheader(f"{location} Termal Kütle ve Hava Sıcaklığı ({selected_day.strftime('%d.%m.%Y')})")
    hours = [f"{i:02d}:00" for i in range(24)]
    inside_temp = [23, 23, 22, 22, 22, 22, 23, 24, 25, 25, 26, 26, 26, 26, 26, 25, 25, 24, 24, 24, 23, 23, 23, 23]
    
    df_temp = pd.DataFrame({'Dış Hava (°C)': outside_temp, 'Bina İç Sıcaklık (°C)': inside_temp}, index=hours)
    st.line_chart(df_temp)
    
    if np_mult >= 0.8:
        st.success(f"✅ **Yüksek Pasif Potansiyel ({location}):** {selected_day.strftime('%d.%m.%Y')} gecesi dış ortam sıcaklığı ideal soğutma bandına düşmektedir. Night-Purge ile günde **{np_kwh_save:,} kWh ({np_tl_save:,} TL / {np_co2_save:,} kg CO₂)** pasif soğutma kazanılır.")
    else:
        st.warning(f"⚠️ **Sınırlı Pasif Potansiyel ({location}):** Sıcak/Nemli gece iklimi sebebiyle Night-Purge katkısı **{np_kwh_save:,} kWh ({np_tl_save:,} TL)** seviyesindedir. Hibrit fan desteği önerilir.")

st.markdown("---")

# --- AI PRESCRIPTIVE DECISION ENGINE ---
st.subheader("🤖 AI Preskriptif Karar Destek ve Otonom Reçete Motoru")

st.markdown(f"""
<div class="recipe-card">
    <h4>📋 OTONOM ENERJİ TASARRUF REÇETESİ ({selected_day.strftime('%d.%m.%Y')})</h4>
    <p><b>Konum:</b> {location}, Türkiye | <b>Bina Tipi:</b> {building_type} ({sqm:,} m²) | <b>Sistem Durumu:</b> BMS Bağlantısı Aktif (BACnet/IP Gateway)</p>
    <ul>
        <li><b>🌙 Pasif Gece Soğutması (Night-Purge):</b> Gece 02:00 - 05:00 arasında HVAC kompresörlerini kapatın, havalandırmayı %40 açın. <br>👉 <i>Katkı: {np_tl_save:,} TL / {np_co2_save:,} kg CO₂</i></li>
        <li style="margin-top: 8px;"><b>🔌 Hayalet Yük Kapatma (NILM):</b> Mesai bitiminde (19:00) 2. Pano altındaki güç gruplarını pasife alın. <br>👉 <i>Katkı: {nilm_tl_save:,} TL / {nilm_co2_save:,} kg CO₂</i></li>
    </ul>
    <br>
    <div>
        <span class="impact-badge-green">💰 Toplam Tasarruf: {total_tl_saved:,} TL / Gün</span>
        <span class="impact-badge-blue">🌱 Toplam Karbon Engelleme: {total_co2_saved:,} kg CO₂</span>
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
        log_text = f"> Connecting to Gateway 192.168.1.50:47808 ({location} Regional Server)...\n"
        log_box.code(log_text)
        time.sleep(0.4)
        
        log_text += f"> Authentication Successful (Priority 8 - {building_type} Config)\n"
        log_box.code(log_text)
        time.sleep(0.4)
        
        log_text += f"> Writing Property: BACnet.Analog_Value.102 -> Date = {selected_day.strftime('%Y-%m-%d')} -> PresentValue = 40.0%\n"
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
        "❓ Seçilen analiz tarihi sonuçları nasıl etkiliyor?",
        "❓ Şehir ve iklim seçimi tasarruf reçetesini nasıl etkiler?",
        "❓ NILM ve Night-Purge tasarruf kalemleri ayrı ayrı nedir?",
        "❓ Gece havalandırması bina içi termal konforu düşürür mü?",
        "❓ Eski BMS sistemimiz bu reçeteyi nasıl uygulayacak?"
    ]
)

if selected_question == "❓ Seçilen analiz tarihi sonuçları nasıl etkiliyor?":
    st.markdown(f"""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz ({selected_day.strftime('%d.%m.%Y')}):</b><br>
        Seçtiğiniz <b>{selected_day.strftime('%d.%m.%Y')}</b> tarihi {'hafta sonuna denk geldiği için bina baz tüketimi düşük ancak atıl hayalet yük oranı daha belirgindir.' if is_weekend else 'hafta içi mesai günüdür. Günlük çalışma rejimine göre pik yükler ve gece soğutması fırsatı anlık hesaplanmıştır.'}
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ Şehir ve iklim seçimi tasarruf reçetesini nasıl etkiler?":
    st.markdown(f"""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz ({location}):</b><br>
        Seçilen <b>{location}</b> şehrinin gece-gündüz sıcaklık farkı analiz edilmiştir. Karasal iklimlerde (Ankara, Erzurum) gece dış hava soğukluğu yüksek olduğu için Night-Purge verimi artar. Nemli iklimlerde (Antalya, İzmir) ise sistem kompresörsöz soğutma potansiyelini otomatik olarak daha temkinli hesaplar.
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ NILM ve Night-Purge tasarruf kalemleri ayrı ayrı nedir?":
    st.markdown(f"""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        • <b>NILM (Hayalet Yük):</b> Gece açık unutulan fan ve UPS kaçaklarını keserek <b>{nilm_kwh_save:,} kWh ({nilm_tl_save:,} TL / {nilm_co2_save:,} kg CO₂)</b> tasarruf sağlar.<br>
        • <b>Night-Purge (Gece Soğutması):</b> Kompresörsüz pasif havalandırmayla <b>{np_kwh_save:,} kWh ({np_tl_save:,} TL / {np_co2_save:,} kg CO₂)</b> tasarruf sağlar.<br>
        • <b>Toplam Günlük Etki ({location} - {sqm:,} m²):</b> {total_kwh_saved:,} kWh ({total_tl_saved:,} TL ve {total_co2_saved:,} kg CO₂).
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ Gece havalandırması bina içi termal konforu düşürür mü?":
    st.markdown("""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        Hayır, ASHRAE 55 standartlarına göre konfor olumsuz etkilenmez. Gece soğutması sadece bina beton kütlesini 21°C seviyesinde tutar. Mesai başlangıcı olan 08:00'de iç ortam sıcaklığı ideal termal konfor bandında (22.5°C) dengelenir.
    </div>
    """, unsafe_allow_html=True)

elif selected_question == "❓ Eski BMS sistemimiz bu reçeteyi nasıl uygulayacak?":
    st.markdown("""
    <div class="chat-box">
        <b>🤖 AI Preskriptif Analiz:</b><br>
        Geliştirdiğimiz hafif IoT Yazılım Köprüsü (Gateway), eski veya yeni tüm BMS sistemlerinin kullandığı evrensel BACnet/Modbus dilini konuşur. 'REÇETEYİ ONAYLA' butonuna bastığınızda komut otonom olarak vanalara enjekte edilir.
    </div>
    """, unsafe_allow_html=True)
