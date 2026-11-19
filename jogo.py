"""
Regras e estado do Jogo de Damas Brasileiras (tabuleiro 8x8, dama voadora,
captura obrigatória, captura para trás e lei da maioria).
"""

import re

COLUNAS = "abcdefgh"

EMPTY = 0
W_MAN = 1
W_KING = 2
B_MAN = -1
B_KING = -2

FEN_INICIAL = "1b1b1b1b/b1b1b1b1/1b1b1b1b/8/8/w1w1w1w1/1w1w1w1w/w1w1w1w1 w 0"

CHAR_PARA_PECA = {
    "w": W_MAN,
    "W": W_KING,
    "b": B_MAN,
    "B": B_KING,
}

PECA_PARA_CHAR = {
    W_MAN: "w",
    W_KING: "W",
    B_MAN: "b",
    B_KING: "B",
}

DIRECOES_DIAGONAIS = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def casa_para_rc(casa):
    if not isinstance(casa, str) or len(casa) != 2:
        raise ValueError(f"Casa inválida: {casa}")
    col_ch = casa[0].lower()
    row_ch = casa[1]
    if col_ch not in COLUNAS or row_ch not in "12345678":
        raise ValueError(f"Casa fora do tabuleiro: {casa}")
    col = COLUNAS.index(col_ch)
    row = 8 - int(row_ch)
    return row, col


def rc_para_casa(row, col):
    return f"{COLUNAS[col]}{8 - row}"


def eh_casa_escura(row, col):
    return (row + col) % 2 == 1


def parse_fen(fen):
    if not isinstance(fen, str) or not fen.strip():
        raise ValueError("FEN inválido: deve ser uma string não vazia.")

    partes = fen.strip().split()
    if len(partes) not in (2, 3):
        raise ValueError("Formato de FEN inválido para Damas.")

    linhas = partes[0].split("/")
    if len(linhas) != 8:
        raise ValueError("FEN deve conter 8 linhas separadas por '/'.")

    board = [EMPTY] * 64
    qtd_brancas = 0
    qtd_pretas = 0

    for r, linha in enumerate(linhas):
        c = 0
        for ch in linha:
            if ch.isdigit():
                n = int(ch)
                if n < 1 or n > 8:
                    raise ValueError("Número inválido no FEN.")
                c += n
            elif ch in CHAR_PARA_PECA:
                if c >= 8:
                    raise ValueError("Linha excede 8 colunas no FEN.")
                if not eh_casa_escura(r, c):
                    raise ValueError(f"Peça posicionada em casa clara inválida ({rc_para_casa(r, c)}).")
                peca = CHAR_PARA_PECA[ch]
                board[r * 8 + c] = peca
                if peca > 0:
                    qtd_brancas += 1
                else:
                    qtd_pretas += 1
                c += 1
            else:
                raise ValueError(f"Caractere inválido no FEN: '{ch}'.")
        if c != 8:
            raise ValueError("Linha incompleta no FEN.")

    if qtd_brancas == 0 and qtd_pretas == 0:
        raise ValueError("Posição FEN ilegal: tabuleiro sem peças.")

    turno_ch = partes[1].lower()
    if turno_ch not in ("w", "b"):
        raise ValueError("Turno inválido no FEN (use 'w' ou 'b').")
    turno = 1 if turno_ch == "w" else -1

    sem_progresso = 0
    if len(partes) == 3:
        if not partes[2].isdigit():
            raise ValueError("Contador de lances sem progresso inválido no FEN.")
        sem_progresso = int(partes[2])

    return board, turno, sem_progresso


def gerar_fen(board, turno, sem_progresso=0):
    linhas = []
    for r in range(8):
        vazias = 0
        s = []
        for c in range(8):
            p = board[r * 8 + c]
            if p == EMPTY:
                vazias += 1
            else:
                if vazias:
                    s.append(str(vazias))
                    vazias = 0
                s.append(PECA_PARA_CHAR[p])
        if vazias:
            s.append(str(vazias))
        linhas.append("".join(s))
    turno_ch = "w" if turno == 1 else "b"
    return f"{'/'.join(linhas)} {turno_ch} {sem_progresso}"


