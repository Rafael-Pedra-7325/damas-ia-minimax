"""
Motor de Inteligência Artificial para Damas Brasileiras usando Minimax com Poda Alfa-Beta,
Busca de Quiescência para trocas de captura, Aprofundamento Iterativo com orçamento de tempo
e Tabela de Transposição com Hashing Zobrist.
"""

import random
import time
from jogo import (
    EMPTY,
    W_MAN,
    W_KING,
    B_MAN,
    B_KING,
    gerar_fen,
    gerar_lances_legais_board,
    aplicar_lance_board,
    desfazer_lance_board,
    rc_para_casa,
)

VALOR_PEDRA = 100
VALOR_DAMA = 330
VITORIA_SCORE = 100000

# Flags da Tabela de Transposição
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2

CASAS_CENTRAIS = {27, 28, 35, 36, 18, 21, 42, 45}

# Tabela Posicional para Pedras (perspectiva das Brancas: linha 7 -> linha 0)
PST_PEDRA = [
     0,  40,   0,  42,   0,  42,   0,  40,
    30,   0,  34,   0,  34,   0,  32,   0,
     0,  22,   0,  28,   0,  28,   0,  20,
    14,   0,  22,   0,  24,   0,  16,   0,
     0,  10,   0,  18,   0,  16,   0,  12,
     8,   0,  10,   0,  12,   0,   8,   0,
     0,   4,   0,   6,   0,   6,   0,   4,
    10,   0,  14,   0,  10,   0,  14,   0,
]

# Tabela Posicional para Damas (valoriza centro e a Grande Diagonal a1-h8)
PST_DAMA = [
     0,   4,   0,   4,   0,   4,   0,  14,
     4,   0,  12,   0,  10,   0,  18,   0,
     0,  12,   0,  20,   0,  22,   0,   6,
     4,   0,  20,   0,  26,   0,  12,   0,
     0,  12,   0,  26,   0,  20,   0,   4,
     6,   0,  22,   0,  20,   0,  12,   0,
     0,  18,   0,  10,   0,  12,   0,   4,
    14,   0,   4,   0,   4,   0,   4,   0,
]

# Chaves Zobrist determinísticas
_rng_zobrist = random.Random(20260519)
ZOBRIST_PECAS = {
    (idx, peca): _rng_zobrist.getrandbits(64)
    for idx in range(64)
    for peca in (W_MAN, W_KING, B_MAN, B_KING)
}
ZOBRIST_TURNO_PRETAS = _rng_zobrist.getrandbits(64)


class BuscaTimeout(Exception):
    """Exceção interna para interromper o aprofundamento iterativo dentro do orçamento de tempo."""


def _calcular_zobrist(board, turno):
    h = 0
    for idx, peca in enumerate(board):
        if peca != EMPTY:
            h ^= ZOBRIST_PECAS[(idx, peca)]
    if turno == -1:
        h ^= ZOBRIST_TURNO_PRETAS
    return h


def _chave_posicao_fen(fen):
    return " ".join(fen.split()[:2])


def avaliar_tabuleiro(board, cor_ia):
    """
    Avalia a posição em centipeões sob a perspectiva de `cor_ia` (1 = brancas, -1 = pretas).
    Valores positivos favorecem a IA; negativos favorecem o oponente.
    """
    pontuacao_brancas = 0
    pedras_b = 0
    pedras_p = 0
    damas_b = 0
    damas_p = 0

    for idx, peca in enumerate(board):
        if peca == EMPTY:
            continue
        if peca == W_MAN:
            pedras_b += 1
            pontuacao_brancas += VALOR_PEDRA + PST_PEDRA[idx]
        elif peca == W_KING:
            damas_b += 1
            pontuacao_brancas += VALOR_DAMA + PST_DAMA[idx]
        elif peca == B_MAN:
            pedras_p += 1
            pontuacao_brancas -= VALOR_PEDRA + PST_PEDRA[63 - idx]
        elif peca == B_KING:
            damas_p += 1
            pontuacao_brancas -= VALOR_DAMA + PST_DAMA[63 - idx]

    total_b = pedras_b + damas_b
    total_p = pedras_p + damas_p

    if total_b == 0:
        return -VITORIA_SCORE if cor_ia == 1 else VITORIA_SCORE
    if total_p == 0:
        return VITORIA_SCORE if cor_ia == 1 else -VITORIA_SCORE

    # Bônus de defesa da base ("Ponte") enquanto o adversário não possui Damas
    if damas_p == 0:
        if board[57] == W_MAN and board[61] == W_MAN:
            pontuacao_brancas += 18
    if damas_b == 0:
        if board[2] == B_MAN and board[6] == B_MAN:
            pontuacao_brancas -= 18

    # Simplificação estratégica: incentiva trocar peças quando está em vantagem material
    total_pecas = total_b + total_p
    if total_pecas <= 12 and abs(pontuacao_brancas) >= 120:
        bonus_simplificacao = (12 - total_pecas) * 6
        if pontuacao_brancas > 0:
            pontuacao_brancas += bonus_simplificacao
        else:
            pontuacao_brancas -= bonus_simplificacao

    return pontuacao_brancas if cor_ia == 1 else -pontuacao_brancas


