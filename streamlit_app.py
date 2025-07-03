import streamlit as st
import pandas as pd
import itertools

# --- Configuração da Página ---
st.set_page_config(page_title="Gerador Lotofácil", page_icon="🎲", layout="wide")

# --- Título e Descrição ---
st.title("🎲 Gerador Inteligente de Jogos da Lotofácil")
st.write("Esta ferramenta usa a sua planilha de resultados para gerar jogos com base em filtros estatísticos.")

# --- Lógica Principal ---
def gerar_jogos(df, dezenas_escolhidas, min_rep, max_rep, min_imp, max_imp):
    """Função que processa e gera os jogos filtrados."""
    
    # Pega o último concurso da planilha
    ultimo_concurso = df.iloc[-1]
    dezenas_ultimo_concurso = set(ultimo_concurso.iloc[2:17].astype(int))

    st.subheader("Análise do Último Concurso")
    st.info(f"Analisando com base no Concurso: **{int(ultimo_concurso['Concurso'])}**")
    st.write(f"**Dezenas sorteadas:** `{sorted(list(dezenas_ultimo_concurso))}`")

    # Gera todas as combinações
    try:
        combinacoes = list(itertools.combinations(dezenas_escolhidas, 15))
        total_inicial = len(combinacoes)
    except Exception as e:
        st.error(f"Erro ao gerar combinações. Verifique se as dezenas foram inseridas corretamente. Erro: {e}")
        return

    if total_inicial == 0:
        st.warning("Nenhuma combinação possível com as dezenas fornecidas. Você precisa escolher pelo menos 15 dezenas.")
        return

    # Filtra os jogos
    jogos_filtrados = []
    for jogo_tupla in combinacoes:
        jogo_set = set(jogo_tupla)
        
        # Filtro de Repetidas
        qtd_repetidas = len(jogo_set.intersection(dezenas_ultimo_concurso))
        if not (min_rep <= qtd_repetidas <= max_rep):
            continue
            
        # Filtro de Ímpares
        qtd_impares = len([num for num in jogo_set if num % 2 != 0])
        if not (min_imp <= qtd_impares <= max_imp):
            continue
            
        jogos_filtrados.append(sorted(list(jogo_set)))

    # Mostra os resultados
    st.subheader("Resultados da Geração")
    st.success(f"De **{total_inicial}** jogos possíveis, **{len(jogos_filtrados)}** foram selecionados após os filtros.")
    
    if jogos_filtrados:
        st.write("---")
        # Cria colunas para exibir os jogos de forma mais organizada
        col1, col2, col3 = st.columns(3)
        colunas = [col1, col2, col3]
        for i, jogo in enumerate(jogos_filtrados):
            jogo_str = ", ".join(f"{num:02d}" for num in jogo)
            colunas[i % 3].text(f"Jogo {i+1:03d}: [ {jogo_str} ]")
    else:
        st.warning("Nenhum jogo encontrado com os filtros atuais. Tente usar filtros mais abertos ou um universo maior de dezenas.")


# --- Interface do Usuário (UI) ---
st.sidebar.header("1. Carregue sua Planilha")
uploaded_file = st.sidebar.file_uploader("Escolha o seu arquivo Lotofácil.xlsx", type="xlsx")

st.sidebar.header("2. Defina sua Estratégia")
dezenas_str = st.sidebar.text_area("Seu universo de dezenas (separadas por vírgula):", "1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25", height=150)

st.sidebar.subheader("Filtros:")
min_rep, max_rep = st.sidebar.slider("Quantidade de Dezenas Repetidas:", 0, 15, (8, 10))
min_imp, max_imp = st.sidebar.slider("Quantidade de Dezenas Ímpares:", 0, 15, (7, 9))

if uploaded_file is not None:
    try:
        df_resultados = pd.read_excel(uploaded_file)
        
        # Converte a string de dezenas em uma lista de números inteiros
        dezenas_escolhidas = sorted(list(set([int(num.strip()) for num in dezenas_str.split(',')])))
        st.write(f"**Universo de {len(dezenas_escolhidas)} dezenas escolhido:** `{dezenas_escolhidas}`")
        
        # Gera os jogos
        gerar_jogos(df_resultados, dezenas_escolhidas, min_rep, max_rep, min_imp, max_imp)
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo ou as dezenas. Verifique o formato. Erro: {e}")
else:
    st.info("Aguardando o upload da sua planilha de resultados para começar a análise.")