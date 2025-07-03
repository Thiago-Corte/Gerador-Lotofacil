import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import requests
import io

# --- Configuração da Página e Constantes ---
st.set_page_config(page_title="Analisador Lotofácil Pro", page_icon="🚀", layout="wide")
MOLDURA_DEZENAS = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS ---

@st.cache_data(ttl=3600)
def carregar_dados_da_web():
    """
    Carrega os dados históricos da Lotofácil usando o arquivo Excel do repositório como base
    e busca o último resultado na API da Caixa para complementar.
    """
    df_completo = None
    try:
        df_hist = pd.read_excel("Lotofácil.xlsx")
        df_hist = df_hist.iloc[:, :17]
        df_hist.columns = ['Concurso', 'Data Sorteio', 'Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15']
        df_completo = df_hist

    except FileNotFoundError:
        st.error("ERRO CRÍTICO: O arquivo 'Lotofácil.xlsx' não foi encontrado no seu repositório do GitHub. Por favor, faça o upload do arquivo.")
        return None
        
    try:
        url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        
        ultimo_resultado = {
            'Concurso': data.get('numero'), 'Data Sorteio': data.get('dataApuracao'),
            **{f'Bola{i+1}': int(dezena) for i, dezena in enumerate(data.get('listaDezenas', []))}
        }
        df_ultimo = pd.DataFrame([ultimo_resultado])
        
        if not df_completo['Concurso'].isin([df_ultimo['Concurso'][0]]).any():
            df_completo = pd.concat([df_completo, df_ultimo], ignore_index=True)

    except Exception as e:
        st.warning(f"Aviso: Não foi possível buscar o último resultado da API. Usando apenas os dados do seu arquivo Excel.")

    for col in df_completo.columns:
        if 'Bola' in col or 'Concurso' in col:
            df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce')
    
    return df_completo.sort_values(by='Concurso').reset_index(drop=True)

@st.cache_data
def extrair_numeros(_df):
    bola_cols = [col for col in _df.columns if col.startswith('Bola')]
    return _df[bola_cols].dropna().astype(int).values.tolist()

@st.cache_data
def analisar_frequencia_e_atraso(_todos_os_sorteios):
    frequencia = Counter(itertools.chain(*_todos_os_sorteios))
    atraso = {}
    total_concursos = len(_todos_os_sorteios)
    for dezena in range(1, 26):
        try:
            ultimo_sorteio_idx_geral = max(i for i, sorteio in enumerate(_todos_os_sorteios) if dezena in sorteio)
            atraso[dezena] = total_concursos - 1 - ultimo_sorteio_idx_geral
        except ValueError:
            atraso[dezena] = total_concursos
    return frequencia, atraso

@st.cache_data
def encontrar_combinacoes_frequentes(_numeros_sorteados, tamanho):
    todas_as_combinacoes = itertools.chain.from_iterable(itertools.combinations(sorteio, tamanho) for sorteio in _numeros_sorteados)
    return Counter(todas_as_combinacoes).most_common(15)

@st.cache_data
def sugerir_universo_estrategico(_df, _todos_os_sorteios, num_sorteios=1000, tamanho_universo=19):
    df_recente = _df.tail(num_sorteios)
    numeros_recentes = extrair_numeros(df_recente)
    frequencia_recente = Counter(itertools.chain(*numeros_recentes))
    _, atraso_geral = analisar_frequencia_e_atraso(_todos_os_sorteios)
    scores = {}
    max_freq = max(frequencia_recente.values()) if frequencia_recente else 1
    max_atraso = max(atraso_geral.values()) if atraso_geral else 1
    for dezena in range(1, 26):
        score_freq = frequencia_recente.get(dezena, 0) / max_freq
        score_atraso = atraso_geral.get(dezena, 0) / max_atraso
        scores[dezena] = (0.6 * score_freq) + (0.4 * score_atraso)
    dezenas_ordenadas = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    universo_sugerido = [dezena for dezena, score in dezenas_ordenadas[:tamanho_universo]]
    return sorted(universo_sugerido)

# --- NOVA FUNÇÃO: BACKTESTING ---
@st.cache_data
def executar_backtest(_df, n_concursos, min_rep, max_rep, min_imp, max_imp, min_mold, max_mold):
    sorteios_teste = _df.tail(n_concursos).copy()
    sorteios_alinhados = []
    
    for index in range(1, len(sorteios_teste)):
        concurso_atual = sorteios_teste.iloc[index]
        concurso_anterior = sorteios_teste.iloc[index - 1]
        
        dezenas_atuais = set(concurso_atual[[f'Bola{i}' for i in range(1,16)]])
        dezenas_anteriores = set(concurso_anterior[[f'Bola{i}' for i in range(1,16)]])
        
        # Calcula as métricas do concurso atual
        qtd_repetidas = len(dezenas_atuais.intersection(dezenas_anteriores))
        qtd_impares = len([n for n in dezenas_atuais if n % 2 != 0])
        qtd_moldura = len(dezenas_atuais.intersection(MOLDURA_DEZENAS))
        
        # Verifica se o resultado do concurso bate com a estratégia
        if (min_rep <= qtd_repetidas <= max_rep) and \
           (min_imp <= qtd_impares <= max_imp) and \
           (min_mold <= qtd_moldura <= max_mold):
            sorteios_alinhados.append(int(concurso_atual['Concurso']))
            
    return sorteios_alinhados

