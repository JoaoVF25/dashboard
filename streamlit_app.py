import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO
import openpyxl  # Necessário para pd.read_excel
import requests
import warnings
import time
from datetime import datetime, timedelta
import yfinance as yf
from portfolio_manager import PortfolioManager

# Ignorar warnings de Feature que podem aparecer em algumas versões do pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# Configuração da página
st.set_page_config(
    page_title="Warren - Dashboard de Carteira",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CHAVE DA API ---
# Substitua pela sua chave da API da brapi.dev
BRAPI_API_KEY = "uriuR777zhTQDGCMcZK8Yv"

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e8b57 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2e8b57;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- INTERFACE PRINCIPAL ---
st.markdown("""
<div class="main-header">
    <h1>💼 Warren - Dashboard de Análise de Carteira</h1>
    <p>Análise completa e em tempo real da sua carteira de investimentos</p>
</div>
""", unsafe_allow_html=True)

# Sidebar melhorada
with st.sidebar:
    st.markdown("### 📊 Sobre o Dashboard")
    st.info(
        "🚀 **Recursos:**\n"
        "• Cotações em tempo real via brapi.dev\n"
        "• Análise de composição da carteira\n"
        "• Gráficos interativos\n"
        "• Formatação brasileira de números"
    )
    
    st.markdown("### 📈 Status da API")
    st.success("🟢 brapi.dev conectada")
    
    st.markdown("---")
    st.markdown("*Desenvolvido com ❤️ usando Streamlit*")

tab1, tab2, tab3 = st.tabs(["📤 Upload de Carteira", "💰 Dividendos", "📚 Portfólios Salvos"])

# Inicializa o gerenciador de portfólios
if 'portfolio_manager' not in st.session_state:
    st.session_state.portfolio_manager = PortfolioManager()

# Colunas alvo que queremos encontrar e padronizar
TARGET_COLUMNS = ["Ativo", "Quantidade"]

# --- FUNÇÕES DE CONECTIVIDADE E DADOS ---

@st.cache_data(ttl=300)  # Cache de 5 minutos para evitar requisições repetidas
def get_yfinance_quotes(tickers):
    """
    Busca cotações e dados históricos usando yfinance.
    Retorna um dicionário com os tickers, seus preços e dados de volume financeiro.
    """
    if not tickers:
        return {}, [], {}

    st.info(f"🔍 Buscando cotações e dados históricos via yfinance para {len(tickers)} ativos...")
    
    prices = {}
    volume_data = {}
    not_found_tickers = []
    
    progress_bar = st.progress(0, text="🚀 Iniciando busca via yfinance...")

    for i, original_ticker in enumerate(tickers):
        progress_text = f"📈 Buscando: {original_ticker.replace('.SA', '')} ({i + 1}/{len(tickers)})"
        progress_bar.progress((i + 1) / len(tickers), text=progress_text)
        
        try:
            # Busca dados do ticker
            ticker_obj = yf.Ticker(original_ticker)
            
            # Busca dados históricos dos últimos 45 dias
            hist_data = ticker_obj.history(period="2mo", interval="1d")
            
            if not hist_data.empty and len(hist_data) > 0:
                # Pega o preço mais recente
                current_price = hist_data['Close'].iloc[-1]
                current_volume_shares = hist_data['Volume'].iloc[-1]
                current_volume_financial = current_volume_shares * current_price
                
                prices[original_ticker] = current_price
                
                # Calcula volume financeiro dos últimos 45 dias
                hist_data_45d = hist_data.tail(45)  # Últimos 45 dias
                
                volumes_financial = []
                for index, row in hist_data_45d.iterrows():
                    volume_shares = row['Volume']
                    close_price = row['Close']
                    
                    if volume_shares > 0 and close_price > 0:
                        volume_financial = volume_shares * close_price
                        volumes_financial.append(volume_financial)
                
                if len(volumes_financial) >= 10:
                    volume_median = np.median(volumes_financial)
                    volume_data[original_ticker] = {
                        'median_volume': volume_median,
                        'volumes': volumes_financial,
                        'current_volume': current_volume_financial,
                        'days_analyzed': len(volumes_financial),
                        'has_historical': True
                    }
                else:
                    volume_data[original_ticker] = {
                        'median_volume': current_volume_financial,
                        'volumes': [],
                        'current_volume': current_volume_financial,
                        'days_analyzed': 0,
                        'has_historical': False
                    }
            else:
                not_found_tickers.append(original_ticker)
                
        except Exception as e:
            not_found_tickers.append(original_ticker)
        
        time.sleep(0.1)  # Pausa pequena para não sobrecarregar

    progress_bar.empty()
    
    # Mensagem de sucesso
    historical_count = len([v for v in volume_data.values() if v.get('has_historical', False)])
    total_days = sum([v.get('days_analyzed', 0) for v in volume_data.values()])
    
    st.success(f"✅ yfinance: {len(prices)} cotações encontradas.")
    st.info(f"📊 Volume financeiro: {historical_count} ativos com dados históricos (total: {total_days} dias analisados)")
    
    if not_found_tickers:
        st.warning(f"⚠️ Não foi possível encontrar cotações para: {', '.join(not_found_tickers)}")
        
    return prices, not_found_tickers, volume_data

@st.cache_data(ttl=300)  # Cache de 5 minutos para evitar requisições repetidas
def get_brapi_quotes(tickers, api_key):
    """
    Busca cotações de múltiplos ativos na API da brapi.dev, fazendo uma requisição por vez
    para se adequar aos limites do plano gratuito.
    Retorna um dicionário com os tickers, seus preços e dados de volume financeiro.
    """
    if not tickers:
        return {}, [], {}

    st.info(f"🔍 Buscando cotações e dados históricos para {len(tickers)} ativos...")
    
    prices = {}
    volume_data = {}
    not_found_tickers = []
    headers = {'Authorization': f'Bearer {api_key}'}
    
    # Calcula datas para os últimos 45 dias
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=45)).strftime("%Y-%m-%d")
    
    progress_bar = st.progress(0, text="🚀 Iniciando busca de cotações e volume financeiro...")

    for i, original_ticker in enumerate(tickers):
        # A API da brapi não usa o sufixo .SA, então o removemos
        ticker_clean = original_ticker.replace('.SA', '')
        
        progress_text = f"📈 Buscando: {ticker_clean} ({i + 1}/{len(tickers)})"
        progress_bar.progress((i + 1) / len(tickers), text=progress_text)
        
        # Busca cotação atual
        url_quote = f"https://brapi.dev/api/quote/{ticker_clean}"
        
        try:
            # Cotação atual
            response_quote = requests.get(url_quote, headers=headers)
            response_quote.raise_for_status()
            data_quote = response_quote.json()
            results_quote = data_quote.get('results', [])
            
            if results_quote and results_quote[0].get('regularMarketPrice') is not None:
                current_price = results_quote[0]['regularMarketPrice']
                prices[original_ticker] = current_price
                current_volume_shares = results_quote[0].get('regularMarketVolume', 0)
                current_volume_financial = current_volume_shares * current_price  # Volume financeiro atual
                
                # Aguarda um pouco entre requisições
                time.sleep(0.15)
                
                # Busca dados históricos usando o endpoint /historical/
                try:
                    url_historical = f"https://brapi.dev/api/quote/historical/{ticker_clean}?start={start_date}&end={end_date}&interval=1d"
                    response_hist = requests.get(url_historical, headers=headers)
                    
                    if response_hist.status_code == 200:
                        data_hist = response_hist.json()
                        results_hist = data_hist.get('results', [])
                        
                        if results_hist and results_hist[0].get('historical'):
                            historical_data = results_hist[0]['historical']
                            
                            # Extrai volumes financeiros dos dados históricos
                            volumes_financial = []
                            
                            for day_data in historical_data:
                                volume_shares = day_data.get('volume')
                                close_price = day_data.get('close')
                                
                                if volume_shares and close_price and volume_shares > 0 and close_price > 0:
                                    volume_financial = volume_shares * close_price
                                    volumes_financial.append(volume_financial)
                            
                            if len(volumes_financial) >= 10:  # Precisa de pelo menos 10 dias para ser válido
                                volume_median = np.median(volumes_financial)
                                volume_data[original_ticker] = {
                                    'median_volume': volume_median,
                                    'volumes': volumes_financial,
                                    'current_volume': current_volume_financial,
                                    'days_analyzed': len(volumes_financial),
                                    'has_historical': True
                                }
                            else:
                                # Se não há dados históricos suficientes
                                volume_data[original_ticker] = {
                                    'median_volume': current_volume_financial,
                                    'volumes': [],
                                    'current_volume': current_volume_financial,
                                    'days_analyzed': 0,
                                    'has_historical': False
                                }
                        else:
                            # Se não conseguir estrutura esperada
                            volume_data[original_ticker] = {
                                'median_volume': current_volume_financial,
                                'volumes': [],
                                'current_volume': current_volume_financial,
                                'days_analyzed': 0,
                                'has_historical': False
                            }
                    else:
                        # Se falhar a busca histórica
                        volume_data[original_ticker] = {
                            'median_volume': current_volume_financial,
                            'volumes': [],
                            'current_volume': current_volume_financial,
                            'days_analyzed': 0,
                            'has_historical': False
                        }
                        
                except Exception as hist_error:
                    # Em caso de erro nos dados históricos
                    volume_data[original_ticker] = {
                        'median_volume': current_volume_financial,
                        'volumes': [],
                        'current_volume': current_volume_financial,
                        'days_analyzed': 0,
                        'has_historical': False
                    }
            else:
                not_found_tickers.append(original_ticker)

        except requests.exceptions.HTTPError as e:
            # Erros 404 (Not Found) são comuns para tickers inválidos, não são um erro fatal.
            if e.response.status_code == 404:
                not_found_tickers.append(original_ticker)
            else:
                # Outros erros HTTP (como 429) ainda podem ocorrer e param a execução
                st.error(f"❌ Erro HTTP ao buscar {ticker_clean}: {e}")
                # Adiciona todos os restantes à lista de não encontrados e para
                not_found_tickers.extend(tickers[i:])
                break 
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Erro de conexão ao buscar {ticker_clean}: {e}")
            not_found_tickers.extend(tickers[i:])
            break
        
        time.sleep(0.25) # Pausa maior devido a múltiplas requisições

    progress_bar.empty() # Limpa a barra de progresso
    
    # Mensagem de sucesso mais informativa
    historical_count = len([v for v in volume_data.values() if v.get('has_historical', False)])
    total_days = sum([v.get('days_analyzed', 0) for v in volume_data.values()])
    
    st.success(f"✅ Busca concluída! {len(prices)} cotações encontradas.")
    st.info(f"📊 Volume financeiro: {historical_count} ativos com dados históricos (total: {total_days} dias analisados)")
    st.info(f"📅 Período analisado: {start_date} até {end_date}")
    
    if not_found_tickers:
        st.warning(f"⚠️ Não foi possível encontrar cotações para: {', '.join(not_found_tickers)}")
        
    return prices, not_found_tickers, volume_data


