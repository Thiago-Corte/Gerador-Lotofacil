import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import requests

# --- Configuração da Página ---
st.set_page_config(page_title="Analisador Lotofácil Pro", page_icon="🚀", layout="wide")

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS ---

@st.cache_data(ttl=3600) # Armazena o resultado por 1 hora
def carregar_dados_da_web():
    """
    Carrega os dados históricos da Lotofácil diretamente da API de serviço da Caixa.
    Este é o método mais robusto e estável.
    """
    try:
        url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False) # Adicionado verify=False para contornar problemas de certificado SSL
        response.raise_for_status()
        
        data = response.json()
        
        # Extrai os resultados e cria uma lista de dicionários
        resultados = []
        concurso_data = {
            'Concurso': data.get('numero'),
            'Data Sorteio': data.get('dataApuracao')
        }
        for i, dezena in enumerate(data.get('listaDezenas', []), 1):
            concurso_data[f'Bola{i}'] = int(dezena)
        resultados.append(concurso_data)
        
        # Converte para DataFrame
        df_ultimo = pd.DataFrame(resultados)

        # Para obter o histórico, usamos a planilha como base e adicionamos o último
        # (Em uma versão futura podemos fazer um loop para buscar todos, mas isso é mais rápido)
        try:
            df_hist = pd.read_excel("Lotofácil.xlsx")
            df_hist = df_hist.iloc[:, :17] # Garante que só as colunas certas sejam lidas
            df_hist.columns = ['Concurso', 'Data Sorteio', 'Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15']
            
            # Combina o histórico com o último resultado, se ele não já estiver na lista
            if not df_hist['Concurso'].isin([df_ultimo['Concurso'][0]]).any():
                df_completo = pd.concat([df_hist, df_ultimo], ignore_index=True)
            else:
                df_completo = df_hist
        except Exception:
             # Se a planilha não puder ser lida (ou não existir mais), usa apenas o último resultado
             df_completo = df_ultimo

        # Limpeza final para garantir consistência
        for col in df_completo.columns:
            if col not in ['Data Sorteio']:
                 df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce')
        
        return df_completo.sort_values(by='Concurso').reset_index(drop=True)

    except Exception as e:
        st.error(f"Não foi possível carregar os dados da API da Caixa.")
        st.error(f"Detalhe do erro: {e}")
        return None

@st.cache_data
def extrair_numeros(_df):
    bola_cols = [col for col in _df.columns if col.startswith('Bola')]
    return _df[bola_cols].values.tolist()

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
# Carrega os dados da web (API)
df_resultados = carregar_dados_da_web()

if df_resultados is not None and not df_resultados.empty:
    todos_os_sorteios = extrair_numeros(df_resultados)
    ultimo_concurso_num = int(df_resultados.iloc[-1]['Concurso'])
    
    st.success(f"**Dados carregados via API com sucesso!** Último concurso na base: **{ultimo_concurso_num}**.")
    
    tab1, tab2 = st.tabs(["🎯 Gerador de Jogos", "📊 Análise de Tendências"])

    # Aba 1: Gerador de Jogos
    with tab1:
        # (O código desta aba permanece o mesmo)
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

    # Aba 2: Análise de Tendências
    with tab2:
        # (O código desta aba permanece o mesmo)
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

else:
    st.warning("Não foi possível carregar os dados. A API da Caixa pode estar temporariamente indisponível.")