def _gerar_capturas_peca(board, idx, peca, turno, capturadas_set):
    """
    Gera recursivamente todas as sequências de captura a partir de `idx`.
    Retorna lista de tuplas: (caminho_indices, tuple_capturados_indices).
    """
    r, c = divmod(idx, 8)
    eh_dama = abs(peca) == 2
    sequencias = []

    if not eh_dama:
        for dr, dc in DIRECOES_DIAGONAIS:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if 0 <= lr < 8 and 0 <= lc < 8:
                mid_idx = mr * 8 + mc
                land_idx = lr * 8 + lc
                mid_peca = board[mid_idx]
                if (
                    mid_peca != EMPTY
                    and (mid_peca * turno) < 0
                    and mid_idx not in capturadas_set
                    and board[land_idx] == EMPTY
                ):
                    board[idx] = EMPTY
                    board[land_idx] = peca
                    novo_cap = capturadas_set | {mid_idx}

                    sub = _gerar_capturas_peca(board, land_idx, peca, turno, novo_cap)
                    if sub:
                        for sub_cam, sub_caps in sub:
                            sequencias.append(([idx] + sub_cam, (mid_idx,) + sub_caps))
                    else:
                        sequencias.append(([idx, land_idx], (mid_idx,)))

                    board[land_idx] = EMPTY
                    board[idx] = peca
    else:
        for dr, dc in DIRECOES_DIAGONAIS:
            step = 1
            inimigo_idx = None
            while True:
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                cur_idx = nr * 8 + nc
                cur_peca = board[cur_idx]
                if cur_peca == EMPTY:
                    step += 1
                    continue
                if (cur_peca * turno) > 0 or cur_idx in capturadas_set:
                    break
                inimigo_idx = cur_idx
                step += 1
                break

            if inimigo_idx is not None:
                while True:
                    lr, lc = r + dr * step, c + dc * step
                    if not (0 <= lr < 8 and 0 <= lc < 8):
                        break
                    land_idx = lr * 8 + lc
                    if board[land_idx] != EMPTY:
                        break

                    board[idx] = EMPTY
                    board[land_idx] = peca
                    novo_cap = capturadas_set | {inimigo_idx}

                    sub = _gerar_capturas_peca(board, land_idx, peca, turno, novo_cap)
                    if sub:
                        for sub_cam, sub_caps in sub:
                            sequencias.append(([idx] + sub_cam, (inimigo_idx,) + sub_caps))
                    else:
                        sequencias.append(([idx, land_idx], (inimigo_idx,)))

                    board[land_idx] = EMPTY
                    board[idx] = peca
                    step += 1

    return sequencias