def normalize_column_name(col_name):
    """Normaliza o nome da coluna para comparação (minúsculas, sem espaços extras)."""
    if pd.isna(col_name):  # Tratar casos onde o nome da coluna pode ser NaN
        return ""
    return str(col_name).strip().lower()

def find_and_select_target_columns(df, target_names_list):
    """
    Verifica se as colunas alvo (normalizadas) existem no DataFrame (com colunas normalizadas).
    Se sim, retorna um novo DataFrame contendo apenas essas colunas,
    renomeadas para os nomes originais em target_names_list.
    Caso contrário, retorna None.
    """
    df_cols_normalized_map = {normalize_column_name(col): col for col in df.columns}
    target_names_normalized_map = {normalize_column_name(name): name for name in target_names_list}

    found_original_col_names_for_selection = []
    rename_map_to_standard = {}

    all_targets_found = True
    for norm_target_name, original_target_name in target_names_normalized_map.items():
        if norm_target_name in df_cols_normalized_map:
            original_df_col_name = df_cols_normalized_map[norm_target_name]
            found_original_col_names_for_selection.append(original_df_col_name)
            rename_map_to_standard[original_df_col_name] = original_target_name
        else:
            all_targets_found = False
            break

    if all_targets_found:
        selected_df = df[found_original_col_names_for_selection]
        return selected_df.rename(columns=rename_map_to_standard)
    else:
        return None

