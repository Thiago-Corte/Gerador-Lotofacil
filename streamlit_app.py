import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import requests
import zipfile
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Analisador Lotofácil Pro", page_icon="🚀", layout="wide")

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS ---

@st.cache_data(ttl=3600) # Armazena o resultado por 1 hora
def carregar_dados_da_web():
    """
    Carrega os dados históricos da Lotofácil baixando o ZIP oficial da Caixa.
    Este método é mais robusto que ler a página HTML diretamente.
    """
    try:
        # URL direta para o arquivo ZIP com os resultados
        url = "http://loterias.caixa.gov.br/wps/portal/loterias/landing/lotofacil/!ut/p/a1/04_Sj9CPykssy0xPLMnMz0vMAfGjzOLNDH0MPAzcDbwMPI0sDBxNXAOMwrzCjA0MDPSjPKwXK_WzdnQwszV3MPA0cDbwMPI0sDBxNXAOMwrzCjA0MDPSjPKwXK_WzdnQwszV3MPA0cDbwMPI0sDBxNXAOMwrzCjA0MDPSjPKwXK_WzdnQwszV3MPA0cDbwMPI0sDBxNXAOMwrzCjA0MDPSjPKwXK_WzdnQwszV3MDfDzyM_N2DN0VAQAV2_x0!/dl5/d5/L2dBISEvZ0FBIS9nQSEh/pw/Z7_61L0H0G0J0VSC0AC4B04I30000/res/id=historico_resultados/c=cacheLevelPage/=/?urile=wcm:path:/loterias/loterias/lotofacil/lotofacil_resultados.html"
        
        # Faz o download do conteúdo da página
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança um erro se o download falhar

        # Usa pandas para ler a tabela HTML diretamente do conteúdo da página
        dfs = pd.read_html(io.StringIO(response.text))
        df = dfs[0]

        # --- Limpeza e Formatação dos Dados ---
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(axis=0, how='any', inplace=True)
        
        colunas_bolas = [f'Bola {i}' for i in range(1, 16)]
        df = df[['Concurso'] + colunas_bolas]

        novos_nomes = {'Concurso': 'Concurso'}
        for i in range(1, 16):
            novos_nomes[f'Bola {i}'] = f'Bola{i}'
        df = df.rename(columns=novos_nomes)
        
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna().astype(int)
        
        return df.sort_values(by='Concurso').reset_index(drop=True)

    except Exception as e:
        st.error(f"Não foi possível carregar os dados da Caixa. O site pode estar fora do ar ou o formato da tabela mudou.")
        st.error(f"Detalhe do erro: {e}")
        return None

@st.cache_data
def extrair_numeros(_df):
    numeros_cols = [f'Bola{i}' for i in range(1, 16)]
    return _df[numeros_cols].values.tolist()

@st.cache_data
def analisar_frequencia_e_atraso(_numeros_sorteados):
    frequencia = Counter(itertools.chain(*_numeros_sorteados))
    atraso = {}
    total_concursos = len(_numeros_sorteados)
    for dezena in range(1, 26):
        try:
            ultimo_sorteio_idx = max(i for i, sorteio in enumerate(_numeros_sorteados) if dezena in sorteio)
            atraso[dezena] = total_concursos - 1 - ultimo_sorteio_idx
        except ValueError:
            atraso[dezena] = total_concursos
    return frequencia, atraso

@st.cache_data
def encontrar_combinacoes_frequentes(_numeros_sorteados, tamanho):
    todas_as_combinacoes = itertools.chain.from_iterable(itertools.combinations(sorteio, tamanho) for sorteio in _numeros_sorteados)
    return Counter(todas_as_combinacoes).most_common(15)

# --- INÍCIO DA APLICAÇÃO ---

st.title("🚀 Analisador Lotofácil Pro")
df_resultados = carregar_dados_da_web()

