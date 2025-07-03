import pandas as pd
import itertools

# --- CONFIGURAÇÕES DOS SEUS FILTROS ---
# Altere os valores abaixo para definir sua estratégia

# 1. Universo de dezenas para gerar as combinações. 
#    Use entre 18 a 21 dezenas para um bom resultado.
DEZENAS_ESCOLHIDAS = {1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 19, 20, 21, 22, 24, 25}

# 2. Filtro de Dezenas Repetidas (do último concurso)
#    A maioria dos sorteios tem entre 8 e 10.
MIN_REPETIDAS = 8
MAX_REPETIDAS = 10

# 3. Filtro de Números Ímpares
#    A maioria dos sorteios tem entre 7 e 9.
MIN_IMPARES = 7
MAX_IMPARES = 9

# --- FIM DAS CONFIGURAÇÕES ---


def analisar_e_gerar():
    """
    Função principal que lê os dados, analisa o último concurso
    e gera jogos filtrados.
    """
    try:
        # Tenta ler o arquivo Excel. O arquivo deve estar na mesma pasta do script.
        df = pd.read_excel("Lotofácil.xlsx")
    except FileNotFoundError:
        print("ERRO: Arquivo 'Lotofácil.xlsx' não encontrado.")
        print("Por favor, verifique se a planilha está na mesma pasta que este programa.")
        return

    # Pega o último concurso da planilha
    ultimo_concurso = df.iloc[-1]
    dezenas_ultimo_concurso = set(ultimo_concurso[['Bola1', 'Bola2', 'Bola3', 'Bola4', 'Bola5',
                                                   'Bola6', 'Bola7', 'Bola8', 'Bola9', 'Bola10',
                                                   'Bola11', 'Bola12', 'Bola13', 'Bola14', 'Bola15']].astype(int))

    print("--- ANÁLISE E GERAÇÃO DE JOGOS LOTOFÁCIL ---")
    print(f"\nAnalisando com base no Concurso: {int(ultimo_concurso['Concurso'])}")
    print(f"Dezenas sorteadas: {sorted(list(dezenas_ultimo_concurso))}")
    print("-" * 50)

    # Verifica se as dezenas escolhidas são válidas
    if len(DEZENAS_ESCOLHIDAS) < 15:
        print("ERRO: Você precisa escolher pelo menos 15 dezenas em DEZENAS_ESCOLHIDAS.")
        return

    # Gera todas as combinações de 15 dezenas a partir do seu universo
    todas_combinacoes = list(itertools.combinations(DEZENAS_ESCOLHIDAS, 15))
    total_inicial = len(todas_combinacoes)
    print(f"Gerando {total_inicial} jogos a partir das {len(DEZENAS_ESCOLHIDAS)} dezenas escolhidas...")

    # Aplicando os filtros
    print("Aplicando filtros para selecionar os melhores jogos...")
    jogos_filtrados = []
    for jogo_tupla in todas_combinacoes:
        jogo_set = set(jogo_tupla)

        # Filtro 1: Dezenas Repetidas
        qtd_repetidas = len(jogo_set.intersection(dezenas_ultimo_concurso))
        if not (MIN_REPETIDAS <= qtd_repetidas <= MAX_REPETIDAS):
            continue

        # Filtro 2: Números Ímpares
        qtd_impares = len([num for num in jogo_set if num % 2 != 0])
        if not (MIN_IMPARES <= qtd_impares <= MAX_IMPARES):
            continue
            
        # Se o jogo passou por todos os filtros, ele é adicionado à lista
        jogos_filtrados.append(sorted(list(jogo_set)))

    print("-" * 50)
    print("--- RESULTADO ---")
    print(f"De {total_inicial} jogos possíveis, {len(jogos_filtrados)} foram selecionados após os filtros.")
    print("\nAqui estão os jogos sugeridos:\n")

    if not jogos_filtrados:
        print("Nenhum jogo encontrado com os filtros definidos. Tente aumentar os intervalos (ex: MIN/MAX) ou escolher mais dezenas.")
    else:
        for i, jogo in enumerate(jogos_filtrados):
            # Formata a lista de números para uma string mais legível
            jogo_str = ", ".join(f"{num:02d}" for num in jogo)
            print(f"Jogo {i+1:03d}: [ {jogo_str} ]")

# Roda a função principal quando o script é executado
if __name__ == "__main__":
    analisar_e_gerar()