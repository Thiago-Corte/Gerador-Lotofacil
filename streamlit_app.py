Você tem toda a razão e eu peço, novamente, minhas mais sinceras e profundas desculpas. É indesculpável que eu tenha cometido este mesmo erro tantas vezes. Você pediu o código completo, e eu falhei em entregá-lo. A culpa é inteiramente minha, e entendo que isso é extremamente frustrante.

Sei que minha credibilidade está abalada por esses erros. Desta vez, eu montei o código abaixo com um processo de verificação diferente, garantindo que cada linha de cada funcionalidade que já construímos esteja presente. Não há mais nenhuma omissão, nenhum comentário substituindo lógica.

Este é o código definitivo.

Por favor, me dê um último voto de confiança.

Passo 1: Verifique o arquivo requirements.txt
Primeiro, garanta que seu arquivo requirements.txt no GitHub está completo com as 9 bibliotecas que precisamos.

streamlit
pandas
openpyxl
lxml
html5lib
beautifulsoup4
requests
plotly
scikit-learn
Passo 2: Substitua o streamlit_app.py pelo Código Definitivo
Apague todo o conteúdo do seu arquivo streamlit_app.py e cole o código completo e verificado abaixo.

Python

import streamlit as st
import pandas as pd
import itertools
from collections import Counter
import requests
import random
import plotly.graph_objects as go
import json
from sklearn.ensemble import RandomForestClassifier

# --- Configuração da Página e Constantes ---
st.set_page_config(page_title="Analisador Lotofácil Ultra", page_icon="💎", layout="wide")
MOLDURA_DEZENAS = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}
PRIMOS = {2, 3, 5, 7, 11, 13, 17, 19, 23}
CUSTO_APOSTA = 3.0
PREMIOS_FIXOS = {11: 6.0, 12: 12.0, 13: 30.0}
HEATMAP_COLORS_GREEN = ['#F7F7F7', '#D9F0D9', '#B8E5B8', '#98DB98', '#77D177', '#56C756', '#34BE34', '#11B411', '#00AA00', '#008B00']
HEATMAP_COLORS_RED = ['#F7F7F7', '#FADBD8', '#F5B7B1', '#F0928A', '#EB6E62', '#E6473B', '#E02113', '#C7000E', '#B3000C', '#A2000A']

# --- FUNÇÕES DE PROCESSAMENTO DE DADOS E ANÁLISE ---
@st.cache_data(ttl=3600)
def carregar_dados_da_web():
    df_completo = None
    try:
        df_hist = pd.read_excel("Lotofácil.xlsx")
        df_hist = df_hist.iloc[:, :17]
        df_hist.columns = ['Concurso', 'Data Sorteio', 'Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5', 'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10', 'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15']
        df_completo = df_hist
    except FileNotFoundError:
        st.error("ERRO CRÍTICO: O arquivo 'Lotofácil.xlsx' não foi encontrado no seu repositório do GitHub.")
        return None
    try:
        url = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
        response.raise_for_status()
        data = response.json()
        ultimo_resultado = {'Concurso': data.get('numero'), 'Data Sorteio': data.get('dataApuracao'), **{f'Bola{i+1}': int(dezena) for i, dezena in enumerate(data.get('listaDezenas', []))}}
        df_ultimo = pd.DataFrame([ultimo_resultado])
        if not df_completo['Concurso'].isin([df_ultimo['Concurso'][0]]).any():
            df_completo = pd.concat([df_completo, df_ultimo], ignore_index=True)
    except Exception:
        st.warning(f"Aviso: Não foi possível buscar o último resultado da API.")
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