if df_resultados is not None:
    todos_os_sorteios = extrair_numeros(df_resultados)
    ultimo_concurso_num = int(df_resultados.iloc[-1]['Concurso'])
    
    st.success(f"**Dados carregados com sucesso!** Último concurso na base: **{ultimo_concurso_num}**.")
    
    tab1, tab2 = st.tabs(["🎯 Gerador de Jogos", "📊 Análise de Tendências"])

    # --- Aba 1: Gerador de Jogos ---
    with tab1:
        st.header("Gerador de Jogos com Filtros Estratégicos")
        
        st.sidebar.header("Defina sua Estratégia de Geração")
        dezenas_str = st.sidebar.text_area("Seu universo de dezenas (separadas por vírgula):", "1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25", height=150)
        
        st.sidebar.subheader("Filtros:")
        min_rep, max_rep = st.sidebar.slider("Quantidade de Dezenas Repetidas (do último concurso):", 0, 15, (8, 10))
        min_imp, max_imp = st.sidebar.slider("Quantidade de Dezenas Ímpares:", 0, 15, (7, 9))
        
        try:
            dezenas_escolhidas = sorted(list(set([int(num.strip()) for num in dezenas_str.split(',')])))
            st.write(f"**Universo de {len(dezenas_escolhidas)} dezenas escolhido:** `{dezenas_escolhidas}`")

            ultimo_concurso_numeros = set(todos_os_sorteios[-1])
            st.info(f"Analisando com base no Concurso **{ultimo_concurso_num}** de dezenas: `{sorted(list(ultimo_concurso_numeros))}`")
            
            if st.button("Gerar Jogos 🚀", type="primary"):
                if len(dezenas_escolhidas) < 15:
                     st.error("Erro: Você precisa escolher pelo menos 15 dezenas.")
                else:
                    combinacoes = list(itertools.combinations(dezenas_escolhidas, 15))
                    jogos_filtrados = []
                    for jogo_tupla in combinacoes:
                        jogo_set = set(jogo_tupla)
                        if not (min_rep <= len(jogo_set.intersection(ultimo_concurso_numeros)) <= max_rep): continue
                        if not (min_imp <= len([n for n in jogo_set if n % 2 != 0]) <= max_imp): continue
                        jogos_filtrados.append(sorted(list(jogo_set)))
                    
                    st.success(f"De **{len(combinacoes)}** jogos possíveis, **{len(jogos_filtrados)}** foram selecionados após os filtros.")
                    if jogos_filtrados:
                        st.write("---")
                        col1, col2, col3 = st.columns(3)
                        colunas = [col1, col2, col3]
                        for i, jogo in enumerate(jogos_filtrados):
                            jogo_str = ", ".join(f"{num:02d}" for num in jogo)
                            colunas[i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
        except Exception as e:
            st.error(f"Ocorreu um erro. Verifique se as dezenas foram inseridas corretamente. Detalhe: {e}")

    # --- Aba 2: Análise de Tendências ---
    with tab2:
        st.header("Painel de Análise de Tendências Históricas")
        st.write(f"Análises baseadas em todos os {ultimo_concurso_num} concursos.")

        frequencia, atraso = analisar_frequencia_e_atraso(todos_os_sorteios)
        
        df_freq = pd.DataFrame(frequencia.most_common(25), columns=['Dezena', 'Frequência']).set_index('Dezena')
        df_atraso = pd.DataFrame(atraso.items(), columns=['Dezena', 'Atraso (concursos)']).sort_values(by='Atraso (concursos)', ascending=False).set_index('Dezena')

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌡️ Dezenas Quentes e Frias")
            st.bar_chart(df_freq)

            st.subheader("✨ Pares de Ouro (Top 15)")
            pares_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 2)
            df_pares = pd.DataFrame(pares_frequentes, columns=['Par', 'Vezes'])
            st.dataframe(df_pares, use_container_width=True)
        
        with col2:
            st.subheader("⏳ Dezenas Atrasadas")
            st.dataframe(df_atraso, use_container_width=True)

            st.subheader("💎 Trios de Diamante (Top 15)")
            trios_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 3)
            df_trios = pd.DataFrame(trios_frequentes, columns=['Trio', 'Vezes'])
            st.dataframe(df_trios, use_container_width=True)