def read_file_robustly(uploaded_file):
    """
    Lê um arquivo (Excel ou CSV) de forma robusta, tentando múltiplos encodings e separadores.
    Retorna DataFrame processado ou None se falhar.
    """
    file_name = uploaded_file.name
    content = uploaded_file.read()
    
    possible_encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    possible_separators_csv = [';', ',', '\t', None]
    max_skip_rows_to_try = 5
    
    # Reset do ponteiro do arquivo
    uploaded_file.seek(0)
    
    if file_name.endswith('.csv'):
        st.info(f"📄 Processando arquivo CSV: {file_name}")
        
        for encoding in possible_encodings:
            for sep in possible_separators_csv:
                for skiprows_val in range(max_skip_rows_to_try):
                    try:
                        # Cria um novo objeto BytesIO para cada tentativa
                        file_like_object = pd.io.common.BytesIO(content)
                        
                        temp_df = pd.read_csv(
                            file_like_object,
                            sep=sep,
                            encoding=encoding,
                            skiprows=skiprows_val,
                            skipinitialspace=True,
                            on_bad_lines='warn'
                        )
                        
                        df_selected_cols = find_and_select_target_columns(temp_df, TARGET_COLUMNS)
                        if df_selected_cols is not None:
                            st.success(f"✅ CSV lido com sucesso!")
                            st.info(f"📋 Parâmetros: encoding='{encoding}', separador='{sep if sep else 'auto'}', linhas puladas={skiprows_val}")
                            return df_selected_cols
                            
                    except Exception as e:
                        continue
        
        st.error(f"❌ Não foi possível ler o arquivo CSV '{file_name}' após várias tentativas.")
        st.error("Verifique se o arquivo contém as colunas 'Ativo' e 'Quantidade' e se não está corrompido.")
        return None
        
    elif file_name.endswith(('.xlsx', '.xls')):
        st.info(f"📊 Processando arquivo Excel: {file_name}")
        
        for skiprows_val in range(max_skip_rows_to_try):
            for engine_to_try in [None, 'openpyxl']:
                try:
                    # Cria um novo objeto BytesIO para cada tentativa
                    file_like_object = pd.io.common.BytesIO(content)
                    
                    temp_df = pd.read_excel(
                        file_like_object,
                        skiprows=skiprows_val,
                        engine=engine_to_try
                    )
                    
                    df_selected_cols = find_and_select_target_columns(temp_df, TARGET_COLUMNS)
                    if df_selected_cols is not None:
                        st.success(f"✅ Excel lido com sucesso!")
                        st.info(f"📋 Parâmetros: linhas puladas={skiprows_val}, engine='{engine_to_try if engine_to_try else 'auto'}'")
                        return df_selected_cols
                        
                except Exception as e:
                    continue
        
        st.error(f"❌ Não foi possível ler o arquivo Excel '{file_name}' após várias tentativas.")
        st.error("Verifique se o arquivo contém as colunas 'Ativo' e 'Quantidade' e se não está corrompido.")
        return None
    
    else:
        st.error(f"❌ Formato de arquivo não suportado: '{file_name}'. Apenas .csv, .xlsx e .xls são aceitos.")
        return None

# --- Abas do Dashboard ---

