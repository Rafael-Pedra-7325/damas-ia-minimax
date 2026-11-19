"""
IA de Damas Brasileiras — Interface de Terminal (CLI).
Permite jogar contra o motor Minimax + Poda Alfa-Beta diretamente no console.
"""

from jogo import PartidaDamas, W_MAN, W_KING, B_MAN, B_KING, eh_casa_escura
from ia import melhor_jogada

SIMBOLOS_PECAS = {
    W_MAN: "⚪",
    W_KING: "👑",
    B_MAN: "⚫",
    B_KING: "♛ ",
}


def exibir_tabuleiro(partida):
    print("\n     a  b  c  d  e  f  g  h")
    print("   ┌─────────────────────────┐")
    for rank in range(7, -1, -1):
        row = 7 - rank
        linha = []
        for col in range(8):
            peca = partida.board[row * 8 + col]
            if peca != 0:
                linha.append(SIMBOLOS_PECAS[peca])
            elif eh_casa_escura(row, col):
                linha.append("· ")
            else:
                linha.append("  ")
        print(f" {rank + 1} │ {' '.join(linha)}│ {rank + 1}")
    print("   └─────────────────────────┘")
    print("     a  b  c  d  e  f  g  h\n")


def jogar():
    print("╔══════════════════════════════════════════╗")
    print("║    ⚪⚫ IA DE DAMAS BRASILEIRAS          ║")
    print("╚══════════════════════════════════════════╝")
    print("Nível: [1] Fácil  [2] Médio  [3] Mestre")
    dif = {"1": "facil", "2": "medio", "3": "mestre"}.get(input("Opção [3]: ").strip(), "mestre")

    cor = input("Jogar com [B]rancas ou [P]retas? [B]: ").strip().upper()
    ia_joga_brancas = cor == "P"

    partida = PartidaDamas()
    historico_fens = [partida.fen()]

    while not partida.estado_jogo(historico_fens)["terminou"]:
        exibir_tabuleiro(partida)
        estado = partida.estado_jogo(historico_fens)
        turno_ia = (partida.turno == 1 and ia_joga_brancas) or (partida.turno == -1 and not ia_joga_brancas)

        if turno_ia:
            lance_uci, detalhes = melhor_jogada(partida, dificuldade=dif, historico_fens=historico_fens)
            info = partida.jogar(lance_uci)
            historico_fens.append(partida.fen())
            print(
                f"🤖 IA jogou: {info['notacao']} — "
                f"{detalhes['nos_avaliados']} nós em {detalhes['tempo_ms']}ms ({detalhes['motivo']})"
            )
        else:
            opcoes = [l["notacao"] for l in estado["lances_legais"]]
            aviso = " [CAPTURA OBRIGATÓRIA]" if estado["captura_obrigatoria"] else ""
            print(f"Lances legais{aviso}: {', '.join(opcoes)}")
            while True:
                entrada = input("Seu lance (ex: c3-d4 ou c3xe5xg7): ").strip()
                try:
                    partida.jogar(entrada)
                    historico_fens.append(partida.fen())
                    break
                except ValueError as e:
                    print(f"Erro: {e}")

    exibir_tabuleiro(partida)
    estado = partida.estado_jogo(historico_fens)
    print(f"Fim de jogo ({estado['motivo_fim']}) — Vencedor: {estado['vencedor']}")


if __name__ == "__main__":
    jogar()