def gerar_lances_legais_board(board, turno):
    """
    Retorna lista de dicts representando todos os lances legais no estado atual,
    aplicando captura obrigatória e Lei da Maioria.
    """
    todas_capturas = []
    for idx, peca in enumerate(board):
        if peca != EMPTY and (peca * turno) > 0:
            seqs = _gerar_capturas_peca(board, idx, peca, turno, frozenset())
            for caminho, capturados in seqs:
                todas_capturas.append((caminho, capturados, peca))

    if todas_capturas:
        max_caps = max(len(c[1]) for c in todas_capturas)
        melhores = [c for c in todas_capturas if len(c[1]) == max_caps]
        lances = []
        for caminho, capturados, peca in melhores:
            dest_r = caminho[-1] // 8
            promove = abs(peca) == 1 and ((turno == 1 and dest_r == 0) or (turno == -1 and dest_r == 7))
            casas = [rc_para_casa(*divmod(i, 8)) for i in caminho]
            notacao = "×".join(casas)
            uci = "x".join(casas)
            lances.append({
                "uci": uci,
                "notacao": notacao,
                "caminho": caminho,
                "capturados": list(capturados),
                "captura": True,
                "qtd_capturas": len(capturados),
                "promocao": promove,
            })
        return lances

    lances_simples = []
    for idx, peca in enumerate(board):
        if peca == EMPTY or (peca * turno) <= 0:
            continue
        r, c = divmod(idx, 8)
        eh_dama = abs(peca) == 2

        if not eh_dama:
            dr = -1 if turno == 1 else 1
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    dest_idx = nr * 8 + nc
                    if board[dest_idx] == EMPTY:
                        promove = (turno == 1 and nr == 0) or (turno == -1 and nr == 7)
                        c_orig = rc_para_casa(r, c)
                        c_dest = rc_para_casa(nr, nc)
                        lances_simples.append({
                            "uci": f"{c_orig}-{c_dest}",
                            "notacao": f"{c_orig}→{c_dest}",
                            "caminho": [idx, dest_idx],
                            "capturados": [],
                            "captura": False,
                            "qtd_capturas": 0,
                            "promocao": promove,
                        })
        else:
            for dr, dc in DIRECOES_DIAGONAIS:
                step = 1
                while True:
                    nr, nc = r + dr * step, c + dc * step
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    dest_idx = nr * 8 + nc
                    if board[dest_idx] != EMPTY:
                        break
                    c_orig = rc_para_casa(r, c)
                    c_dest = rc_para_casa(nr, nc)
                    lances_simples.append({
                        "uci": f"{c_orig}-{c_dest}",
                        "notacao": f"{c_orig}→{c_dest}",
                        "caminho": [idx, dest_idx],
                        "capturados": [],
                        "captura": False,
                        "qtd_capturas": 0,
                        "promocao": False,
                    })
                    step += 1

    return lances_simples


def aplicar_lance_board(board, turno, lance):
    """
    Aplica `lance` in-place em `board` e retorna info para desfazer:
    (peca_original, capturadas_com_peca).
    """
    caminho = lance["caminho"]
    orig_idx = caminho[0]
    dest_idx = caminho[-1]
    peca_orig = board[orig_idx]

    capturadas_info = [(cap_idx, board[cap_idx]) for cap_idx in lance["capturados"]]
    for cap_idx, _ in capturadas_info:
        board[cap_idx] = EMPTY

    board[orig_idx] = EMPTY
    nova_peca = (W_KING if turno == 1 else B_KING) if lance["promocao"] else peca_orig
    board[dest_idx] = nova_peca

    return peca_orig, capturadas_info


def desfazer_lance_board(board, lance, undo_info):
    peca_orig, capturadas_info = undo_info
    caminho = lance["caminho"]
    board[caminho[-1]] = EMPTY
    board[caminho[0]] = peca_orig
    for cap_idx, cap_peca in capturadas_info:
        board[cap_idx] = cap_peca