def _prioridade_lance(board, lance, uci_tt=None):
    """Ordena lance da TT, capturas múltiplas, promoções e domínio do centro."""
    if uci_tt is not None and lance["uci"] == uci_tt:
        return 1_000_000

    score = 0
    if lance["captura"]:
        score += 10_000 + lance["qtd_capturas"] * 600
        for cap_idx in lance["capturados"]:
            if abs(board[cap_idx]) == 2:
                score += 250

    if lance["promocao"]:
        score += 900

    dest = lance["caminho"][-1]
    if dest in CASAS_CENTRAIS:
        score += 25

    return score


def _ordenar_lances(board, lances, uci_tt=None):
    lances.sort(key=lambda l: _prioridade_lance(board, l, uci_tt), reverse=True)
    return lances


def _quiescence(board, turno, alfa, beta, maximizando, cor_ia, metricas, deadline, prof_q=0):
    """
    Estende a busca enquanto houver capturas obrigatórias para evitar o efeito horizonte.
    """
    metricas["nos"] += 1
    if (metricas["nos"] & 1023) == 0 and time.perf_counter() >= deadline:
        raise BuscaTimeout()

    stand_pat = avaliar_tabuleiro(board, cor_ia)
    if prof_q >= 6:
        return stand_pat

    legais = gerar_lances_legais_board(board, turno)
    if not legais:
        return (-VITORIA_SCORE + prof_q) if turno == cor_ia else (VITORIA_SCORE - prof_q)

    # Só continua se a posição for taticamente instável (captura obrigatória ativa)
    if not legais[0]["captura"]:
        return stand_pat

    _ordenar_lances(board, legais)

    if maximizando:
        melhor = float("-inf")
        for lance in legais:
            undo = aplicar_lance_board(board, turno, lance)
            val = _quiescence(board, -turno, alfa, beta, False, cor_ia, metricas, deadline, prof_q + 1)
            desfazer_lance_board(board, lance, undo)
            if val > melhor:
                melhor = val
            alfa = max(alfa, melhor)
            if beta <= alfa:
                break
        return melhor
    else:
        melhor = float("inf")
        for lance in legais:
            undo = aplicar_lance_board(board, turno, lance)
            val = _quiescence(board, -turno, alfa, beta, True, cor_ia, metricas, deadline, prof_q + 1)
            desfazer_lance_board(board, lance, undo)
            if val < melhor:
                melhor = val
            beta = min(beta, melhor)
            if beta <= alfa:
                break
        return melhor


def minimax(board, turno, profundidade, alfa, beta, maximizando, cor_ia, metricas, tt, deadline):
    """Busca Minimax com Poda Alfa-Beta, Tabela de Transposição Zobrist e Quiescence Search."""
    metricas["nos"] += 1
    if (metricas["nos"] & 1023) == 0 and time.perf_counter() >= deadline:
        raise BuscaTimeout()

    legais = gerar_lances_legais_board(board, turno)
    if not legais:
        return (-VITORIA_SCORE - profundidade) if turno == cor_ia else (VITORIA_SCORE + profundidade)

    if profundidade <= 0:
        return _quiescence(board, turno, alfa, beta, maximizando, cor_ia, metricas, deadline)

    alfa_orig = alfa
    beta_orig = beta
    chave = _calcular_zobrist(board, turno)
    entrada_tt = tt.get(chave)
    uci_tt = None

    if entrada_tt is not None:
        tt_prof, tt_val, tt_flag, uci_tt = entrada_tt
        if tt_prof >= profundidade:
            if tt_flag == TT_EXACT:
                return tt_val
            if tt_flag == TT_ALPHA and tt_val <= alfa:
                return tt_val
            if tt_flag == TT_BETA and tt_val >= beta:
                return tt_val

    _ordenar_lances(board, legais, uci_tt)
    melhor_uci = None

    if maximizando:
        melhor = float("-inf")
        for lance in legais:
            undo = aplicar_lance_board(board, turno, lance)
            valor = minimax(board, -turno, profundidade - 1, alfa, beta, False, cor_ia, metricas, tt, deadline)
            desfazer_lance_board(board, lance, undo)
            if valor > melhor:
                melhor = valor
                melhor_uci = lance["uci"]
            alfa = max(alfa, melhor)
            if beta <= alfa:
                break
    else:
        melhor = float("inf")
        for lance in legais:
            undo = aplicar_lance_board(board, turno, lance)
            valor = minimax(board, -turno, profundidade - 1, alfa, beta, True, cor_ia, metricas, tt, deadline)
            desfazer_lance_board(board, lance, undo)
            if valor < melhor:
                melhor = valor
                melhor_uci = lance["uci"]
            beta = min(beta, melhor)
            if beta <= alfa:
                break

    if melhor <= alfa_orig:
        flag = TT_ALPHA
    elif melhor >= beta_orig:
        flag = TT_BETA
    else:
        flag = TT_EXACT

    if len(tt) < 80_000:
        tt[chave] = (profundidade, melhor, flag, melhor_uci)

    return melhor