# Aba 1: Upload
with tab1:
    st.markdown("## 📁 Upload da Planilha de Ativos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📋 Instruções:
        1. 📤 Faça upload de uma planilha (Excel .xlsx/.xls ou CSV)
        2. 📊 O arquivo deve conter as colunas **'Ativo'** e **'Quantidade'**
        3. 🏢 Os ativos devem estar no formato da B3 (ex: PETR4, VALE3, ITUB4)
        4. 🔧 Para CSV, o sistema tentará automaticamente diferentes separadores
        """)
        
        uploaded_file = st.file_uploader(
            "📂 Escolha seu arquivo de dados",
            type=['xlsx', 'xls', 'csv'],
            help="Upload de arquivo Excel ou CSV com colunas 'Ativo' e 'Quantidade'"
        )
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4>📝 Exemplo de planilha:</h4>
        
        | Ativo | Quantidade |
        |-------|------------|
        | PETR4 | 100        |
        | VALE3 | 50         |
        | ITUB4 | 200        |
        
        <h4>📁 Formatos aceitos:</h4>
        • Excel: .xlsx, .xls<br>
        • CSV: .csv (separadores: ; , tab)
        </div>
        """, unsafe_allow_html=True)
    
    if uploaded_file is not None:
        df_uploaded = read_file_robustly(uploaded_file)
        if df_uploaded is not None:
            # Garante que a coluna 'Ativo' é string e 'Quantidade' é numérica
            try:
                df_uploaded['Ativo'] = df_uploaded['Ativo'].astype(str)
                df_uploaded['Quantidade'] = pd.to_numeric(df_uploaded['Quantidade'], errors='coerce')
                
                # Remove linhas onde a quantidade não pôde ser convertida para número OU é zero
                df_uploaded = df_uploaded.dropna(subset=['Quantidade'])
                df_uploaded = df_uploaded[df_uploaded['Quantidade'] > 0]  # Remove quantidades zero
                df_uploaded['Quantidade'] = df_uploaded['Quantidade'].astype(int)

                st.session_state.portfolio_df = df_uploaded
                
                # Detecta automaticamente o nome do portfólio baseado no arquivo
                portfolio_name = uploaded_file.name.replace('.csv', '').replace('.xlsx', '').replace('.xls', '').upper()
                
                # Se contém índices conhecidos, usa eles
                indices_conhecidos = ['IDIV', 'IFIX', 'IBOV', 'SMALL', 'IVVB', 'BOVA', 'SMAL']
                portfolio_detected = None
                for indice in indices_conhecidos:
                    if indice in portfolio_name:
                        portfolio_detected = indice
                        break
                
                if not portfolio_detected:
                    portfolio_detected = portfolio_name
                
                # Oferece opção para salvar automaticamente
                col_save1, col_save2 = st.columns([3, 1])
                with col_save1:
                    save_name = st.text_input("💾 Nome para salvar:", value=portfolio_detected, key="save_name")
                with col_save2:
                    st.write("")  # Espaçamento
                    st.write("")  # Espaçamento
                    if st.button("💾 Salvar Portfólio", type="primary"):
                        pm = st.session_state.portfolio_manager
                        metadata = {
                            'file_name': uploaded_file.name,
                            'file_size': uploaded_file.size,
                            'total_assets': len(df_uploaded),
                            'total_quantity': df_uploaded['Quantidade'].sum()
                        }
                        
                        if pm.save_portfolio(save_name, df_uploaded, metadata):
                            st.balloons()
                
                # Exibição melhorada do sucesso
                st.markdown("""
                <div class="success-box">
                    <h4>✅ Arquivo carregado com sucesso!</h4>
                    <p>📊 Dados processados e prontos para análise</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Métricas do arquivo carregado
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📈 Total de Ativos", len(df_uploaded))
                with col2:
                    st.metric("📊 Quantidade Total", f"{df_uploaded['Quantidade'].sum():,}")
                with col3:
                    st.metric("📋 Média por Ativo", f"{df_uploaded['Quantidade'].mean():.0f}")
                
                st.dataframe(st.session_state.portfolio_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"❌ Erro ao processar as colunas do arquivo: {e}")
                st.error("Verifique se a coluna 'Ativo' contém os tickers e 'Quantidade' contém números.")

# Aba 2: Dividendos (antiga Análise da Carteira)
with tab2:
    st.markdown("## 💰 Análise de Dividendos")

    if 'portfolio_df' not in st.session_state or st.session_state.portfolio_df.empty:
        st.warning("⚠️ Por favor, carregue sua carteira na aba '📤 Upload de Carteira' primeiro.")
    else:
        portfolio_df = st.session_state.portfolio_df.copy()

        # Remove ativos com quantidade zero antes do agrupamento
        portfolio_df = portfolio_df[portfolio_df['Quantidade'] > 0]

        # Agrupa por ativo, somando as quantidades
        portfolio_df = portfolio_df.groupby('Ativo')['Quantidade'].sum().reset_index()

        # Adiciona o sufixo .SA se não estiver presente (necessário para a API)
        portfolio_df['Ativo_API'] = portfolio_df['Ativo'].apply(
            lambda x: f"{x}.SA" if not str(x).upper().endswith('.SA') else str(x)
        )

        tickers_list = portfolio_df['Ativo_API'].unique().tolist()
        
        # --- BUSCA DE DADOS ---
        st.markdown("### 🚀 Escolha a Fonte de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            brapi_button = st.button("📊 Buscar via brapi.dev", key="brapi_button", type="primary", use_container_width=True)
        
        with col2:
            yfinance_button = st.button("📈 Buscar via yfinance", key="yfinance_button", type="secondary", use_container_width=True)
        
        # Processamento dos botões
        if brapi_button:
            if not BRAPI_API_KEY or BRAPI_API_KEY == "COLE_SUA_CHAVE_AQUI":
                st.error("❌ Chave da API da brapi.dev não configurada. Por favor, insira no código.")
            else:
                # Mapeamento entre ticker da API (com .SA) e ticker original (sem .SA)
                ticker_map_api_to_original = pd.Series(portfolio_df.Ativo.values, index=portfolio_df.Ativo_API).to_dict()

                prices, not_found_api, volume_data = get_brapi_quotes(tickers_list, BRAPI_API_KEY)
                st.session_state.data_source = "brapi.dev"
                
                if prices:
                    # Mapeia os preços encontrados de volta para o DataFrame
                    portfolio_df['Preço'] = portfolio_df['Ativo_API'].map(prices)
                    
                    # Para ativos não encontrados, o preço será NaN
                    df_found = portfolio_df.dropna(subset=['Preço']).copy()
                    
                    # Identifica os ativos não encontrados pelo nome original
                    not_found_original = []
                    for api_ticker in not_found_api:
                        if api_ticker in ticker_map_api_to_original:
                            not_found_original.append(ticker_map_api_to_original[api_ticker])
                    
                    df_not_found = portfolio_df[portfolio_df['Ativo'].isin(not_found_original)].copy()

                    if not df_found.empty:
                        # Cálculos
                        df_found['Valor Total'] = df_found['Quantidade'] * df_found['Preço']
                        total_portfolio_value = df_found['Valor Total'].sum()
                        df_found['Peso (%)'] = (df_found['Valor Total'] / total_portfolio_value) * 100
                        
                        # --- MÉTRICAS PRINCIPAIS ---
                        st.markdown(f"### 💰 Resumo da Carteira (Fonte: brapi.dev)")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "💼 Valor Total", 
                                f"R$ {total_portfolio_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                                delta=None
                            )
                        with col2:
                            st.metric("📈 Ativos Válidos", len(df_found))
                        with col3:
                            st.metric("📊 Quantidade Total", f"{df_found['Quantidade'].sum():,}".replace(',', '.'))
                        with col4:
                            maior_posicao = df_found.loc[df_found['Valor Total'].idxmax(), 'Ativo']
                            st.metric("🏆 Maior Posição", maior_posicao)
                        
                        # --- EXIBIÇÃO DA TABELA ---
                        st.markdown("### 📋 Composição da Carteira")
                        
                        # Formata as colunas para exibição
                        display_df = df_found[['Ativo', 'Quantidade', 'Preço', 'Valor Total', 'Peso (%)']].copy()
                        
                        # Formatação personalizada para o padrão brasileiro
                        display_df['Quantidade'] = display_df['Quantidade'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                        display_df['Preço'] = display_df['Preço'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        display_df['Valor Total'] = display_df['Valor Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                        display_df['Peso (%)'] = display_df['Peso (%)'].map('{:.2f}%'.format).str.replace('.', ',')

                        # Ordena por Peso (%) do maior para o menor e remove o índice
                        display_df_sorted = display_df.sort_values(by="Peso (%)", ascending=False, key=lambda x: x.str.replace('%', '').str.replace(',', '.').astype(float))
                        st.dataframe(display_df_sorted, use_container_width=True, hide_index=True)
                        
                        # Salva dados na sessão
                        st.session_state.analyzed_df = df_found.copy()
                        st.session_state.total_value = total_portfolio_value
                        st.session_state.volume_data = volume_data
                        st.session_state.ticker_map = ticker_map_api_to_original
                        
                                            # --- SEÇÃO DE GRÁFICOS ---
                    st.markdown("---")
                    st.markdown("## 📈 Resumo Gráfico da Carteira")
                    
                    # Métricas principais dos gráficos
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.metric(
                            "💼 Valor Total do Portfólio", 
                            f"R$ {total_portfolio_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        )
                    with col2:
                        st.metric("📊 Número de Ativos", len(df_found))
                    
                    # Gráficos lado a lado
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de Pizza
                        fig_pie = px.pie(
                            df_found,
                            names='Ativo',
                            values='Valor Total',
                            title='🥧 Distribuição da Carteira por Ativo',
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_pie.update_traces(
                            textposition='inside', 
                            textinfo='percent+label',
                            hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Peso: %{percent}<extra></extra>"
                        )
                        fig_pie.update_layout(
                            font=dict(size=12),
                            showlegend=True,
                            legend=dict(orientation="v", yanchor="middle", y=0.5)
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Gráfico de Barras - Top 10
                        top_10 = df_found.nlargest(10, 'Valor Total')
                        fig_bar = px.bar(
                            top_10,
                            x='Valor Total',
                            y='Ativo',
                            orientation='h',
                            title='📊 Top 10 Maiores Posições',
                            color='Valor Total',
                            color_continuous_scale='Viridis'
                        )
                        fig_bar.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            font=dict(size=12),
                            showlegend=False
                        )
                        fig_bar.update_traces(
                            hovertemplate="<b>%{y}</b><br>Valor: R$ %{x:,.2f}<extra></extra>"
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # --- SEÇÃO DE VOLUME ---
                    st.markdown("---")
                    st.markdown("## 💰 Análise de Volume Financeiro")
                    st.info(f"📊 Dados de volume obtidos via: **yfinance**")
                    
                    if volume_data:
                        # Prepara dados de volume para análise
                        volume_analysis = []
                        for ativo_api in df_found['Ativo_API']:
                            ativo_original = ticker_map_api_to_original.get(ativo_api, ativo_api.replace('.SA', ''))
                            if ativo_api in volume_data:
                                vol_data = volume_data[ativo_api]
                                has_hist = vol_data.get('has_historical', False)
                                days_analyzed = vol_data.get('days_analyzed', 0)
                                
                                # Calcula relação apenas se tiver dados históricos válidos
                                if has_hist and vol_data['median_volume'] > 0:
                                    relacao = (vol_data['current_volume'] / vol_data['median_volume'] * 100)
                                else:
                                    relacao = 100  # Se não tem histórico, considera 100% (neutro)
                                
                                volume_analysis.append({
                                    'Ativo': ativo_original,
                                    'Volume Atual': vol_data['current_volume'],
                                    'Mediana (até 45d)': vol_data['median_volume'],
                                    'Relação (%)': relacao,
                                    'Dias Analisados': days_analyzed,
                                    'Tem Histórico': '✅' if has_hist else '❌'
                                })
                        
                        df_volume = pd.DataFrame(volume_analysis)
                        
                        if not df_volume.empty:
                            # Métricas de volume
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                volume_total_atual = df_volume['Volume Atual'].sum()
                                st.metric("💰 Volume Financeiro Atual", f"R$ {volume_total_atual/1000000:,.1f}M".replace(',', '.'))
                            
                            with col2:
                                volume_mediana_total = df_volume['Mediana (até 45d)'].sum()
                                st.metric("📊 Mediana Financeira", f"R$ {volume_mediana_total/1000000:,.1f}M".replace(',', '.'))
                            
                            with col3:
                                # Apenas para ativos com histórico válido
                                df_com_historico = df_volume[df_volume['Tem Histórico'] == '✅']
                                if not df_com_historico.empty:
                                    relacao_media = df_com_historico['Relação (%)'].mean()
                                    st.metric("📈 Relação Média", f"{relacao_media:.1f}%", 
                                             delta=f"{relacao_media-100:.1f}% vs mediana")
                                else:
                                    st.metric("📈 Relação Média", "N/A", delta="Sem dados históricos")
                            
                            with col4:
                                ativos_com_historico = len(df_com_historico)
                                st.metric("📚 Com Dados Históricos", f"{ativos_com_historico}/{len(df_volume)}")
                            
                            # Tabela de volume
                            st.markdown("### 📋 Detalhamento por Ativo")
                            
                            # Formatação da tabela de volume
                            display_volume_df = df_volume.copy()
                            display_volume_df['Volume Atual'] = display_volume_df['Volume Atual'].apply(lambda x: f"R$ {x/1000000:,.2f}M".replace(',', '.'))
                            display_volume_df['Mediana (até 45d)'] = display_volume_df['Mediana (até 45d)'].apply(lambda x: f"R$ {x/1000000:,.2f}M".replace(',', '.'))
                            display_volume_df['Relação (%)'] = display_volume_df['Relação (%)'].apply(lambda x: f"{x:.1f}%")
                            
                            # Ordena pela relação percentual
                            display_volume_df_sorted = display_volume_df.sort_values(by="Relação (%)", ascending=False, key=lambda x: x.str.replace('%', '').astype(float))
                            st.dataframe(display_volume_df_sorted, use_container_width=True, hide_index=True)
                            
                            # Gráficos de volume financeiro
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Gráfico de barras - Volume atual vs Mediana
                                fig_volume_comparison = go.Figure()
                                
                                fig_volume_comparison.add_trace(go.Bar(
                                    name='Volume Atual',
                                    x=df_volume['Ativo'],
                                    y=df_volume['Volume Atual']/1000000,  # Em milhões
                                    marker_color='lightblue'
                                ))
                                
                                fig_volume_comparison.add_trace(go.Bar(
                                    name='Mediana (45d)',
                                    x=df_volume['Ativo'],
                                    y=df_volume['Mediana (até 45d)']/1000000,  # Em milhões
                                    marker_color='orange'
                                ))
                                
                                fig_volume_comparison.update_layout(
                                    title='💰 Volume Financeiro: Atual vs Mediana (R$ Milhões)',
                                    xaxis_title='Ativos',
                                    yaxis_title='Volume Financeiro (R$ Milhões)',
                                    barmode='group',
                                    font=dict(size=10)
                                )
                                
                                st.plotly_chart(fig_volume_comparison, use_container_width=True)
                            
                            with col2:
                                # Novo gráfico: Dias para zerar posição
                                dias_para_zerar = []
                                for index, row in df_volume.iterrows():
                                    ativo = row['Ativo']
                                    volume_mediana = row['Mediana (até 45d)']
                                    
                                    # Pega o valor total da posição do ativo
                                    valor_posicao = df_found[df_found['Ativo'] == ativo]['Valor Total'].iloc[0]
                                    
                                    # Calcula 20% da mediana de 45 dias
                                    volume_mediana_20pct = volume_mediana * 0.20
                                    
                                    # Calcula dias para zerar (valor da posição / 20% da mediana)
                                    if volume_mediana_20pct > 0:
                                        dias_para_zerar_posicao = valor_posicao / volume_mediana_20pct
                                    else:
                                        dias_para_zerar_posicao = float('inf')
                                    
                                    dias_para_zerar.append({
                                        'Ativo': ativo,
                                        'Dias para Zerar': min(dias_para_zerar_posicao, 999)  # Limita a 999 dias para visualização
                                    })
                                
                                df_dias = pd.DataFrame(dias_para_zerar)
                                
                                # Gráfico de barras - Dias para zerar posição
                                fig_dias = px.bar(
                                    df_dias,
                                    x='Ativo',
                                    y='Dias para Zerar',
                                    title='⏱️ Dias para Zerar Posição (20% da Mediana)',
                                    color='Dias para Zerar',
                                    color_continuous_scale='RdYlBu_r'
                                )
                                
                                fig_dias.update_layout(
                                    xaxis_title='Ativos',
                                    yaxis_title='Dias',
                                    font=dict(size=10),
                                    showlegend=False
                                )
                                
                                fig_dias.update_traces(
                                    hovertemplate="<b>%{x}</b><br>Dias para zerar: %{y:.1f}<extra></extra>"
                                )
                                
                                st.plotly_chart(fig_dias, use_container_width=True)
                        else:
                            st.warning("⚠️ Não foi possível processar os dados de volume.")
                    else:
                        st.warning("⚠️ Dados de volume não disponíveis.")
                        
                    if not df_not_found.empty:
                        st.markdown("### ⚠️ Ativos Não Encontrados")
                        st.warning(f"Não foi possível obter a cotação para os seguintes ativos:")
                        st.dataframe(df_not_found[['Ativo', 'Quantidade']], use_container_width=True, hide_index=True)
                else:
                    st.error("❌ Não foi possível obter nenhuma cotação. Verifique os tickers ou a API.")
        
        elif yfinance_button:
            prices, not_found, volume_data = get_yfinance_quotes(tickers_list)
            st.session_state.data_source = "yfinance"
            
            # Para yfinance, o mapeamento é direto
            ticker_map_api_to_original = {ticker: ticker.replace('.SA', '') for ticker in tickers_list}
            
            if prices:
                # Mapeia os preços encontrados de volta para o DataFrame
                portfolio_df['Preço'] = portfolio_df['Ativo_API'].map(prices)
                
                # Para ativos não encontrados, o preço será NaN
                df_found = portfolio_df.dropna(subset=['Preço']).copy()
                
                # Identifica os ativos não encontrados pelo nome original
                not_found_original = []
                for api_ticker in not_found:
                    if api_ticker in ticker_map_api_to_original:
                        not_found_original.append(ticker_map_api_to_original[api_ticker])
                
                df_not_found = portfolio_df[portfolio_df['Ativo'].isin(not_found_original)].copy()

                if not df_found.empty:
                    # Cálculos
                    df_found['Valor Total'] = df_found['Quantidade'] * df_found['Preço']
                    total_portfolio_value = df_found['Valor Total'].sum()
                    df_found['Peso (%)'] = (df_found['Valor Total'] / total_portfolio_value) * 100
                    
                    # --- MÉTRICAS PRINCIPAIS ---
                    st.markdown(f"### 💰 Resumo da Carteira (Fonte: yfinance)")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "💼 Valor Total", 
                            f"R$ {total_portfolio_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                            delta=None
                        )
                    with col2:
                        st.metric("📈 Ativos Válidos", len(df_found))
                    with col3:
                        st.metric("📊 Quantidade Total", f"{df_found['Quantidade'].sum():,}".replace(',', '.'))
                    with col4:
                        maior_posicao = df_found.loc[df_found['Valor Total'].idxmax(), 'Ativo']
                        st.metric("🏆 Maior Posição", maior_posicao)
                    
                    # --- EXIBIÇÃO DA TABELA ---
                    st.markdown("### 📋 Composição da Carteira")
                    
                    # Formata as colunas para exibição
                    display_df = df_found[['Ativo', 'Quantidade', 'Preço', 'Valor Total', 'Peso (%)']].copy()
                    
                    # Formatação personalizada para o padrão brasileiro
                    display_df['Quantidade'] = display_df['Quantidade'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
                    display_df['Preço'] = display_df['Preço'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    display_df['Valor Total'] = display_df['Valor Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    display_df['Peso (%)'] = display_df['Peso (%)'].map('{:.2f}%'.format).str.replace('.', ',')

                    # Ordena por Peso (%) do maior para o menor e remove o índice
                    display_df_sorted = display_df.sort_values(by="Peso (%)", ascending=False, key=lambda x: x.str.replace('%', '').str.replace(',', '.').astype(float))
                    st.dataframe(display_df_sorted, use_container_width=True, hide_index=True)
                    
                    # Salva dados na sessão
                    st.session_state.analyzed_df = df_found.copy()
                    st.session_state.total_value = total_portfolio_value
                    st.session_state.volume_data = volume_data
                    st.session_state.ticker_map = ticker_map_api_to_original
                    
                    # --- SEÇÃO DE GRÁFICOS ---
                    st.markdown("---")
                    st.markdown("## 📈 Resumo Gráfico da Carteira")
                    
                    # Métricas principais dos gráficos
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.metric(
                            "💼 Valor Total do Portfólio", 
                            f"R$ {total_portfolio_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                        )
                    with col2:
                        st.metric("📊 Número de Ativos", len(df_found))
                    
                    # Gráficos lado a lado
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de Pizza
                        fig_pie = px.pie(
                            df_found,
                            names='Ativo',
                            values='Valor Total',
                            title='🥧 Distribuição da Carteira por Ativo',
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_pie.update_traces(
                            textposition='inside', 
                            textinfo='percent+label',
                            hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Peso: %{percent}<extra></extra>"
                        )
                        fig_pie.update_layout(
                            font=dict(size=12),
                            showlegend=True,
                            legend=dict(orientation="v", yanchor="middle", y=0.5)
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    with col2:
                        # Gráfico de Barras - Top 10
                        top_10 = df_found.nlargest(10, 'Valor Total')
                        fig_bar = px.bar(
                            top_10,
                            x='Valor Total',
                            y='Ativo',
                            orientation='h',
                            title='📊 Top 10 Maiores Posições',
                            color='Valor Total',
                            color_continuous_scale='Viridis'
                        )
                        fig_bar.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            font=dict(size=12),
                            showlegend=False
                        )
                        fig_bar.update_traces(
                            hovertemplate="<b>%{y}</b><br>Valor: R$ %{x:,.2f}<extra></extra>"
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    
                    # --- SEÇÃO DE VOLUME ---
                    st.markdown("---")
                    st.markdown("## 💰 Análise de Volume Financeiro")
                    st.info(f"📊 Dados de volume obtidos via: **yfinance**")
                    
                    if volume_data:
                        # Prepara dados de volume para análise
                        volume_analysis = []
                        for ativo_api in df_found['Ativo_API']:
                            ativo_original = ticker_map_api_to_original.get(ativo_api, ativo_api.replace('.SA', ''))
                            if ativo_api in volume_data:
                                vol_data = volume_data[ativo_api]
                                has_hist = vol_data.get('has_historical', False)
                                days_analyzed = vol_data.get('days_analyzed', 0)
                                
                                # Calcula relação apenas se tiver dados históricos válidos
                                if has_hist and vol_data['median_volume'] > 0:
                                    relacao = (vol_data['current_volume'] / vol_data['median_volume'] * 100)
                                else:
                                    relacao = 100  # Se não tem histórico, considera 100% (neutro)
                                
                                volume_analysis.append({
                                    'Ativo': ativo_original,
                                    'Volume Atual': vol_data['current_volume'],
                                    'Mediana (até 45d)': vol_data['median_volume'],
                                    'Relação (%)': relacao,
                                    'Dias Analisados': days_analyzed,
                                    'Tem Histórico': '✅' if has_hist else '❌'
                                })
                        
                        df_volume = pd.DataFrame(volume_analysis)
                        
                        if not df_volume.empty:
                            # Métricas de volume
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                volume_total_atual = df_volume['Volume Atual'].sum()
                                st.metric("💰 Volume Financeiro Atual", f"R$ {volume_total_atual/1000000:,.1f}M".replace(',', '.'))
                            
                            with col2:
                                volume_mediana_total = df_volume['Mediana (até 45d)'].sum()
                                st.metric("📊 Mediana Financeira", f"R$ {volume_mediana_total/1000000:,.1f}M".replace(',', '.'))
                            
                            with col3:
                                # Apenas para ativos com histórico válido
                                df_com_historico = df_volume[df_volume['Tem Histórico'] == '✅']
                                if not df_com_historico.empty:
                                    relacao_media = df_com_historico['Relação (%)'].mean()
                                    st.metric("📈 Relação Média", f"{relacao_media:.1f}%", 
                                             delta=f"{relacao_media-100:.1f}% vs mediana")
                                else:
                                    st.metric("📈 Relação Média", "N/A", delta="Sem dados históricos")
                            
                            with col4:
                                ativos_com_historico = len(df_com_historico)
                                st.metric("📚 Com Dados Históricos", f"{ativos_com_historico}/{len(df_volume)}")
                            
                            # Tabela de volume
                            st.markdown("### 📋 Detalhamento por Ativo")
                            
                            # Formatação da tabela de volume
                            display_volume_df = df_volume.copy()
                            display_volume_df['Volume Atual'] = display_volume_df['Volume Atual'].apply(lambda x: f"R$ {x/1000000:,.2f}M".replace(',', '.'))
                            display_volume_df['Mediana (até 45d)'] = display_volume_df['Mediana (até 45d)'].apply(lambda x: f"R$ {x/1000000:,.2f}M".replace(',', '.'))
                            display_volume_df['Relação (%)'] = display_volume_df['Relação (%)'].apply(lambda x: f"{x:.1f}%")
                            
                            # Ordena pela relação percentual
                            display_volume_df_sorted = display_volume_df.sort_values(by="Relação (%)", ascending=False, key=lambda x: x.str.replace('%', '').astype(float))
                            st.dataframe(display_volume_df_sorted, use_container_width=True, hide_index=True)
                            
                            # Gráficos de volume financeiro
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Gráfico de barras - Volume atual vs Mediana
                                fig_volume_comparison = go.Figure()
                                
                                fig_volume_comparison.add_trace(go.Bar(
                                    name='Volume Atual',
                                    x=df_volume['Ativo'],
                                    y=df_volume['Volume Atual']/1000000,  # Em milhões
                                    marker_color='lightblue'
                                ))
                                
                                fig_volume_comparison.add_trace(go.Bar(
                                    name='Mediana (45d)',
                                    x=df_volume['Ativo'],
                                    y=df_volume['Mediana (até 45d)']/1000000,  # Em milhões
                                    marker_color='orange'
                                ))
                                
                                fig_volume_comparison.update_layout(
                                    title='💰 Volume Financeiro: Atual vs Mediana (R$ Milhões)',
                                    xaxis_title='Ativos',
                                    yaxis_title='Volume Financeiro (R$ Milhões)',
                                    barmode='group',
                                    font=dict(size=10)
                                )
                                
                                st.plotly_chart(fig_volume_comparison, use_container_width=True)
                            
                            with col2:
                                # Novo gráfico: Dias para zerar posição
                                dias_para_zerar = []
                                for index, row in df_volume.iterrows():
                                    ativo = row['Ativo']
                                    volume_mediana = row['Mediana (até 45d)']
                                    
                                    # Pega o valor total da posição do ativo
                                    valor_posicao = df_found[df_found['Ativo'] == ativo]['Valor Total'].iloc[0]
                                    
                                    # Calcula 20% da mediana de 45 dias
                                    volume_mediana_20pct = volume_mediana * 0.20
                                    
                                    # Calcula dias para zerar (valor da posição / 20% da mediana)
                                    if volume_mediana_20pct > 0:
                                        dias_para_zerar_posicao = valor_posicao / volume_mediana_20pct
                                    else:
                                        dias_para_zerar_posicao = float('inf')
                                    
                                    dias_para_zerar.append({
                                        'Ativo': ativo,
                                        'Dias para Zerar': min(dias_para_zerar_posicao, 999)  # Limita a 999 dias para visualização
                                    })
                                
                                df_dias = pd.DataFrame(dias_para_zerar)
                                
                                # Gráfico de barras - Dias para zerar posição
                                fig_dias = px.bar(
                                    df_dias,
                                    x='Ativo',
                                    y='Dias para Zerar',
                                    title='⏱️ Dias para Zerar Posição (20% da Mediana)',
                                    color='Dias para Zerar',
                                    color_continuous_scale='RdYlBu_r'
                                )
                                
                                fig_dias.update_layout(
                                    xaxis_title='Ativos',
                                    yaxis_title='Dias',
                                    font=dict(size=10),
                                    showlegend=False
                                )
                                
                                fig_dias.update_traces(
                                    hovertemplate="<b>%{x}</b><br>Dias para zerar: %{y:.1f}<extra></extra>"
                                )
                                
                                st.plotly_chart(fig_dias, use_container_width=True)
                        else:
                            st.warning("⚠️ Não foi possível processar os dados de volume.")
                    else:
                        st.warning("⚠️ Dados de volume não disponíveis.")
                    
                if not df_not_found.empty:
                    st.markdown("### ⚠️ Ativos Não Encontrados")
                    st.warning(f"Não foi possível obter a cotação para os seguintes ativos:")
                    st.dataframe(df_not_found[['Ativo', 'Quantidade']], use_container_width=True, hide_index=True)
            else:
                st.error("❌ Não foi possível obter nenhuma cotação via yfinance.")

# Aba 3: Portfólios Salvos
with tab3:
    st.markdown("## 📚 Gerenciamento de Portfólios Salvos")
    
    pm = st.session_state.portfolio_manager
    
    # Lista de portfólios salvos
    portfolio_names = pm.get_portfolio_names()
    
    if not portfolio_names:
        st.info("📝 Nenhum portfólio salvo ainda. Faça upload de uma planilha na primeira aba e salve!")
        st.markdown("""
        ### 🚀 Como usar:
        1. **Upload**: Vá para a aba "📤 Upload de Carteira"
        2. **Carregue**: Selecione seu arquivo Excel/CSV
        3. **Salve**: Use o botão "💾 Salvar Portfólio"
        4. **Gerencie**: Volte aqui para carregar, comparar ou excluir
        """)
    else:
        # Seção de carregamento rápido
        st.markdown("### 🚀 Carregamento Rápido")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_portfolio = st.selectbox(
                "📁 Selecione um portfólio:",
                options=portfolio_names,
                key="portfolio_selector"
            )
        
        with col2:
            if st.button("📂 Carregar", type="primary", use_container_width=True):
                if selected_portfolio:
                    df_loaded = pm.load_portfolio(selected_portfolio)
                    if df_loaded is not None:
                        st.session_state.portfolio_df = df_loaded
                        st.success(f"✅ Portfólio '{selected_portfolio}' carregado!")
                        st.balloons()
                    else:
                        st.error("❌ Erro ao carregar portfólio")
        
        with col3:
            if st.button("🗑️ Excluir", type="secondary", use_container_width=True):
                if selected_portfolio:
                    if st.confirm(f"Tem certeza que deseja excluir '{selected_portfolio}'?"):
                        if pm.delete_portfolio(selected_portfolio):
                            st.rerun()
        
        st.markdown("---")
        
        # Histórico detalhado
        st.markdown("### 📈 Histórico de Versões")
        
        for portfolio_name in portfolio_names:
            with st.expander(f"📊 {portfolio_name}", expanded=False):
                history = pm.get_portfolio_history(portfolio_name)
                
                if history:
                    # Métricas do portfólio
                    latest = history[0]
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📋 Versões", len(history))
                    with col2:
                        st.metric("📈 Ativos", latest['assets_count'])
                    with col3:
                        st.metric("📊 Quantidade", f"{latest['total_quantity']:,}".replace(',', '.'))
                    with col4:
                        st.metric("📅 Última Atualização", latest['date'].split(' ')[0])
                    
                    # Tabela de histórico
                    history_df = pd.DataFrame(history)
                    history_df['date'] = pd.to_datetime(history_df['date']).dt.strftime('%d/%m/%Y %H:%M')
                    history_df = history_df.rename(columns={
                        'version': 'Versão',
                        'date': 'Data/Hora',
                        'assets_count': 'Ativos',
                        'total_quantity': 'Quantidade Total'
                    })
                    
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
                    
                    # Botões de ação
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"📂 Carregar {portfolio_name}", key=f"load_{portfolio_name}"):
                            df_loaded = pm.load_portfolio(portfolio_name)
                            if df_loaded is not None:
                                st.session_state.portfolio_df = df_loaded
                                st.success(f"✅ '{portfolio_name}' carregado!")
                                st.rerun()
                    
                    with col2:
                        if st.button(f"📋 Ver Dados", key=f"view_{portfolio_name}"):
                            df_view = pm.load_portfolio(portfolio_name)
                            if df_view is not None:
                                st.markdown(f"#### 📊 Dados de '{portfolio_name}':")
                                st.dataframe(df_view, use_container_width=True, hide_index=True)
                    
                    with col3:
                        if len(history) > 1:
                            if st.button(f"🔍 Comparar Versões", key=f"compare_{portfolio_name}"):
                                st.markdown(f"#### 🔍 Comparação de Versões - {portfolio_name}")
                                
                                # Selectboxes para escolher versões
                                col_v1, col_v2 = st.columns(2)
                                with col_v1:
                                    version1 = st.selectbox("Versão 1:", [h['version'] for h in history], key=f"v1_{portfolio_name}")
                                with col_v2:
                                    version2 = st.selectbox("Versão 2:", [h['version'] for h in history], key=f"v2_{portfolio_name}")
                                
                                if version1 != version2:
                                    changes = pm.compare_portfolios(portfolio_name, version1, version2)
                                    if changes:
                                        col_add, col_rem, col_mod = st.columns(3)
                                        
                                        with col_add:
                                            if changes['added']:
                                                st.markdown("**➕ Adicionados:**")
                                                for asset in changes['added']:
                                                    st.write(f"• {asset}")
                                        
                                        with col_rem:
                                            if changes['removed']:
                                                st.markdown("**➖ Removidos:**")
                                                for asset in changes['removed']:
                                                    st.write(f"• {asset}")
                                        
                                        with col_mod:
                                            if changes['modified']:
                                                st.markdown("**✏️ Modificados:**")
                                                for mod in changes['modified']:
                                                    st.write(f"• {mod['asset']}: {mod['old_qty']} → {mod['new_qty']}")
                else:
                    st.warning("⚠️ Histórico não disponível")
        
        # Status da conexão
        st.markdown("---")
        st.markdown("### 🔌 Status da Conexão")
        
        try:
            # Testa a conexão
            test_portfolios = pm.get_portfolio_names()
            if test_portfolios is not None:
                st.success("🟢 Conectado ao Google Sheets")
                st.info(f"📊 {len(portfolio_names)} portfólio(s) encontrado(s)")
            else:
                st.error("🔴 Erro de conexão com Google Sheets")
        except Exception as e:
            st.error(f"🔴 Erro de conexão: {e}")
            st.markdown("""
            #### 🔧 Possíveis soluções:
            1. Verifique as credenciais no painel do Streamlit Cloud
            2. Confirme se a API do Google Sheets está habilitada
            3. Verifique se o arquivo de credenciais está correto
            """)