# --- INÍCIO DA APLICAÇÃO ---
st.title("🚀 Analisador Lotofácil Pro")
df_resultados = carregar_dados_da_web()

if 'sugeridas' not in st.session_state: st.session_state.sugeridas = ""

if df_resultados is not None and not df_resultados.empty:
    todos_os_sorteios = extrair_numeros(df_resultados)
    ultimo_concurso_num = int(df_resultados.iloc[-1]['Concurso'])
    
    st.success(f"**Dados carregados com sucesso!** Último concurso na base: **{ultimo_concurso_num}**.")
    
    tab_gerador, tab_analise, tab_conferidor, tab_backtest = st.tabs(["🎯 Gerador de Jogos", "📊 Análise de Tendências", "✅ Conferidor de Jogos", "🔬 Backtesting"])

    with tab_gerador:
        st.header("Gerador de Jogos com Filtros Estratégicos")
        st.sidebar.header("Defina sua Estratégia de Geração")
        st.sidebar.subheader("✨ Sugestão Inteligente")
        if st.sidebar.button("Sugerir Universo (Análise de 1000 Sorteios)"):
            with st.spinner("Analisando 1000 sorteios..."):
                universo = sugerir_universo_estrategico(df_resultados, todos_os_sorteios)
                st.session_state.sugeridas = ", ".join(map(str, universo))
        dezenas_str = st.sidebar.text_area("Seu universo de dezenas (separadas por vírgula):", value=st.session_state.sugeridas, height=150)
        st.sidebar.subheader("Filtros:")
        min_rep, max_rep = st.sidebar.slider("Qtd. Dezenas Repetidas:", 0, 15, (8, 10), key='slider_rep_gerador')
        min_imp, max_imp = st.sidebar.slider("Qtd. Dezenas Ímpares:", 0, 15, (7, 9), key='slider_imp_gerador')
        # Lógica de Geração ...
        # (código omitido para brevidade, é o mesmo da versão anterior)

    with tab_analise:
        st.header("Painel de Análise de Tendências Históricas")
        # (código omitido para brevidade, é o mesmo da versão anterior)
        
    with tab_conferidor:
        st.header("✅ Conferidor de Jogos")
        # (código omitido para brevidade, é o mesmo da versão anterior)

    # --- NOVA ABA: BACKTESTING ---
    with tab_backtest:
        st.header("🔬 Backtesting de Estratégias")
        st.info("Teste a eficácia de uma estratégia de filtros contra os resultados passados.")
        
        st.subheader("1. Defina o Período da Análise")
        n_concursos_backtest = st.number_input("Analisar os últimos X concursos:", min_value=10, max_value=len(df_resultados)-1, value=200, step=10)
        
        st.subheader("2. Defina os Filtros da sua Estratégia")
        col1, col2, col3 = st.columns(3)
        with col1:
            bt_min_rep, bt_max_rep = st.slider("Qtd. Dezenas Repetidas:", 0, 15, (8, 10), key='slider_rep_backtest')
        with col2:
            bt_min_imp, bt_max_imp = st.slider("Qtd. Dezenas Ímpares:", 0, 15, (7, 9), key='slider_imp_backtest')
        with col3:
            bt_min_mold, bt_max_mold = st.slider("Qtd. Dezenas na Moldura:", 0, 16, (9, 11), key='slider_mold_backtest')
        
        if st.button("Iniciar Backtest ⚡", type="primary"):
            with st.spinner(f"Analisando {n_concursos_backtest} concursos..."):
                sorteios_alinhados = executar_backtest(df_resultados, n_concursos_backtest, bt_min_rep, bt_max_rep, bt_min_imp, bt_max_imp, bt_min_mold, bt_max_mold)
            
            st.write("---")
            st.subheader("Resultado do Backtest")
            
            total_testado = len(df_resultados.tail(n_concursos_backtest)) -1 
            total_alinhado = len(sorteios_alinhados)
            percentual = (total_alinhado / total_testado * 100) if total_testado > 0 else 0
            
            st.metric(label="Percentual de Alinhamento", value=f"{percentual:.1f} %", delta=f"{total_alinhado} de {total_testado} concursos")
            st.progress(int(percentual))
            st.write(f"A sua estratégia se alinhou com o resultado real em **{total_alinhado}** dos últimos **{total_testado}** concursos analisados.")
            
            with st.expander("Ver concursos que se alinharam com a estratégia"):
                st.write(sorteios_alinhados)
else:
    st.warning("Aguardando o carregamento dos dados...")
