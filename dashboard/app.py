import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import os

# Configuration page (DOIT être la première commande Streamlit)
st.set_page_config(
    page_title="Bitcoin Dashboard",
    page_icon="₿",
    layout="wide"
)

# Fonction pour charger données
@st.cache_data(ttl=3600)  # Cache 1 heure
def load_bitcoin_data():
    """Charge données Bitcoin depuis CSV"""
    try:
        df = pd.read_csv('data/bitcoin_price.csv', index_col='date', parse_dates=True)
        return df
    except FileNotFoundError:
        st.error("❌ Fichier data/bitcoin_price.csv introuvable. Lance test_basics.py d'abord.")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lecture données : {e}")
        return None


def refresh_bitcoin_data(days=365):
    """Re-télécharge données Bitcoin depuis CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return None, f"Erreur API : Status {response.status_code}"
        
        data = response.json()
        
        if 'prices' not in data:
            return None, "Format réponse invalide"
        
        # Convertit en DataFrame
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['date', 'price']]
        df.set_index('date', inplace=True)
        
        # Sauvegarde
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/bitcoin_price.csv')
        
        return df, None
        
    except Exception as e:
        return None, str(e)


# --- MAIN DASHBOARD ---
st.title("₿ Bitcoin Price Dashboard")
st.markdown("---")

# Charge données
with st.spinner("Chargement des données..."):
    df = load_bitcoin_data()

# Affiche dashboard seulement si données existent
if df is not None and not df.empty:
    
    # === SIDEBAR : FILTRES ===
    st.sidebar.header("⚙️ Paramètres")
    
    # Slider période
    days_to_show = st.sidebar.slider(
        "Période affichée (jours)",
        min_value=7,
        max_value=len(df),
        value=365,
        step=1,
        key="days_slider"  # Clé unique
    )
    
    # Filtre le DataFrame
    df_filtered = df.tail(days_to_show)
    
    st.sidebar.info(f"📅 Affichage : {len(df_filtered)} jours")
    
    st.sidebar.markdown("---")
    
    # Bouton refresh avec clé unique
    if st.sidebar.button("🔄 Rafraîchir les données", type="primary", key="refresh_button"):
        with st.spinner("📡 Téléchargement des nouvelles données..."):
            new_df, error = refresh_bitcoin_data(days=365)
            
            if error:
                st.sidebar.error(f"❌ Erreur : {error}")
            else:
                st.sidebar.success("✅ Données mises à jour !")
                st.cache_data.clear()
                st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("💡 Bouge le slider pour ajuster la période")
    
    st.sidebar.markdown("---")
    
    #Bouton export CSV
    st.sidebar.subheader("📥 Export Données")
    
    # Prépare CSV pour download
    csv_data = df_filtered.to_csv().encode('utf-8')
    
    st.sidebar.download_button(
        label="💾 Télécharger CSV",
        data=csv_data,
        file_name=f"bitcoin_price_{days_to_show}j_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="download_csv_button"
    )
    
    st.sidebar.caption(f"📊 Export : {len(df_filtered)} jours")
    # === SECTION 1 : Métriques Clés ===
    st.header("📊 Métriques Clés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculs
    current_price = df_filtered['price'].iloc[-1]
    avg_price = df_filtered['price'].mean()
    variation = ((current_price - avg_price) / avg_price) * 100
    min_price = df_filtered['price'].min()
    max_price = df_filtered['price'].max()
    
    # Affichage métriques
    with col1:
        st.metric(
            label="Prix Actuel",
            value=f"${current_price:,.2f}",
            delta=f"{variation:+.2f}% vs moyenne"
        )
    
    with col2:
        st.metric(
            label=f"Prix Moyen ({days_to_show}j)",
            value=f"${avg_price:,.2f}"
        )
    
    with col3:
        st.metric(
            label=f"Plus Bas ({days_to_show}j)",
            value=f"${min_price:,.2f}"
        )
    
    with col4:
        st.metric(
            label=f"Plus Haut ({days_to_show}j)",
            value=f"${max_price:,.2f}"
        )
    
    st.markdown("---")
    
    # === SECTION 2 : Graphique Prix ===
    st.header("📈 Évolution du Prix")
    
    # Toggle moyennes mobiles avec clé unique
    show_ma = st.checkbox("📊 Afficher moyennes mobiles (MA7 / MA30)", value=False, key="show_ma_checkbox")
    
    # Calcule moyennes mobiles si activées
    if show_ma:
        df_filtered = df_filtered.copy()  # Évite SettingWithCopyWarning
        df_filtered['MA7'] = df_filtered['price'].rolling(window=7, min_periods=1).mean()
        df_filtered['MA30'] = df_filtered['price'].rolling(window=30, min_periods=1).mean()
    
    # Créer graphique Plotly
    fig = go.Figure()
    
    # Ligne principale : Prix Bitcoin
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered['price'],
        mode='lines',
        name='Prix Bitcoin',
        line=dict(color='#00D9FF', width=2)
    ))
    
    # Moyennes mobiles si activées
    if show_ma:
        fig.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['MA7'],
            mode='lines',
            name='MA 7 jours',
            line=dict(color='#FFA500', width=2, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['MA30'],
            mode='lines',
            name='MA 30 jours',
            line=dict(color='#00FF00', width=2, dash='dot')
        ))
    
    # Mise en page
    fig.update_layout(
        title=f'Bitcoin Price ({days_to_show} derniers jours)',
        xaxis_title="Date",
        yaxis_title="Prix (USD)",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    # Affiche graphique
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === SECTION 3 : Données Brutes ===
    st.header("📋 Données Brutes")
    
    # Toggle avec clé unique
    if st.checkbox("Afficher données complètes", key="show_data_checkbox"):
        st.dataframe(df_filtered.sort_index(ascending=False), use_container_width=True)
    
    # Statistiques
    st.subheader("Statistiques")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Période**")
        st.write(f"- Début : {df_filtered.index[0].strftime('%Y-%m-%d')}")
        st.write(f"- Fin : {df_filtered.index[-1].strftime('%Y-%m-%d')}")
        st.write(f"- Nombre de jours : {len(df_filtered)}")
    
    with col2:
        st.write("**Prix**")
        st.write(f"- Écart-type : ${df_filtered['price'].std():,.2f}")
        st.write(f"- Médiane : ${df_filtered['price'].median():,.2f}")
        st.write(f"- Volatilité : {(df_filtered['price'].std() / df_filtered['price'].mean() * 100):.2f}%")

else:
    # Message si pas de données
    st.warning("⚠️ Aucune donnée disponible. Exécute `python test_basics.py` pour télécharger les données.")
    
    with st.expander("📖 Instructions"):
        st.code("""
# 1. Télécharge les données Bitcoin
python test_basics.py

# 2. Lance le dashboard
streamlit run dashboard/app.py
        """, language="bash")

# Footer
st.markdown("---")
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
