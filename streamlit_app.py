import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import requests
import random

# --- Configuração da Página e Constantes ---
st.set_page_config(page_title="Analisador Lotofácil Ultra", page_icon="💎", layout="wide")
MOLDURA_DEZENAS = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PREMIO_11_ACERTOS = 6.0
PREMIO_12_ACERTOS = 12.0
PREMIO_13_ACERTOS = 30.0
CUSTO_APOSTA = 3.0

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
    except Exception:
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
def encontrar_combinacoes_frequentes(_numeros_sorteados, tamanho, top_n=15):
    todas_as_combinacoes = itertools.chain.from_iterable(itertools.combinations(sorteio, tamanho) for sorteio in _numeros_sorteados)
    return Counter(todas_as_combinacoes).most_common(top_n)

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

@st.cache_data
def executar_backtest_filtros(_df, n_concursos, min_rep, max_rep, min_imp, max_imp, min_mold, max_mold):
    sorteios_teste = _df.tail(n_concursos).copy()
    sorteios_alinhados = []
    for index in range(1, len(sorteios_teste)):
        concurso_atual_row = sorteios_teste.iloc[index]
        concurso_anterior_row = sorteios_teste.iloc[index - 1]
        dezenas_atuais = set(concurso_atual_row[[f'Bola{i}' for i in range(1,16)]])
        dezenas_anteriores = set(concurso_anterior_row[[f'Bola{i}' for i in range(1,16)]])
        qtd_repetidas = len(dezenas_atuais.intersection(dezenas_anteriores))
        qtd_impares = len([n for n in dezenas_atuais if n % 2 != 0])
        qtd_moldura = len(dezenas_atuais.intersection(MOLDURA_DEZENAS))
        if (min_rep <= qtd_repetidas <= max_rep) and (min_imp <= qtd_impares <= max_imp) and (min_mold <= qtd_moldura <= max_mold):
            sorteios_alinhados.append(int(concurso_atual_row['Concurso']))
    return sorteios_alinhados

# --- INÍCIO DA APLICAÇÃO ---
st.title("🚀 Analisador Lotofácil Ultra")

if 'sugeridas' not in st.session_state: st.session_state.sugeridas = ""
if 'sorteios_alinhados' not in st.session_state: st.session_state.sorteios_alinhados = []
if 'backtest_rodado' not in st.session_state: st.session_state.backtest_rodado = False

df_resultados = carregar_dados_da_web()

