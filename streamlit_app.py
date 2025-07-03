import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import requests
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Analisador Lotofácil Pro", page_icon="🚀", layout="wide")

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS ---

@st.cache_data(ttl=3600) # Armazena o resultado por 1 hora
def carregar_dados_da_web():
    """
    Carrega os dados históricos da Lotofácil usando o arquivo local como base
    e busca o último resultado na API da Caixa para complementar.
    """
    df_completo = None
    try:
        df_hist = pd.read_excel("Lotofácil.xlsx")
        df_hist = df_hist.iloc[:, :17]
        df_hist.columns = ['Concurso', 'Data Sorteio', 'Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15']
        df_completo = df_hist

    except FileNotFoundError:
        st.error("ERRO CRÍTICO: O arquivo 'Lotofácil.xlsx' não foi encontrado no seu repositório do GitHub. Por favor, faça o upload do arquivo para que a aplicação funcione.")
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
        st.warning(f"Aviso: Não foi possível buscar o último resultado da API. Usando apenas os dados do seu arquivo Excel. Erro: {e}")

    for col in df_completo.columns:
        if 'Bola' in col or 'Concurso' in col:
            df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce')
    
    return df_completo.sort_values(by='Concurso').reset_index(drop=True)


@st.cache_data
def extrair_numeros(_df):
    bola_cols = [col for col in _df.columns if col.startswith('Bola')]
    return _df[bola_cols].dropna().astype(int).values.tolist()

@st.cache_data
def analisar_frequencia_e_atraso(_numeros_sorteados, total_concursos_geral):
    frequencia = Counter(itertools.chain(*_numeros_sorteados))
    atraso = {}
    
    for dezena in range(1, 26):
        try:
            # Encontra o índice do último sorteio em que a dezena apareceu na lista GERAL
            ultimo_sorteio_idx_geral = max(i for i, sorteio in enumerate(todos_os_sorteios) if dezena in sorteio)
            atraso[dezena] = total_concursos_geral - 1 - ultimo_sorteio_idx_geral
        except ValueError:
            atraso[dezena] = total_concursos_geral
            
    return frequencia, atraso

@st.cache_data
def encontrar_combinacoes_frequentes(_numeros_sorteados, tamanho):
    todas_as_combinacoes = itertools.chain.from_iterable(itertools.combinations(sorteio, tamanho) for sorteio in _numeros_sorteados)
    return Counter(todas_as_combinacoes).most_common(15)

# --- FUNÇÃO CORRIGIDA: MOTOR DE SUGESTÃO ---
@st.cache_data
def sugerir_universo_estrategico(_df, _todos_os_sorteios, num_sorteios=1000, tamanho_universo=19):
    """
    Analisa os últimos 1000 jogos e sugere um universo de 19 dezenas
    combinando frequência e atraso. CORRIGIDO PARA USAR TODAS AS 25 DEZENAS.
    """
    df_recente = _df.tail(num_sorteios)
    numeros_recentes = extrair_numeros(df_recente)
    
    # Análise de Frequência no período recente de 1000 jogos
    frequencia_recente = Counter(itertools.chain(*numeros_recentes))
    
    # Análise de Atraso considerando o histórico GERAL
    _, atraso_geral = analisar_frequencia_e_atraso(numeros_recentes, len(_todos_os_sorteios))
    
    scores = {}
    # Normalização dos scores
    max_freq = max(frequencia_recente.values()) if frequencia_recente else 1
    max_atraso = max(atraso_geral.values()) if atraso_geral else 1

    for dezena in range(1, 26):
        # Score de Frequência (0 a 1)
        score_freq = frequencia_recente.get(dezena, 0) / max_freq
        
        # Score de Atraso (0 a 1)
        score_atraso = atraso_geral.get(dezena, 0) / max_atraso
        
        # Score Combinado (60% Frequência nos últimos 1000 jogos, 40% Atraso geral)
        scores[dezena] = (0.6 * score_freq) + (0.4 * score_atraso)
        
    # Ordena as dezenas pelo score combinado e retorna as melhores
    dezenas_ordenadas = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    
    universo_sugerido = [dezena for dezena, score in dezenas_ordenadas[:tamanho_universo]]
    return sorted(universo_sugerido)


# --- INÍCIO DA APLICAÇÃO ---

st.title("🚀 Analisador Lotofácil Pro")
df_resultados = carregar_dados_da_web()

# Inicializa o session_state para guardar as dezenas sugeridas
if 'sugeridas' not in st.session_state:
    st.session_state.sugeridas = ""

