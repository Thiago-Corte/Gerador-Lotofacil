import streamlit as st
import pandas as pd
import itertools
from collections import Counter

# --- Configuração da Página ---
st.set_page_config(page_title="Analisador Lotofácil", page_icon="🎲", layout="wide")

# --- Funções de Análise (com cache para performance) ---

@st.cache_data
def extrair_numeros(df):
    """Extrai todos os números sorteados para uma lista de listas."""
    numeros_cols = [f'Bola{i}' for i in range(1, 16)]
    return df[numeros_cols].values.tolist()

@st.cache_data
def analisar_frequencia_e_atraso(numeros_sorteados):
    """Calcula a frequência e o atraso de cada dezena."""
    frequencia = Counter(itertools.chain(*numeros_sorteados))
    
    atraso = {}
    total_concursos = len(numeros_sorteados)
    for dezena in range(1, 26):
        try:
            ultimo_sorteio = max(i for i, sorteio in enumerate(numeros_sorteados) if dezena in sorteio)
            atraso[dezena] = total_concursos - 1 - ultimo_sorteio
        except ValueError:
            atraso[dezena] = total_concursos  # Nunca foi sorteada
            
    return frequencia, atraso

@st.cache_data
def encontrar_combinacoes_frequentes(numeros_sorteados, tamanho):
    """Encontra os pares (tamanho=2) ou trios (tamanho=3) mais frequentes."""
    todas_as_combinacoes = itertools.chain.from_iterable(
        itertools.combinations(sorteio, tamanho) for sorteio in numeros_sorteados
    )
    return Counter(todas_as_combinacoes).most_common(15)

# --- Título Principal ---
st.title("🎲 Analisador e Gerador Inteligente da Lotofácil")
st.write(f"Análise atualizada até a data de hoje: **{pd.Timestamp.now(tz='America/Sao_Paulo').strftime('%d/%m/%Y')}**")

# --- Interface Principal ---
st.sidebar.header("1. Carregue sua Planilha")
uploaded_file = st.sidebar.file_uploader("Escolha o seu arquivo Lotofácil.xlsx", type="xlsx")

if uploaded_file is None:
    st.info("⬅️ **Comece fazendo o upload da sua planilha na barra lateral para carregar os dados.**")
    st.image("https://i.imgur.com/3_Infografico_Lotofacil_Dezenas.png", caption="Exemplo de análise de dezenas.")
else:
    df_resultados = pd.read_excel(uploaded_file)
    todos_os_sorteios = extrair_numeros(df_resultados)
    
    # --- Cria as Abas ---
    tab1, tab2 = st.tabs(["🎯 Gerador de Jogos", "📊 Análise de Tendências"])

    # --- Aba 1: Gerador de Jogos ---
    with tab1:
        st.header("Gerador de Jogos com Filtros Estratégicos")
        
        st.sidebar.header("2. Defina sua Estratégia de Geração")
        dezenas_str = st.sidebar.text_area("Seu universo de dezenas (separadas por vírgula):", "1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25", height=150)
        
        st.sidebar.subheader("Filtros:")
        min_rep, max_rep = st.sidebar.slider("Quantidade de Dezenas Repetidas (do último concurso):", 0, 15, (8, 10))
        min_imp, max_imp = st.sidebar.slider("Quantidade de Dezenas Ímpares:", 0, 15, (7, 9))
        
        # Lógica do Gerador
        try:
            dezenas_escolhidas = sorted(list(set([int(num.strip()) for num in dezenas_str.split(',')])))
            st.write(f"**Universo de {len(dezenas_escolhidas)} dezenas escolhido:** `{dezenas_escolhidas}`")

            ultimo_concurso_numeros = set(todos_os_sorteios[-1])
            st.info(f"Analisando com base no Concurso **{df_resultados.iloc[-1]['Concurso']}** de dezenas: `{sorted(list(ultimo_concurso_numeros))}`")
            
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
                        for i, jogo in enumerate(jogos_filtrados):
                            jogo_str = ", ".join(f"{num:02d}" for num in jogo)
                            colunas[i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
        except Exception as e:
            st.error(f"Ocorreu um erro. Verifique se as dezenas foram inseridas corretamente. Detalhe: {e}")

    # --- Aba 2: Análise de Tendências ---
    with tab2:
        st.header("Painel de Análise de Tendências Históricas")
        st.write("Análises baseadas em todos os concursos da planilha carregada.")

        # Executa as análises
        frequencia, atraso = analisar_frequencia_e_atraso(todos_os_sorteios)
        pares_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 2)
        trios_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 3)

        # Prepara dados para exibição
        df_freq = pd.DataFrame(frequencia.most_common(25), columns=['Dezena', 'Frequência']).set_index('Dezena')
        df_atraso = pd.DataFrame(atraso.items(), columns=['Dezena', 'Atraso (concursos)']).sort_values(by='Atraso (concursos)', ascending=False).set_index('Dezena')

        # Exibição das análises
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌡️ Dezenas Quentes e Frias")
            st.bar_chart(df_freq)

            st.subheader("✨ Pares de Ouro")
            df_pares = pd.DataFrame(pares_frequentes, columns=['Par', 'Vezes'])
            st.dataframe(df_pares, use_container_width=True)
        
        with col2:
            st.subheader("⏳ Dezenas Atrasadas")
            st.dataframe(df_atraso, use_container_width=True)

            st.subheader("💎 Trios de Diamante")
            df_trios = pd.DataFrame(trios_frequentes, columns=['Trio', 'Vezes'])
            st.dataframe(df_trios, use_container_width=True)