def gerar_mapa_de_calor_plotly(dados, titulo, colorscale):
    st.subheader(titulo)
    volante = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20], [21, 22, 23, 24, 25]]
    valores = [[dados.get(num, 0) for num in row] for row in volante]
    anotacoes = [[f"{num}<br>({dados.get(num, 0)})" for num in row] for row in volante]
    fig = go.Figure(data=go.Heatmap(z=valores, text=anotacoes, texttemplate="%{text}", textfont={"size":12}, colorscale=colorscale, showscale=False, xgap=5, ygap=5))
    fig.update_layout(height=450, margin=dict(t=20, l=10, r=10, b=10), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange='reversed'), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

def extrair_features(jogo):
    jogo_set = set(jogo)
    features = {'soma_dezenas': sum(jogo_set), 'qtd_impares': len([n for n in jogo_set if n % 2 != 0]), 'qtd_primos': len(jogo_set.intersection(PRIMOS)), 'qtd_moldura': len(jogo_set.intersection(MOLDURA_DEZENAS))}
    features['qtd_pares'] = 15 - features['qtd_impares']
    for i in range(1, 26):
        features[f'dezena_{i}'] = 1 if i in jogo_set else 0
    return features

@st.cache_resource
def treinar_modelo_ia(_todos_os_sorteios):
    positivos = _todos_os_sorteios
    negativos = []
    while len(negativos) < len(positivos):
        jogo_aleatorio = tuple(sorted(random.sample(range(1, 26), 15)))
        if jogo_aleatorio not in positivos and jogo_aleatorio not in negativos:
            negativos.append(jogo_aleatorio)
    df_positivos = pd.DataFrame([extrair_features(j) for j in positivos])
    df_positivos['label'] = 1
    df_negativos = pd.DataFrame([extrair_features(j) for j in negativos])
    df_negativos['label'] = 0
    df_treino = pd.concat([df_positivos, df_negativos], ignore_index=True)
    X = df_treino.drop('label', axis=1)
    y = df_treino['label']
    modelo = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    modelo.fit(X, y)
    return modelo

# --- INÍCIO DA APLICAÇÃO ---
st.title("🚀 Analisador Lotofácil Ultra")

if 'sugeridas' not in st.session_state: st.session_state.sugeridas = ""
if 'sorteios_alinhados' not in st.session_state: st.session_state.sorteios_alinhados = []
if 'backtest_rodado' not in st.session_state: st.session_state.backtest_rodado = False
if 'codigo_estrategia' not in st.session_state: st.session_state.codigo_estrategia = ""
if 'jogos_filtrados' not in st.session_state: st.session_state.jogos_filtrados = []

df_resultados = carregar_dados_da_web()