if df_resultados is not None and not df_resultados.empty:
    todos_os_sorteios = extrair_numeros(df_resultados)
    ultimo_concurso_num = int(df_resultados.iloc[-1]['Concurso'])
    
    st.success(f"**Dados carregados com sucesso!** Último concurso na base: **{ultimo_concurso_num}**.")
    
    tabs = ["🎯 Gerador de Jogos", "📊 Análise de Tendências", "✅ Conferidor de Jogos", "🔬 Backtesting e Simulação"]
    tab_gerador, tab_analise, tab_conferidor, tab_backtest = st.tabs(tabs)

    with tab_gerador:
        st.header("Gerador de Jogos com Filtros Estratégicos")
        st.sidebar.header("Defina sua Estratégia de Geração")
        st.sidebar.subheader("✨ Sugestão Inteligente")
        if st.sidebar.button("Sugerir Universo (Análise de 1000 Sorteios)"):
            with st.spinner("Analisando 1000 sorteios..."):
                universo = sugerir_universo_estrategico(df_resultados, todos_os_sorteios)
                st.session_state.sugeridas = ", ".join(map(str, universo))
        dezenas_str = st.sidebar.text_area("Seu universo de dezenas:", value=st.session_state.sugeridas, height=150, key="dezenas_gerador")
        st.sidebar.subheader("Filtros:")
        min_rep, max_rep = st.sidebar.slider("Repetidas:", 0, 15, (8, 10), key='slider_rep_gerador')
        min_imp, max_imp = st.sidebar.slider("Ímpares:", 0, 15, (7, 9), key='slider_imp_gerador')
        
        try:
            if dezenas_str:
                dezenas_escolhidas = sorted(list(set([int(num.strip()) for num in dezenas_str.split(',') if num.strip()])))
                st.write(f"**Universo de {len(dezenas_escolhidas)} dezenas escolhido:** `{dezenas_escolhidas}`")
                ultimo_concurso_numeros = set(todos_os_sorteios[-1])
                st.info(f"Analisando com base no Concurso **{ultimo_concurso_num}** de dezenas: `{sorted(list(ultimo_concurso_numeros))}`")
                if st.button("Gerar Jogos 🚀", type="primary", key="gerar_jogos_principal"):
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
                            if len(jogos_filtrados) > 50:
                                 st.info(f"Mostrando os primeiros 50 jogos de {len(jogos_filtrados)} gerados.")
                            col1, col2, col3 = st.columns(3)
                            for i, jogo in enumerate(jogos_filtrados[:50]): # Mostra no máximo 50 jogos
                                jogo_str = ", ".join(f"{num:02d}" for num in jogo)
                                colunas = [col1, col2, col3]
                                colunas[i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar os jogos. Verifique se as dezenas foram inseridas corretamente.")

    with tab_analise:
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
            st.dataframe(pd.DataFrame(pares_frequentes, columns=['Par', 'Vezes']), use_container_width=True)
        with col2:
            st.subheader("⏳ Dezenas Atrasadas")
            st.dataframe(df_atraso, use_container_width=True)
            st.subheader("💎 Trios de Diamante (Top 15)")
            trios_frequentes = encontrar_combinacoes_frequentes(todos_os_sorteios, 3)
            st.dataframe(pd.DataFrame(trios_frequentes, columns=['Trio', 'Vezes']), use_container_width=True)
        
    with tab_conferidor:
        st.header("✅ Conferidor de Jogos")
        st.write("Cole seus jogos e o resultado do sorteio para ver seus acertos.")
        col1, col2 = st.columns(2)
        with col1:
            jogos_para_conferir = st.text_area("Cole seus jogos aqui (um por linha)", height=250, placeholder="Ex: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15")
        with col2:
            resultado_str = st.text_input("Digite o resultado do sorteio (15 dezenas separadas por vírgula)")
        if st.button("Conferir Meus Jogos", type="primary"):
            try:
                resultado_set = set([int(num.strip()) for num in resultado_str.split(',') if num.strip().isdigit()])
                if len(resultado_set) != 15:
                    st.error("Erro: O resultado do sorteio deve conter exatamente 15 números válidos.")
                else:
                    linhas = jogos_para_conferir.strip().split('\n')
                    jogos = [set([int(num.strip()) for num in linha.replace('[', '').replace(']', '').split(',') if num.strip().isdigit()]) for linha in linhas if linha]
                    if not jogos:
                        st.warning("Nenhum jogo para conferir. Por favor, cole seus jogos na área de texto.")
                    else:
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
                        st.subheader("Resumo de Prêmios")
                        if sum(premios.values()) > 0:
                            for acertos, qtd in sorted(premios.items(), reverse=True):
                                st.success(f"Você teve **{qtd}** jogo(s) com **{acertos}** acertos!")
                        else:
                            st.info("Nenhum jogo premiado (11 ou mais acertos).")
            except Exception:
                st.error(f"Ocorreu um erro ao conferir os jogos. Verifique se os números foram digitados corretamente.")

    with tab_backtest:
        st.header("🔬 Backtesting e Simulação Financeira")
        
        st.subheader("Etapa A: Validar Filtros da Estratégia")
        st.info("Primeiro, veja com que frequência sua estratégia de filtros se alinha com os resultados reais.")
        n_concursos_filtros = st.number_input("Analisar os últimos X concursos:", min_value=10, max_value=len(df_resultados)-1, value=100, step=10, key="n_filtros")
        c1, c2, c3 = st.columns(3)
        with c1: bt_min_rep, bt_max_rep = st.slider("Repetidas:", 0, 15, (8, 10), key='bt_rep')
        with c2: bt_min_imp, bt_max_imp = st.slider("Ímpares:", 0, 15, (7, 9), key='bt_imp')
        with c3: bt_min_mold, bt_max_mold = st.slider("Moldura:", 0, 16, (9, 11), key='bt_mold')
        
        if st.button("Validar Estratégia de Filtros ⚡"):
            st.session_state.backtest_rodado = True
            with st.spinner(f"Analisando {n_concursos_filtros} concursos..."):
                st.session_state.sorteios_alinhados = executar_backtest_filtros(df_resultados, n_concursos_filtros, bt_min_rep, bt_max_rep, bt_min_imp, bt_max_imp, bt_min_mold, bt_max_mold)

        if st.session_state.backtest_rodado:
            st.write("---")
            st.subheader("Resultado da Validação")
            total_testado = len(df_resultados.tail(n_concursos_filtros)) - 1
            total_alinhado = len(st.session_state.sorteios_alinhados)
            percentual = (total_alinhado / total_testado * 100) if total_testado > 0 else 0
            st.metric(label="Percentual de Alinhamento da Estratégia", value=f"{percentual:.1f} %", delta=f"{total_alinhado} de {total_testado} concursos")
            st.progress(int(percentual))
            with st.expander("Ver concursos que se alinharam com a estratégia"):
                st.write(st.session_state.sorteios_alinhados)
        
        st.write("---")
        st.subheader("Etapa B: Simulação de Custo/Benefício de Jogos")
        st.info("Cole um conjunto de jogos e simule quanto eles teriam custado e rendido no passado.")
        
        jogos_para_simular = st.text_area("Cole aqui os jogos que você quer testar (um por linha)", height=200, placeholder="Copie e cole aqui os jogos gerados na primeira aba, por exemplo.")
        n_concursos_simulacao = st.number_input("Simular apostas nos últimos X concursos:", min_value=10, max_value=len(df_resultados)-1, value=100, step=10, key="n_simulacao")

        if st.button("Calcular Custo/Benefício 💰", type="primary"):
            try:
                linhas_simulacao = jogos_para_simular.strip().split('\n')
                jogos_apostados = [set(int(num.strip()) for num in linha.replace('[', '').replace(']', '').split(',') if num.strip()) for linha in linhas_simulacao if linha]
                
                if not jogos_apostados:
                    st.error("Nenhum jogo válido encontrado para simular.")
                else:
                    with st.spinner(f"Simulando {len(jogos_apostados)} jogos em {n_concursos_simulacao} concursos..."):
                        sorteios_para_teste = todos_os_sorteios[-n_concursos_simulacao:]
                        premios = Counter()
                        for sorteio_resultado in sorteios_para_teste:
                            for aposta in jogos_apostados:
                                acertos = len(aposta.intersection(set(sorteio_resultado)))
                                if acertos >= 11:
                                    premios[acertos] += 1
                        
                        custo_total = len(jogos_apostados) * n_concursos_simulacao * CUSTO_APOSTA
                        receita_11 = premios[11] * PREMIO_11_ACERTOS
                        receita_12 = premios[12] * PREMIO_12_ACERTOS
                        receita_13 = premios[13] * PREMIO_13_ACERTOS
                        receita_total_fixa = receita_11 + receita_12 + receita_13
                        saldo = receita_total_fixa - custo_total
                        
                        st.subheader("Relatório Financeiro da Simulação")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Custo Total Estimado", f"R$ {custo_total:,.2f}")
                        c2.metric("Receita (Prêmios Fixos)", f"R$ {receita_total_fixa:,.2f}")
                        c3.metric("Saldo Final", f"R$ {saldo:,.2f}")
                        
                        st.subheader("Detalhamento de Prêmios")
                        st.success(f"**11 Acertos:** {premios[11]} prêmio(s) (Receita: R$ {receita_11:,.2f})")
                        st.success(f"**12 Acertos:** {premios[12]} prêmio(s) (Receita: R$ {receita_12:,.2f})")
                        st.success(f"**13 Acertos:** {premios[13]} prêmio(s) (Receita: R$ {receita_13:,.2f})")
                        st.warning(f"**14 Acertos:** {premios[14]} prêmio(s) (valor variável)")
                        st.error(f"**15 Acertos:** {premios[15]} prêmio(s) (valor variável)")
            except Exception:
                st.error("Ocorreu um erro ao processar os jogos colados para simulação. Verifique o formato.")

else:
    st.warning("Aguardando o carregamento dos dados...")