if df_resultados is not None and not df_resultados.empty:
    todos_os_sorteios = extrair_numeros(df_resultados)
    ultimo_concurso_num = int(df_resultados.iloc[-1]['Concurso'])
    
    st.success(f"**Dados carregados com sucesso!** Último concurso na base: **{ultimo_concurso_num}**.")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Gerador de Jogos", "📊 Análise de Tendências", "✅ Conferidor de Jogos"])

    # --- Aba 1: Gerador de Jogos ---
    with tab1:
        st.header("Gerador de Jogos com Filtros Estratégicos")
        
        st.sidebar.header("Defina sua Estratégia de Geração")
        
        st.sidebar.subheader("✨ Sugestão Inteligente")
        if st.sidebar.button("Sugerir Universo (Análise de 1000 Sorteios)"):
            with st.spinner("Analisando 1000 sorteios... Isso pode levar um momento."):
                universo = sugerir_universo_estrategico(df_resultados, todos_os_sorteios)
                st.session_state.sugeridas = ", ".join(map(str, universo))
        
        dezenas_str = st.sidebar.text_area("Seu universo de dezenas (separadas por vírgula):", value=st.session_state.sugeridas, height=150)
        st.sidebar.subheader("Filtros:")
        min_rep, max_rep = st.sidebar.slider("Quantidade de Dezenas Repetidas (do último concurso):", 0, 15, (8, 10), key='slider_rep')
        min_imp, max_imp = st.sidebar.slider("Quantidade de Dezenas Ímpares:", 0, 15, (7, 9), key='slider_imp')
        
        try:
            if dezenas_str:
                dezenas_escolhidas = sorted(list(set([int(num.strip()) for num in dezenas_str.split(',') if num.strip()])))
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
                            if len(jogos_filtrados) > 20:
                                 st.info(f"Mostrando os primeiros 20 jogos de {len(jogos_filtrados)} gerados.")
                            col1, col2, col3 = st.columns(3)
                            colunas = [col1, col2, col3]
                            for i, jogo in enumerate(jogos_filtrados[:20]):
                                jogo_str = ", ".join(f"{num:02d}" for num in jogo)
                                colunas[i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar os jogos. Verifique se as dezenas foram inseridas corretamente. Detalhe: {e}")

    # --- Aba 2: Análise de Tendências ---
    with tab2:
        st.header("Painel de Análise de Tendências Históricas")
        st.write(f"Análises baseadas em todos os {ultimo_concurso_num} concursos.")
        frequencia, atraso = analisar_frequencia_e_atraso(todos_os_sorteios, len(todos_os_sorteios))
        df_freq = pd.DataFrame(frequencia.most_common(25), columns=['Dezena', 'Frequência']).set_index('Dezena')
        df_atraso = pd.DataFrame(atraso.items(), columns=['Dezena', 'Atraso (concursos)']).sort_values(by='Atraso (concursos)', ascending=False).set_index('Dezena')
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🌡️ Dezenas Quentes e Frias")
            st.bar_chart(df_freq)
            st.subheader("✨ Pares de Ouro (Top 15)")
            pares_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 2)
            st.dataframe(pd.DataFrame(pares_frequentes, columns=['Par', 'Vezes']), use_container_width=True)
        with col2:
            st.subheader("⏳ Dezenas Atrasadas")
            st.dataframe(df_atraso, use_container_width=True)
            st.subheader("💎 Trios de Diamante (Top 15)")
            trios_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 3)
            st.dataframe(pd.DataFrame(trios_frequentes, columns=['Trio', 'Vezes']), use_container_width=True)

    # --- Aba 3: Conferidor de Jogos ---
    with tab3:
        st.header("✅ Conferidor de Jogos")
        st.write("Cole seus jogos e o resultado do sorteio para ver seus acertos.")
        
        col1, col2 = st.columns(2)
        with col1:
            jogos_para_conferir = st.text_area("Cole seus jogos aqui (um por linha, dezenas separadas por vírgula)", height=250, placeholder="Ex: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15\n1,3,5,7,9,11,13,15,17,19,21,22,23,24,25")
        
        with col2:
            resultado_str = st.text_input("Digite o resultado do sorteio (15 dezenas separadas por vírgula)")
        
        if st.button("Conferir Meus Jogos", type="primary"):
            try:
                resultado_set = set([int(num.strip()) for num in resultado_str.split(',') if num.strip().isdigit()])
                if len(resultado_set) != 15:
                    st.error("Erro: O resultado do sorteio deve conter exatamente 15 números válidos.")
                else:
                    linhas = jogos_para_conferir.strip().split('\n')
                    jogos = [set([int(num.strip()) for num in linha.split(',') if num.strip().isdigit()]) for linha in linhas if linha]
                    
                    if not jogos:
                        st.warning("Nenhum jogo para conferir. Por favor, cole seus jogos na área de texto.")
                    else:
                        st.write("---")
                        st.subheader("Resultado da Conferência")
                        
                        resultados_conferencia = []
                        premios = Counter()
                        
                        for i, jogo_set in enumerate(jogos):
                            if len(jogo_set) > 0:
                                acertos = len(jogo_set.intersection(resultado_set))
                                jogo_formatado = ", ".join(map(str, sorted(list(jogo_set))))
                                resultados_conferencia.append({'Jogo': jogo_formatado, 'Acertos': acertos})
                                
                                if acertos >= 11:
                                    premios[acertos] += 1

                        df_conferencia = pd.DataFrame(resultados_conferencia)
                        st.dataframe(df_conferencia, use_container_width=True)
                        
                        st.write("---")
                        st.subheader("Resumo de Prêmios")
                        if sum(premios.values()) > 0:
                            for acertos, qtd in sorted(premios.items(), reverse=True):
                                st.success(f"Você teve **{qtd}** jogo(s) com **{acertos}** acertos!")
                        else:
                            st.info("Nenhum jogo premiado (11 ou mais acertos).")

            except Exception as e:
                st.error(f"Ocorreu um erro ao conferir os jogos. Verifique se os números foram digitados corretamente.")
                st.error(f"Detalhe: {e}")

else:
    st.warning("Aguardando o carregamento dos dados... A API da Caixa pode estar temporariamente indisponível ou o arquivo Excel não foi encontrado no repositório.")
