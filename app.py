"""
Servidor Web Flask para a IA de Damas Brasileiras (Minimax + Poda Alfa-Beta + Quiescence).
Pronto para deploy no Render, Railway, PythonAnywhere, Fly.io ou execução local.
"""

import os
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from jogo import PartidaDamas
from ia import melhor_jogada, analisar_posicao, avaliar_tabuleiro

app = Flask(__name__)

DIFICULDADES_VALIDAS = {"facil", "medio", "mestre"}


def _carregar_partida(fen):
    if not isinstance(fen, str) or not fen.strip():
        return None
    try:
        return PartidaDamas(fen)
    except ValueError:
        return None


@app.errorhandler(HTTPException)
def handle_http_exception(err):
    if request.path.startswith("/api/"):
        return jsonify({"erro": err.description or "Erro na requisição."}), err.code
    return err


@app.errorhandler(Exception)
def handle_unexpected_exception(err):
    app.logger.exception("Erro interno inesperado: %s", err)
    if request.path.startswith("/api/"):
        return jsonify({"erro": "Erro interno no servidor de damas. Tente novamente."}), 500
    return "Erro interno no servidor.", 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "engine": "damas-minimax-alpha-beta"})


@app.route("/api/validar", methods=["POST"])
def api_validar():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Corpo JSON inválido."}), 400

    fen = dados.get("fen")
    lance = dados.get("lance")

    partida = _carregar_partida(fen)
    if partida is None:
        return jsonify({"erro": "FEN inválido."}), 400

    try:
        info_lance = partida.jogar(lance)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400

    eval_brancas = avaliar_tabuleiro(partida.board, 1)

    return jsonify({
        "lance": info_lance,
        "estado": partida.estado_jogo(),
        "avaliacao_brancas_cp": eval_brancas,
    })


@app.route("/api/jogada", methods=["POST"])
def api_jogada():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Corpo JSON inválido."}), 400

    fen = dados.get("fen")
    dificuldade = dados.get("dificuldade", "mestre")
    historico_fens = dados.get("historico_fens")

    if dificuldade not in DIFICULDADES_VALIDAS:
        dificuldade = "mestre"

    if not isinstance(historico_fens, list):
        historico_fens = []

    partida = _carregar_partida(fen)
    if partida is None:
        return jsonify({"erro": "FEN inválido."}), 400

    estado_atual = partida.estado_jogo(historico_fens)
    if estado_atual["terminou"]:
        return jsonify({
            "lance": None,
            "estado": estado_atual,
            "telemetria": None,
        })

    lance_uci, detalhes = melhor_jogada(
        partida,
        dificuldade=dificuldade,
        historico_fens=historico_fens,
    )
    if not lance_uci:
        return jsonify({
            "lance": None,
            "estado": partida.estado_jogo(historico_fens),
            "telemetria": None,
        })

    info_lance = partida.jogar(lance_uci)
    novo_historico = historico_fens + [partida.fen()]

    return jsonify({
        "lance": info_lance,
        "estado": partida.estado_jogo(novo_historico),
        "telemetria": {
            "nos_avaliados": detalhes.get("nos_avaliados", 0),
            "tempo_ms": detalhes.get("tempo_ms", 0),
            "profundidade": detalhes.get("profundidade", 1),
            "avaliacao_brancas_cp": detalhes.get("avaliacao_brancas_cp", 0),
            "motivo": detalhes.get("motivo", ""),
            "candidatos": detalhes.get("candidatos", []),
            "dificuldade": dificuldade,
        },
    })


@app.route("/api/analisar", methods=["POST"])
def api_analisar():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Corpo JSON inválido."}), 400

    fen = dados.get("fen")

    partida = _carregar_partida(fen)
    if partida is None:
        return jsonify({"erro": "FEN inválido."}), 400

    estado = partida.estado_jogo()
    if estado["terminou"]:
        return jsonify({
            "avaliacoes": [],
            "melhor_lance": None,
            "lances_legais": [],
            "nos_avaliados": 0,
            "tempo_ms": 0,
        })

    resultado = analisar_posicao(
        partida.board,
        partida.turno,
        cor_referencia=partida.turno,
        profundidade=5,
        limite_candidatos=4,
        tempo_limite_s=0.9,
    )
    melhor = resultado["avaliacoes"][0] if resultado["avaliacoes"] else None

    return jsonify({
        "avaliacoes": resultado["avaliacoes"],
        "melhor_lance": melhor,
        "lances_legais": estado["lances_legais"],
        "captura_obrigatoria": estado["captura_obrigatoria"],
        "nos_avaliados": resultado["nos_avaliados"],
        "tempo_ms": resultado["tempo_ms"],
    })


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