class PartidaDamas:
    def __init__(self, fen=None):
        if fen is None:
            self.board, self.turno, self.sem_progresso = parse_fen(FEN_INICIAL)
        else:
            self.board, self.turno, self.sem_progresso = parse_fen(fen)

    def fen(self):
        return gerar_fen(self.board, self.turno, self.sem_progresso)

    def copiar(self):
        return PartidaDamas(self.fen())

    def turno_cor(self):
        return "brancas" if self.turno == 1 else "pretas"

    def lances_legais(self):
        return gerar_lances_legais_board(self.board, self.turno)

    def _normalizar_entrada_lance(self, texto):
        limpo = texto.strip().lower().replace("×", "x").replace("→", "-").replace(" ", "-")
        if "-" not in limpo and "x" not in limpo and len(limpo) >= 4 and len(limpo) % 2 == 0:
            return [limpo[i:i + 2] for i in range(0, len(limpo), 2)]
        return [p for p in re.split(r"[-x]+", limpo) if p]

    def jogar(self, lance_str):
        if not isinstance(lance_str, str) or not lance_str.strip():
            raise ValueError("Lance não informado ou inválido.")

        legais = self.lances_legais()
        if not legais:
            raise ValueError("Não há lances legais disponíveis nesta posição.")

        partes = self._normalizar_entrada_lance(lance_str)
        if len(partes) < 2:
            raise ValueError(f"Formato de lance inválido: {lance_str}")

        try:
            indices_entrada = [casa_para_rc(p)[0] * 8 + casa_para_rc(p)[1] for p in partes]
        except ValueError as exc:
            raise ValueError(f"Coordenada inválida no lance: {lance_str}") from exc

        correspondente = None
        for l in legais:
            if l["caminho"] == indices_entrada:
                correspondente = l
                break

        # Permite atalho origem-destino quando não há ambiguidade na sequência
        if correspondente is None and len(indices_entrada) == 2:
            candidatos = [
                l for l in legais
                if l["caminho"][0] == indices_entrada[0] and l["caminho"][-1] == indices_entrada[1]
            ]
            if len(candidatos) == 1:
                correspondente = candidatos[0]
            elif len(candidatos) > 1:
                raise ValueError("Lance ambíguo: especifique a casa intermediária da captura.")

        if correspondente is None:
            tem_cap = any(l["captura"] for l in legais)
            if tem_cap:
                raise ValueError("Lance ilegal: captura obrigatória (ou Lei da Maioria) ativa.")
            raise ValueError(f"Lance ilegal na posição atual: {lance_str}")

        peca_movida = self.board[correspondente["caminho"][0]]
        aplicar_lance_board(self.board, self.turno, correspondente)

        if correspondente["captura"] or abs(peca_movida) == 1:
            self.sem_progresso = 0
        else:
            self.sem_progresso += 1

        self.turno = -self.turno

        return {
            "uci": correspondente["uci"],
            "notacao": correspondente["notacao"],
            "captura": correspondente["captura"],
            "qtd_capturas": correspondente["qtd_capturas"],
            "promocao": correspondente["promocao"],
            "caminho": [rc_para_casa(*divmod(i, 8)) for i in correspondente["caminho"]],
            "capturados": [rc_para_casa(*divmod(i, 8)) for i in correspondente["capturados"]],
        }

    def estado_jogo(self, historico_fens=None):
        legais = self.lances_legais()
        pecas_b = sum(1 for p in self.board if p > 0)
        pecas_p = sum(1 for p in self.board if p < 0)
        damas_b = sum(1 for p in self.board if p == W_KING)
        damas_p = sum(1 for p in self.board if p == B_KING)

        terminou = False
        vencedor = None
        motivo_fim = None

        if pecas_b == 0:
            terminou = True
            vencedor = "pretas"
            motivo_fim = "Todas as peças brancas capturadas"
        elif pecas_p == 0:
            terminou = True
            vencedor = "brancas"
            motivo_fim = "Todas as peças pretas capturadas"
        elif not legais:
            terminou = True
            vencedor = "pretas" if self.turno == 1 else "brancas"
            motivo_fim = "Adversário sem movimentos legais (bloqueio)"
        elif self.sem_progresso >= 50:
            terminou = True
            vencedor = "empate"
            motivo_fim = "Regra dos 25 lances sem captura ou avanço de pedra"
        elif historico_fens:
            chave_atual = " ".join(self.fen().split()[:2])
            reps = sum(
                1 for f in historico_fens
                if isinstance(f, str) and " ".join(f.split()[:2]) == chave_atual
            )
            if reps >= 3:
                terminou = True
                vencedor = "empate"
                motivo_fim = "Repetição tripla da posição"

        captura_obrigatoria = any(l["captura"] for l in legais) if not terminou else False

        return {
            "fen": self.fen(),
            "turno": self.turno_cor(),
            "lances_legais": [
                {
                    "uci": l["uci"],
                    "notacao": l["notacao"],
                    "caminho": [rc_para_casa(*divmod(i, 8)) for i in l["caminho"]],
                    "capturados": [rc_para_casa(*divmod(i, 8)) for i in l["capturados"]],
                    "captura": l["captura"],
                    "qtd_capturas": l["qtd_capturas"],
                    "promocao": l["promocao"],
                }
                for l in legais
            ],
            "captura_obrigatoria": captura_obrigatoria,
            "pecas_brancas": pecas_b,
            "pecas_pretas": pecas_p,
            "damas_brancas": damas_b,
            "damas_pretas": damas_p,
            "terminou": terminou,
            "vencedor": vencedor,
            "motivo_fim": motivo_fim,
        }