def analisar_posicao(
    board,
    turno,
    cor_referencia=None,
    profundidade=6,
    limite_candidatos=5,
    tempo_limite_s=2.0,
    historico_fens=None,
):
    """
    Avalia os lances legais de `board` sob o ponto de vista de `cor_referencia`
    usando aprofundamento iterativo com limite de tempo.
    """
    if cor_referencia is None:
        cor_referencia = turno

    inicio = time.perf_counter()
    deadline = inicio + max(0.15, tempo_limite_s)
    metricas = {"nos": 0}
    tt = {}

    board_copia = board.copy()
    lances_raiz = _ordenar_lances(board_copia, gerar_lances_legais_board(board_copia, turno))

    if not lances_raiz:
        return {
            "avaliacoes": [],
            "todas_avaliacoes": [],
            "nos_avaliados": 0,
            "tempo_ms": 0,
            "profundidade": 0,
        }

    contagem_fens = {}
    if historico_fens:
        for f in historico_fens:
            if isinstance(f, str) and f.strip():
                k = _chave_posicao_fen(f)
                contagem_fens[k] = contagem_fens.get(k, 0) + 1

    melhor_mapa = {}
    profundidade_atingida = 1

    for prof_atual in range(1, max(1, profundidade) + 1):
        mapa_iteracao = {}
        try:
            prazo_atual = float("inf") if prof_atual == 1 else deadline

            for lance in lances_raiz:
                undo = aplicar_lance_board(board_copia, turno, lance)
                chave_pos = _chave_posicao_fen(gerar_fen(board_copia, -turno))
                repeticoes = contagem_fens.get(chave_pos, 0)

                if repeticoes >= 2:
                    valor = 0
                else:
                    valor = minimax(
                        board_copia,
                        turno=-turno,
                        profundidade=prof_atual - 1,
                        alfa=float("-inf"),
                        beta=float("inf"),
                        maximizando=False,
                        cor_ia=cor_referencia,
                        metricas=metricas,
                        tt=tt,
                        deadline=prazo_atual,
                    )
                    if repeticoes == 1 and valor > 30:
                        valor -= 50

                desfazer_lance_board(board_copia, lance, undo)
                mapa_iteracao[lance["uci"]] = (lance, valor)

            melhor_mapa = mapa_iteracao
            profundidade_atingida = prof_atual
            lances_raiz = [
                item[0]
                for item in sorted(melhor_mapa.values(), key=lambda x: x[1], reverse=True)
            ]
        except BuscaTimeout:
            break

    avaliacoes = []
    for uci, (lance, valor) in melhor_mapa.items():
        avaliacoes.append({
            "uci": uci,
            "notacao": lance["notacao"],
            "caminho": [rc_para_casa(*divmod(i, 8)) for i in lance["caminho"]],
            "captura": lance["captura"],
            "qtd_capturas": lance["qtd_capturas"],
            "promocao": lance["promocao"],
            "centipawns": valor,
            "pedras": round(valor / 100.0, 2),
            "vitoria_forcada": abs(valor) >= VITORIA_SCORE - 50,
        })

    avaliacoes.sort(key=lambda item: item["centipawns"], reverse=True)
    tempo_ms = round((time.perf_counter() - inicio) * 1000, 2)

    return {
        "avaliacoes": avaliacoes[:limite_candidatos],
        "todas_avaliacoes": avaliacoes,
        "nos_avaliados": metricas["nos"],
        "tempo_ms": tempo_ms,
        "profundidade": profundidade_atingida,
    }