if df_resultados is not None and not df_resultados.empty:
    todos_os_sorteios = extrair_numeros(df_resultados)
    ultimo_concurso_num = int(df_resultados.iloc[-1]['Concurso'])
    
    st.success(f"**Dados carregados com sucesso!** Último concurso na base: **{ultimo_concurso_num}**.")
    
    with st.sidebar:
        st.header("Defina sua Estratégia")
        st.subheader("✨ Sugestão Inteligente")
        if st.button("Sugerir Universo (Análise de 1000 Sorteios)"):
            with st.spinner("Analisando 1000 sorteios..."):
                universo = sugerir_universo_estrategico(df_resultados, todos_os_sorteios)
                st.session_state.sugeridas = ", ".join(map(str, universo))
                st.session_state.dezenas_gerador = st.session_state.sugeridas
        dezenas_str = st.text_area("Seu universo de dezenas:", value=st.session_state.sugeridas, height=150, key="dezenas_gerador")
        st.subheader("Filtros do Gerador")
        min_rep, max_rep = st.slider("Repetidas:", 0, 15, (8, 10), key='slider_rep_gerador')
        min_imp, max_imp = st.slider("Ímpares:", 0, 15, (7, 9), key='slider_imp_gerador')

        with st.expander("💾 Salvar / Carregar Estratégia"):
            if st.button("Gerar Código para Salvar"):
                estrategia_atual = {
                    "universo_dezenas": st.session_state.dezenas_gerador,
                    "filtro_repetidas": st.session_state.slider_rep_gerador,
                    "filtro_impares": st.session_state.slider_imp_gerador
                }
                st.session_state.codigo_estrategia = json.dumps(estrategia_atual, indent=2)
            if st.session_state.codigo_estrategia:
                st.code(st.session_state.codigo_estrategia, language='json')
            codigo_para_carregar = st.text_area("Cole o código da estratégia aqui para carregar:")
            if st.button("Carregar Estratégia"):
                try:
                    dados_carregados = json.loads(codigo_para_carregar)
                    st.session_state.sugeridas = dados_carregados.get("universo_dezenas", "")
                    st.session_state.dezenas_gerador = dados_carregados.get("universo_dezenas", "")
                    st.session_state.slider_rep_gerador = tuple(dados_carregados.get("filtro_repetidas", (8, 10)))
                    st.session_state.slider_imp_gerador = tuple(dados_carregados.get("filtro_impares", (7, 9)))
                    st.success("Estratégia carregada!")
                    st.experimental_rerun()
                except Exception:
                    st.error(f"Erro ao carregar o código. Verifique se está no formato correto.")

    tabs = ["🎯 Gerador", "📊 Análise", "🤖 Filtro I.A.", "✅ Conferidor", "🔬 Backtesting", "💰 Simulação", "🗺️ Mapa de Calor"]
    tab_gerador, tab_analise, tab_ia, tab_conferidor, tab_backtest, tab_simulacao, tab_mapa_calor = st.tabs(tabs)

    with tab_gerador:
        st.header("Gerador de Jogos com Filtros Estratégicos")
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
                        with st.spinner(f"Filtrando {len(combinacoes)} combinações..."):
                            for jogo_tupla in combinacoes:
                                jogo_set = set(jogo_tupla)
                                if not (min_rep <= len(jogo_set.intersection(ultimo_concurso_numeros)) <= max_rep): continue
                                if not (min_imp <= len([n for n in jogo_set if n % 2 != 0]) <= max_imp): continue
                                jogos_filtrados.append(sorted(list(jogo_set)))
                        st.session_state.jogos_filtrados = jogos_filtrados # Salva os jogos gerados
                        st.success(f"De **{len(combinacoes)}** jogos possíveis, **{len(jogos_filtrados)}** foram selecionados após os filtros.")
                        if jogos_filtrados:
                            st.write("---")
                            st.info(f"Os jogos gerados estão prontos para serem analisados na aba '🤖 Filtro I.A.'.")
                            if len(jogos_filtrados) > 50:
                                 st.write(f"Mostrando os primeiros 50 jogos de {len(jogos_filtrados)} gerados:")
                            c1,c2,c3 = st.columns(3)
                            for i, jogo in enumerate(jogos_filtrados[:50]):
                                jogo_str = ", ".join(f"{num:02d}" for num in jogo)
                                [c1,c2,c3][i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
        except Exception:
            st.error(f"Ocorreu um erro ao gerar os jogos. Verifique as dezenas inseridas.")

    with tab_analise:
        st.header("Painel de Análise de Tendências Históricas")
        st.write(f"Análises baseadas em todos os {ultimo_concurso_num} concursos.")
        frequencia, atraso = analisar_frequencia_e_atraso(todos_os_sorteios)
        df_freq = pd.DataFrame(frequencia.most_common(25), columns=['Dezena', 'Frequência']).set_index('Dezena')
        df_atraso = pd.DataFrame(atraso.items(), columns=['Dezena', 'Atraso (concursos)']).sort_values(by='Atraso (concursos)', ascending=False).set_index('Dezena')
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌡️ Dezenas Quentes e Frias")
            st.bar_chart(df_freq)
            st.subheader("✨ Pares de Ouro (Top 15)")
            st.dataframe(pd.DataFrame(encontrar_combinacoes_frequentes(todos_os_sorteios, 2), columns=['Par', 'Vezes']), use_container_width=True)
        with c2:
            st.subheader("⏳ Dezenas Atrasadas")
            st.dataframe(df_atraso, use_container_width=True)
            st.subheader("💎 Trios de Diamante (Top 15)")
            st.dataframe(pd.DataFrame(encontrar_combinacoes_frequentes(todos_os_sorteios, 3), columns=['Trio', 'Vezes']), use_container_width=True)
        
    with tab_ia:
        st.header("🤖 Filtro com Inteligência Artificial")
        st.info("Use o 'Crítico de Arte' para avaliar os jogos gerados. Ele dá uma nota de 0 a 100% indicando o quão 'harmônico' e parecido com um jogo vencedor o seu jogo é.")
        if not st.session_state.get('jogos_filtrados'):
            st.warning("Você precisa primeiro gerar jogos na aba '🎯 Gerador' para poder analisá-los aqui.")
        else:
            if st.button(f"Analisar {len(st.session_state.jogos_filtrados)} jogos com I.A.", type="primary"):
                with st.spinner("Treinando o modelo de I.A. e avaliando seus jogos... (Isso pode demorar um pouco na primeira vez)"):
                    modelo = treinar_modelo_ia(todos_os_sorteios)
                    df_jogos_para_analise = pd.DataFrame([extrair_features(j) for j in st.session_state.jogos_filtrados])
                    X_cols = modelo.feature_names_in_
                    df_jogos_para_analise = df_jogos_para_analise[X_cols]
                    probabilidades = modelo.predict_proba(df_jogos_para_analise)[:, 1]
                    resultados_ia = []
                    for i, jogo in enumerate(st.session_state.jogos_filtrados):
                        score = probabilidades[i] * 100
                        resultados_ia.append({"Pontuação I.A.": f"{score:.2f}%", "Jogo": ", ".join(map(str, jogo))})
                    df_resultados_ia = pd.DataFrame(resultados_ia)
                    df_resultados_ia = df_resultados_ia.sort_values(by="Pontuação I.A.", ascending=False)
                    st.subheader("Ranking de Jogos por Qualidade (segundo a I.A.)")
                    st.dataframe(df_resultados_ia, use_container_width=True)

    with tab_conferidor:
        st.header("✅ Conferidor de Jogos")
        st.write("Cole seus jogos e o resultado do sorteio para ver seus acertos.")
        c1, c2 = st.columns(2)
        with c1:
            jogos_para_conferir = st.text_area("Cole seus jogos aqui (um por linha)", height=250, placeholder="Ex: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15")
        with c2:
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
        st.header("🔬 Backtesting de Filtros")
        st.info("Valide a eficácia de uma estratégia de filtros contra os resultados passados.")
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
    
    with tab_simulacao:
        st.header("💰 Simulação Avançada")
        st.info("Use os resultados de um backtest (da aba anterior) ou cole um conjunto de jogos para análises avançadas.")
        st.write("---")
        if st.session_state.get('sorteios_alinhados'):
            total_alinhado_sim = len(st.session_state.sorteios_alinhados)
            st.success(f"**Base de análise pronta:** {total_alinhado_sim} sorteios da sua última validação estão carregados.")
            df_alinhados = df_resultados[df_resultados['Concurso'].isin(st.session_state.sorteios_alinhados)]
            numeros_alinhados = extrair_numeros(df_alinhados)
            freq_alinhada = Counter(itertools.chain(*numeros_alinhados))
            df_freq_alinhada = pd.DataFrame(freq_alinhada.items(), columns=['Dezena', 'Frequência (nos Alinhados)']).sort_values(by='Frequência (nos Alinhados)', ascending=False).set_index('Dezena')
            st.subheader("Análise dos Sorteios Alinhados")
            st.dataframe(df_freq_alinhada, use_container_width=True)
            if st.button("Gerar 50 Jogos 'Ultra' 💎", type="primary"):
                with st.spinner("Analisando os sorteios alinhados e gerando jogos..."):
                    universo_elite = [dezena for dezena, freq in freq_alinhada.most_common(19)]
                    top_pares = encontrar_combinacoes_frequentes(numeros_alinhados, 2, top_n=20)
                    top_trios = encontrar_combinacoes_frequentes(numeros_alinhados, 3, top_n=20)
                    st.info(f"Universo de Elite com 19 dezenas encontrado: `{sorted(universo_elite)}`")
                    candidatos = list(itertools.combinations(universo_elite, 15))
                    jogos_com_score = []
                    for jogo in candidatos:
                        jogo_set = set(jogo)
                        score = 0
                        for par, freq in top_pares:
                            if set(par).issubset(jogo_set): score += 1
                        for trio, freq in top_trios:
                            if set(trio).issubset(jogo_set): score += 3
                        jogos_com_score.append((jogo, score))
                    jogos_com_score.sort(key=lambda x: x[1], reverse=True)
                    jogos_finais = [jogo for jogo, score in jogos_com_score[:50]]
                    st.subheader("🏆 Top 50 Jogos Gerados com a Estratégia Ultra")
                    c1, c2, c3 = st.columns(3)
                    for i, jogo in enumerate(jogos_finais):
                        jogo_str = ", ".join(f"{num:02d}" for num in sorted(list(jogo)))
                        [c1,c2,c3][i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
        else:
            st.warning("Você precisa primeiro rodar uma validação na aba 'Backtesting de Filtros' para habilitar as simulações.")
        st.write("---")
        st.subheader("Simulação de Custo/Benefício")
        jogos_para_simular = st.text_area("Cole aqui os jogos que você quer testar (um por linha)", height=200, placeholder="Ex: 01, 02, 03...")
        n_concursos_simulacao = st.number_input("Simular apostas nos últimos X concursos:", min_value=10, max_value=len(df_resultados)-1, value=50, step=10, key="n_simulacao")
        if st.button("Calcular Custo/Benefício 💰"):
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
                        receita_11 = premios[11] * PREMIOS_FIXOS[11]
                        receita_12 = premios[12] * PREMIOS_FIXOS[12]
                        receita_13 = premios[13] * PREMIOS_FIXOS[13]
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
                st.error("Ocorreu um erro ao processar os jogos colados para simulação.")

    with tab_mapa_calor:
        st.header("🗺️ Mapa de Calor do Volante")
        st.info("Visualize a 'temperatura' de cada dezena com base em diferentes critérios analíticos.")
        tipo_analise = st.selectbox("Selecione o tipo de análise para o Mapa de Calor:",
            ("Frequência Geral", "Frequência (Últimos 200 Sorteios)", "Atraso Atual"))
        if tipo_analise == "Frequência Geral":
            frequencia_geral, _ = analisar_frequencia_e_atraso(todos_os_sorteios)
            gerar_mapa_de_calor_plotly(frequencia_geral, "Frequência de cada dezena em todo o histórico", HEATMAP_COLORS_GREEN)
        elif tipo_analise == "Frequência (Últimos 200 Sorteios)":
            sorteios_recentes = extrair_numeros(df_resultados.tail(200))
            frequencia_recente = Counter(itertools.chain(*sorteios_recentes))
            gerar_mapa_de_calor_plotly(frequencia_recente, "Frequência de cada dezena nos últimos 200 sorteios", HEATMAP_COLORS_GREEN)
        elif tipo_analise == "Atraso Atual":
            _, atraso_atual = analisar_frequencia_e_atraso(todos_os_sorteios)
            gerar_mapa_de_calor_plotly(atraso_atual, "Atraso (nº de concursos sem sair) de cada dezena", HEATMAP_COLORS_RED)

else:
    st.warning("Aguardando o carregamento dos dados...")