def _gerar_diagnostico(escolhido, dificuldade, profundidade):
    cp = escolhido["centipawns"]
    notacao = escolhido["notacao"]

    prefixo = {
        "facil": "Modo Aprendiz",
        "medio": "Modo Desafiante",
        "mestre": f"Modo Mestre (Prof. {profundidade})",
    }.get(dificuldade, "Motor IA")

    if cp >= VITORIA_SCORE - 50:
        return f"{prefixo}: vitória forçada detectada com {notacao}!"
    if cp <= -VITORIA_SCORE + 50:
        return f"{prefixo}: defesa crítica ({notacao}), posição comprometida."
    if escolhido["qtd_capturas"] >= 2:
        return f"{prefixo}: golpe tático! Captura múltipla de {escolhido['qtd_capturas']} peças ({notacao}, {cp / 100:+.2f})."
    if escolhido["promocao"]:
        return f"{prefixo}: coroação de Dama executada ({notacao}, {cp / 100:+.2f})."
    if cp >= 250:
        return f"{prefixo}: vantagem material decisiva ({notacao}, {cp / 100:+.2f})."
    if cp >= 70:
        return f"{prefixo}: vantagem posicional e domínio diagonal ({notacao}, {cp / 100:+.2f})."
    if cp <= -250:
        return f"{prefixo}: em desvantagem, buscando contra-jogo ({notacao}, {cp / 100:+.2f})."
    if cp <= -70:
        return f"{prefixo}: adversário pressiona o centro ({notacao}, {cp / 100:+.2f})."
    return f"{prefixo}: equilíbrio dinâmico no tabuleiro ({notacao}, {cp / 100:+.2f})."


def melhor_jogada(partida_ou_board, turno=None, dificuldade="mestre", historico_fens=None):
    """
    Escolhe o lance da IA de acordo com o nível:
    - 'facil': profundidade 2 com variação exploratória
    - 'medio': profundidade 4 com variação tática ocasional
    - 'mestre': profundidade 7 (com orçamento de 2.0s), Quiescence Search e Poda Alfa-Beta completa
    """
    if hasattr(partida_ou_board, "board") and hasattr(partida_ou_board, "turno"):
        board = partida_ou_board.board
        cor_ia = partida_ou_board.turno
    else:
        board = partida_ou_board
        cor_ia = turno if turno is not None else 1

    lances_legais = gerar_lances_legais_board(board, cor_ia)
    if not lances_legais:
        return None, {}

    mapa_profundidade = {
        "facil": 2,
        "medio": 4,
        "mestre": 7,
    }
    mapa_tempo = {
        "facil": 0.4,
        "medio": 1.0,
        "mestre": 2.0,
    }
    profundidade = mapa_profundidade.get(dificuldade, 7)
    tempo_limite = mapa_tempo.get(dificuldade, 2.0)

    analise = analisar_posicao(
        board,
        turno=cor_ia,
        cor_referencia=cor_ia,
        profundidade=profundidade,
        limite_candidatos=len(lances_legais),
        tempo_limite_s=tempo_limite,
        historico_fens=historico_fens,
    )
    todas = analise["todas_avaliacoes"]

    if dificuldade == "facil" and len(todas) > 1 and random.random() < 0.60:
        escolhido = random.choice(todas[:min(5, len(todas))])
    elif dificuldade == "medio" and len(todas) > 1 and random.random() < 0.25:
        escolhido = random.choice(todas[:min(3, len(todas))])
    else:
        melhor_cp = todas[0]["centipawns"]
        empatados = [a for a in todas if a["centipawns"] == melhor_cp]
        escolhido = random.choice(empatados)

    eval_brancas = escolhido["centipawns"] if cor_ia == 1 else -escolhido["centipawns"]

    detalhes = {
        "uci": escolhido["uci"],
        "notacao": escolhido["notacao"],
        "caminho": escolhido["caminho"],
        "nos_avaliados": analise["nos_avaliados"],
        "tempo_ms": analise["tempo_ms"],
        "profundidade": analise["profundidade"],
        "avaliacao_brancas_cp": eval_brancas,
        "motivo": _gerar_diagnostico(escolhido, dificuldade, analise["profundidade"]),
        "candidatos": analise["avaliacoes"][:3],
    }

    return escolhido["uci"], detalhes
