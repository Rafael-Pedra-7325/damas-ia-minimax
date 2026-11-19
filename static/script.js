(() => {
  const FEN_INICIAL = "1b1b1b1b/b1b1b1b1/1b1b1b1b/8/8/w1w1w1w1/1w1w1w1w/w1w1w1w1 w 0";
  const ARQUIVOS = ["a", "b", "c", "d", "e", "f", "g", "h"];

  const PECAS_SVG = {
    w: `<svg class="piece-svg" viewBox="0 0 100 100">
          <defs>
            <radialGradient id="gradW" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stop-color="#ffffff"/>
              <stop offset="65%" stop-color="#e2e8f0"/>
              <stop offset="100%" stop-color="#94a3b8"/>
            </radialGradient>
          </defs>
          <circle cx="50" cy="52" r="38" fill="#64748b"/>
          <circle cx="50" cy="48" r="38" fill="url(#gradW)" stroke="#0f172a" stroke-width="3"/>
          <circle cx="50" cy="48" r="27" fill="none" stroke="#94a3b8" stroke-width="2.5"/>
          <circle cx="50" cy="48" r="17" fill="none" stroke="#cbd5e1" stroke-width="2"/>
        </svg>`,
    W: `<svg class="piece-svg" viewBox="0 0 100 100">
          <defs>
            <radialGradient id="gradWK" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stop-color="#ffffff"/>
              <stop offset="65%" stop-color="#e2e8f0"/>
              <stop offset="100%" stop-color="#94a3b8"/>
            </radialGradient>
          </defs>
          <circle cx="50" cy="53" r="38" fill="#64748b"/>
          <circle cx="50" cy="48" r="38" fill="url(#gradWK)" stroke="#fbbf24" stroke-width="4"/>
          <circle cx="50" cy="48" r="28" fill="none" stroke="#f59e0b" stroke-width="2"/>
          <path d="M31 57 L35 38 L44 47 L50 34 L56 47 L65 38 L69 57 Z" fill="#f59e0b" stroke="#0f172a" stroke-width="2" stroke-linejoin="round"/>
        </svg>`,
    b: `<svg class="piece-svg" viewBox="0 0 100 100">
          <defs>
            <radialGradient id="gradB" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stop-color="#334155"/>
              <stop offset="60%" stop-color="#1e293b"/>
              <stop offset="100%" stop-color="#090d16"/>
            </radialGradient>
          </defs>
          <circle cx="50" cy="52" r="38" fill="#020617"/>
          <circle cx="50" cy="48" r="38" fill="url(#gradB)" stroke="#020617" stroke-width="3"/>
          <circle cx="50" cy="48" r="27" fill="none" stroke="#475569" stroke-width="2.5"/>
          <circle cx="50" cy="48" r="17" fill="none" stroke="#38bdf8" stroke-width="1.8" opacity="0.65"/>
        </svg>`,
    B: `<svg class="piece-svg" viewBox="0 0 100 100">
          <defs>
            <radialGradient id="gradBK" cx="35%" cy="30%" r="70%">
              <stop offset="0%" stop-color="#334155"/>
              <stop offset="60%" stop-color="#1e293b"/>
              <stop offset="100%" stop-color="#090d16"/>
            </radialGradient>
          </defs>
          <circle cx="50" cy="53" r="38" fill="#020617"/>
          <circle cx="50" cy="48" r="38" fill="url(#gradBK)" stroke="#fbbf24" stroke-width="4"/>
          <circle cx="50" cy="48" r="28" fill="none" stroke="#f59e0b" stroke-width="2"/>
          <path d="M31 57 L35 38 L44 47 L50 34 L56 47 L65 38 L69 57 Z" fill="#fbbf24" stroke="#0f172a" stroke-width="2" stroke-linejoin="round"/>
        </svg>`,
  };

  const LANCES_INICIAIS = [
    { uci: "a3-b4", notacao: "a3→b4", caminho: ["a3", "b4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
    { uci: "c3-b4", notacao: "c3→b4", caminho: ["c3", "b4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
    { uci: "c3-d4", notacao: "c3→d4", caminho: ["c3", "d4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
    { uci: "e3-d4", notacao: "e3→d4", caminho: ["e3", "d4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
    { uci: "e3-f4", notacao: "e3→f4", caminho: ["e3", "f4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
    { uci: "g3-f4", notacao: "g3→f4", caminho: ["g3", "f4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
    { uci: "g3-h4", notacao: "g3→h4", caminho: ["g3", "h4"], capturados: [], captura: false, qtd_capturas: 0, promocao: false },
  ];

  const estado = {
    partidaId: 0,
    fen: FEN_INICIAL,
    turno: "brancas",
    corHumano: "brancas",
    invertido: false,
    dificuldade: "mestre",
    lancesLegais: [...LANCES_INICIAIS],
    capturaObrigatoria: false,
    casaSelecionada: null,
    caminhoParcial: [],
    ultimoCaminho: [],
    evalBrancasCp: 0,
    bloqueado: false,
    terminou: false,
    modoRaioX: false,
    somAtivo: true,
    pilhaEstados: [],
    historicoNotacao: [],
    historicoFens: [FEN_INICIAL],
    placar: { vitorias: 0, empates: 0, derrotas: 0 },
  };

  let abortControllerAtivo = null;

  const tabuleiroEl = document.getElementById("tabuleiro");
  const setasSvg = document.getElementById("setas-svg");
  const statusBanner = document.getElementById("status-banner");
  const statusTexto = document.getElementById("status-texto");
  const evalBarFill = document.getElementById("eval-bar-fill");
  const evalBarLabel = document.getElementById("eval-bar-label");
  const placarEvalEl = document.getElementById("placar-eval");
  const telNosEl = document.getElementById("tel-nos");
  const telTempoEl = document.getElementById("tel-tempo");
  const telMotivoEl = document.getElementById("tel-motivo");
  const listaHistoricoEl = document.getElementById("lista-historico");

  let audioCtx = null;
  function tocarSom(tipo) {
    if (!estado.somAtivo) return;
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      const t = audioCtx.currentTime;

      if (tipo === "move") {
        osc.type = "triangle";
        osc.frequency.setValueAtTime(300, t);
        osc.frequency.exponentialRampToValueAtTime(170, t + 0.07);
        gain.gain.setValueAtTime(0.09, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.08);
        osc.start(t);
        osc.stop(t + 0.08);
      } else if (tipo === "capture") {
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(480, t);
        osc.frequency.exponentialRampToValueAtTime(150, t + 0.12);
        gain.gain.setValueAtTime(0.09, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.13);
        osc.start(t);
        osc.stop(t + 0.13);
      } else if (tipo === "promote") {
        osc.type = "sine";
        osc.frequency.setValueAtTime(523.25, t);
        osc.frequency.setValueAtTime(659.25, t + 0.08);
        osc.frequency.setValueAtTime(783.99, t + 0.16);
        gain.gain.setValueAtTime(0.11, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + 0.28);
        osc.start(t);
        osc.stop(t + 0.28);
      }
    } catch (_) {}
  }

  function cancelarRequisicaoAtiva() {
    if (abortControllerAtivo) {
      try {
        abortControllerAtivo.abort();
      } catch (_) {}
      abortControllerAtivo = null;
    }
  }

  async function fetchApiSegura(url, payload, { tentativas = 2, timeoutMs = 25000 } = {}) {
    cancelarRequisicaoAtiva();
    const controller = new AbortController();
    abortControllerAtivo = controller;

    for (let tentativa = 1; tentativa <= tentativas; tentativa++) {
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        clearTimeout(timer);

        const textoBruto = await resp.text();
        let dados = null;
        try {
          dados = textoBruto ? JSON.parse(textoBruto) : {};
        } catch (_) {
          if (tentativa < tentativas && [502, 503, 504].includes(resp.status)) {
            atualizarStatus("⏳ Servidor acordando no Render, reconectando...", "turno-ia");
            await new Promise((r) => setTimeout(r, 1500));
            continue;
          }
          throw new Error("O servidor demorou a responder. Tente novamente.");
        }

        if (!resp.ok) {
          throw new Error(dados.erro || `Erro HTTP ${resp.status}`);
        }
        return dados;
      } catch (err) {
        clearTimeout(timer);
        if (err.name === "AbortError") throw err;
        if (tentativa < tentativas) {
          await new Promise((r) => setTimeout(r, 1200));
          continue;
        }
        throw err;
      }
    }
  }

  function carregarPlacar() {
    try {
      const salvo = localStorage.getItem("damas_ia_placar");
      if (salvo) estado.placar = { ...estado.placar, ...JSON.parse(salvo) };
    } catch (_) {}
    atualizarPlacarUI();
  }

  function salvarPlacar() {
    try {
      localStorage.setItem("damas_ia_placar", JSON.stringify(estado.placar));
    } catch (_) {}
    atualizarPlacarUI();
  }

  function atualizarPlacarUI() {
    document.getElementById("placar-vitorias").textContent = estado.placar.vitorias;
    document.getElementById("placar-empates").textContent = estado.placar.empates;
    document.getElementById("placar-derrotas").textContent = estado.placar.derrotas;
  }

  function parseFenMapa(fen) {
    const mapa = {};
    const parteTabuleiro = fen.split(" ")[0];
    const linhas = parteTabuleiro.split("/");
    linhas.forEach((linha, rIdx) => {
      const rank = 8 - rIdx;
      let fileIdx = 0;
      for (const ch of linha) {
        if (/\d/.test(ch)) {
          fileIdx += parseInt(ch, 10);
        } else {
          const casa = `${ARQUIVOS[fileIdx]}${rank}`;
          mapa[casa] = ch;
          fileIdx += 1;
        }
      }
    });
    return mapa;
  }

  function atualizarPecasCapturadas(mapa) {
    let brancasAtuais = 0;
    let pretasAtuais = 0;
    Object.values(mapa).forEach((ch) => {
      if (ch === "w" || ch === "W") brancasAtuais += 1;
      if (ch === "b" || ch === "B") pretasAtuais += 1;
    });

    const brancasPerdidas = Math.max(0, 12 - brancasAtuais);
    const pretasPerdidas = Math.max(0, 12 - pretasAtuais);

    const capHumano = estado.corHumano === "brancas" ? pretasPerdidas : brancasPerdidas;
    const capIA = estado.corHumano === "brancas" ? brancasPerdidas : pretasPerdidas;

    const simboloAlvo = estado.corHumano === "brancas" ? "⚫" : "⚪";
    const simboloProprio = estado.corHumano === "brancas" ? "⚪" : "⚫";

    document.getElementById("cap-humano").textContent =
      capHumano > 0 ? `${simboloAlvo.repeat(Math.min(capHumano, 6))} (${capHumano}/12)` : "—";
    document.getElementById("cap-ia").textContent =
      capIA > 0 ? `${simboloProprio.repeat(Math.min(capIA, 6))} (${capIA}/12)` : "—";
  }

  function atualizarBarraAvaliacao(cp) {
    estado.evalBrancasCp = cp;
    const pedras = (cp / 100).toFixed(2);
    placarEvalEl.textContent = cp > 0 ? `+${pedras}` : pedras;

    const clamped = Math.max(-1000, Math.min(1000, cp));
    const pctBrancas = 50 + 50 * (2 / (1 + Math.exp(-0.0045 * clamped)) - 1);
    evalBarFill.style.height = `${pctBrancas.toFixed(1)}%`;
    evalBarLabel.textContent = Math.abs(cp / 100).toFixed(1);
  }

  function lancesFiltradosPorSelecao() {
    if (!estado.casaSelecionada) return [];
    const prefixo = estado.caminhoParcial.length ? estado.caminhoParcial : [estado.casaSelecionada];
    return estado.lancesLegais.filter((l) => {
      if (l.caminho.length < prefixo.length) return false;
      return prefixo.every((casa, idx) => l.caminho[idx] === casa);
    });
  }

  function renderizarTabuleiro() {
    const mapaPecas = parseFenMapa(estado.fen);
    atualizarPecasCapturadas(mapaPecas);
    tabuleiroEl.innerHTML = "";
    setasSvg.innerHTML = "";

    const pecasObrigatorias = new Set();
    if (estado.capturaObrigatoria && estado.turno === estado.corHumano && !estado.terminou && !estado.bloqueado) {
      estado.lancesLegais.forEach((l) => pecasObrigatorias.add(l.caminho[0]));
    }

    const destinosFinais = new Map();
    const casasIntermediarias = new Set();

    const candidatosSelecao = lancesFiltradosPorSelecao();
    const passoAtual = estado.caminhoParcial.length ? estado.caminhoParcial.length : 1;

    candidatosSelecao.forEach((l) => {
      const destFinal = l.caminho[l.caminho.length - 1];
      destinosFinais.set(destFinal, l);
      if (l.caminho.length > passoAtual + 1) {
        casasIntermediarias.add(l.caminho[passoAtual]);
      }
    });

    const ranks = estado.invertido ? [1, 2, 3, 4, 5, 6, 7, 8] : [8, 7, 6, 5, 4, 3, 2, 1];
    const files = estado.invertido ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];

    ranks.forEach((rank, rVis) => {
      files.forEach((fIdx, cVis) => {
        const file = ARQUIVOS[fIdx];
        const casa = `${file}${rank}`;
        const row = 8 - rank;
        const isDark = (row + fIdx) % 2 === 1;

        const sqEl = document.createElement("div");
        sqEl.className = `square ${isDark ? "dark" : "light"}`;
        sqEl.dataset.square = casa;

        if (estado.casaSelecionada === casa) sqEl.classList.add("selected");
        if (estado.ultimoCaminho.includes(casa)) sqEl.classList.add("last-move");
        if (pecasObrigatorias.has(casa)) sqEl.classList.add("must-capture");

        if (cVis === 0) {
          const rLabel = document.createElement("span");
          rLabel.className = "coord-rank";
          rLabel.textContent = rank;
          sqEl.appendChild(rLabel);
        }
        if (rVis === 7) {
          const fLabel = document.createElement("span");
          fLabel.className = "coord-file";
          fLabel.textContent = file;
          sqEl.appendChild(fLabel);
        }

        const pecaCode = mapaPecas[casa];
        if (pecaCode && PECAS_SVG[pecaCode]) {
          sqEl.insertAdjacentHTML("beforeend", PECAS_SVG[pecaCode]);
        }

        if (destinosFinais.has(casa)) {
          const lanceAlvo = destinosFinais.get(casa);
          const ind = document.createElement("span");
          ind.className = lanceAlvo.captura ? "legal-capture-dot" : "legal-dot";
          sqEl.appendChild(ind);

          if (lanceAlvo.caminho.length > 2) {
            sqEl.addEventListener("mouseenter", () => desenharSetas([lanceAlvo], "#34d399"));
            sqEl.addEventListener("mouseleave", () => {
              if (estado.modoRaioX && !estado.terminou && !estado.bloqueado) atualizarRaioX();
              else setasSvg.innerHTML = "";
            });
          }
        } else if (casasIntermediarias.has(casa)) {
          const ind = document.createElement("span");
          ind.className = "step-dot";
          sqEl.appendChild(ind);
        }

        sqEl.addEventListener("click", () => aoClicarCasa(casa, pecaCode));
        tabuleiroEl.appendChild(sqEl);
      });
    });

    if (estado.modoRaioX && !estado.terminou && !estado.bloqueado) {
      atualizarRaioX();
    }
  }

  function desenharSetas(candidatos, corOverride = null) {
    setasSvg.innerHTML = "";
    if (!candidatos || !candidatos.length) return;

    const cor = corOverride || "#38bdf8";
    const defs = `<defs><marker id="arrowhead" markerWidth="4" markerHeight="4" refX="2.5" refY="2" orient="auto"><polygon points="0 0, 4 2, 0 4" fill="${cor}" /></marker></defs>`;
    setasSvg.insertAdjacentHTML("beforeend", defs);

    candidatos.slice(0, 3).forEach((cand, idx) => {
      const caminho = cand.caminho || cand.uci.split(/[-x]/);
      if (caminho.length < 2) return;

      const opacidade = idx === 0 ? 0.88 : 0.42;
      const largura = idx === 0 ? 13 : 8;

      for (let i = 0; i < caminho.length - 1; i++) {
        const [x1, y1] = centroCasaSvg(caminho[i]);
        const [x2, y2] = centroCasaSvg(caminho[i + 1]);
        const ehUltimoSegmento = i === caminho.length - 2;

        const line = document.createElementNS("[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)", "line");
        line.setAttribute("x1", x1);
        line.setAttribute("y1", y1);
        line.setAttribute("x2", x2);
        line.setAttribute("y2", y2);
        line.setAttribute("stroke", cor);
        line.setAttribute("stroke-width", largura);
        line.setAttribute("stroke-linecap", "round");
        line.setAttribute("opacity", opacidade);
        if (ehUltimoSegmento) {
          line.setAttribute("marker-end", "url(#arrowhead)");
        }
        setasSvg.appendChild(line);
      }
    });
  }

  function centroCasaSvg(casa) {
    const fIdx = ARQUIVOS.indexOf(casa[0]);
    const rank = parseInt(casa[1], 10);
    const col = estado.invertido ? 7 - fIdx : fIdx;
    const row = estado.invertido ? rank - 1 : 8 - rank;
    return [col * 100 + 50, row * 100 + 50];
  }

  function ehPecaDoHumano(pecaCode) {
    if (!pecaCode) return false;
    if (estado.corHumano === "brancas") return pecaCode === "w" || pecaCode === "W";
    return pecaCode === "b" || pecaCode === "B";
  }

  function aoClicarCasa(casa, pecaCode) {
    if (estado.bloqueado || estado.terminou || estado.turno !== estado.corHumano) return;

    if (estado.casaSelecionada) {
      const candidatos = lancesFiltradosPorSelecao();
      const passoAtual = estado.caminhoParcial.length ? estado.caminhoParcial.length : 1;

      // Verifica se clicou em uma casa intermediária de captura múltipla
      const comPassoIntermediario = candidatos.filter(
        (l) => l.caminho.length > passoAtual + 1 && l.caminho[passoAtual] === casa
      );
      if (comPassoIntermediario.length > 0) {
        estado.caminhoParcial = [...(estado.caminhoParcial.length ? estado.caminhoParcial : [estado.casaSelecionada]), casa];
        renderizarTabuleiro();
        return;
      }

      // Verifica se clicou no destino final de algum lance válido
      const finais = candidatos.filter((l) => l.caminho[l.caminho.length - 1] === casa);
      if (finais.length >= 1) {
        executarLanceHumano(finais[0].uci);
        return;
      }
    }

    if (ehPecaDoHumano(pecaCode)) {
      if (estado.casaSelecionada === casa) {
        estado.casaSelecionada = null;
        estado.caminhoParcial = [];
      } else {
        estado.casaSelecionada = casa;
        estado.caminhoParcial = [casa];
      }
      renderizarTabuleiro();
    } else {
      estado.casaSelecionada = null;
      estado.caminhoParcial = [];
      renderizarTabuleiro();
    }
  }

  async function executarLanceHumano(lanceUci) {
    const partidaAtual = estado.partidaId;
    estado.bloqueado = true;
    estado.casaSelecionada = null;
    estado.caminhoParcial = [];

    const snapshotAntesLance = {
      fen: estado.fen,
      lancesLegais: estado.lancesLegais,
      capturaObrigatoria: estado.capturaObrigatoria,
      historicoNotacao: [...estado.historicoNotacao],
      historicoFens: [...estado.historicoFens],
      ultimoCaminho: [...estado.ultimoCaminho],
      evalBrancasCp: estado.evalBrancasCp,
    };

    try {
      const dados = await fetchApiSegura("/api/validar", {
        fen: estado.fen,
        lance: lanceUci,
      });

      if (partidaAtual !== estado.partidaId) return;

      estado.pilhaEstados.push(snapshotAntesLance);
      estado.historicoFens.push(dados.estado.fen);
      aplicarRespostaEstado(dados.estado, dados.lance, dados.avaliacao_brancas_cp);

      if (!estado.terminou) {
        await turnoIA(partidaAtual);
      }
    } catch (e) {
      if (e.name === "AbortError" || partidaAtual !== estado.partidaId) return;
      estado.bloqueado = false;
      renderizarTabuleiro();
      atualizarStatus(`⚠️ ${e.message}`, "captura-alerta");
    }
  }

  async function turnoIA(partidaAtual = estado.partidaId) {
    estado.bloqueado = true;
    atualizarStatus("🤖 IA calculando variantes na árvore Minimax...", "turno-ia");

    try {
      const dados = await fetchApiSegura("/api/jogada", {
        fen: estado.fen,
        dificuldade: estado.dificuldade,
        historico_fens: estado.historicoFens.slice(-16),
      });

      if (partidaAtual !== estado.partidaId) return;

      if (dados.telemetria) {
        telNosEl.textContent = dados.telemetria.nos_avaliados.toLocaleString("pt-BR");
        telTempoEl.textContent = `${dados.telemetria.tempo_ms} ms`;
        telMotivoEl.textContent = dados.telemetria.motivo;
      }

      estado.historicoFens.push(dados.estado.fen);
      aplicarRespostaEstado(
        dados.estado,
        dados.lance,
        dados.telemetria ? dados.telemetria.avaliacao_brancas_cp : estado.evalBrancasCp
      );
    } catch (e) {
      if (e.name === "AbortError" || partidaAtual !== estado.partidaId) return;
      estado.bloqueado = false;
      renderizarTabuleiro();
      atualizarStatus(`⚠️ ${e.message} (Clique em Nova Partida ou Desfazer)`, "captura-alerta");
    }
  }

  function aplicarRespostaEstado(novoEstado, infoLance, evalBrancasCp) {
    estado.fen = novoEstado.fen;
    estado.turno = novoEstado.turno;
    estado.lancesLegais = novoEstado.lances_legais || [];
    estado.capturaObrigatoria = Boolean(novoEstado.captura_obrigatoria);
    estado.terminou = Boolean(novoEstado.terminou);
    estado.bloqueado = false;

    if (infoLance) {
      estado.ultimoCaminho = infoLance.caminho || [];
      estado.historicoNotacao.push(infoLance.notacao);
      atualizarHistoricoUI();

      if (infoLance.promocao) tocarSom("promote");
      else if (infoLance.captura) tocarSom("capture");
      else tocarSom("move");
    }

    if (typeof evalBrancasCp === "number") {
      atualizarBarraAvaliacao(evalBrancasCp);
    }

    renderizarTabuleiro();

    if (novoEstado.terminou) {
      if (novoEstado.vencedor === "empate") {
        estado.placar.empates += 1;
        atualizarStatus(`🤝 Empate por ${novoEstado.motivo_fim}!`, "captura-alerta");
      } else if (novoEstado.vencedor === estado.corHumano) {
        estado.placar.vitorias += 1;
        atualizarStatus(`🎉 Vitória! ${novoEstado.motivo_fim}!`, "resultado-vitoria");
      } else {
        estado.placar.derrotas += 1;
        atualizarStatus(`🤖 Fim de jogo (${novoEstado.motivo_fim}) — A IA venceu.`, "resultado-derrota");
      }
      salvarPlacar();
      return;
    }

    if (estado.turno === estado.corHumano) {
      if (estado.capturaObrigatoria) {
        atualizarStatus("⚡ Captura obrigatória ativa! Execute a tomada destacada.", "captura-alerta");
      } else {
        atualizarStatus("Sua vez! Selecione uma peça para mover.", "turno-humano");
      }
    }
  }

  function atualizarHistoricoUI() {
    if (!estado.historicoNotacao.length) {
      listaHistoricoEl.innerHTML = '<li class="empty-history">Nenhum lance realizado ainda.</li>';
      return;
    }
    listaHistoricoEl.innerHTML = "";
    for (let i = 0; i < estado.historicoNotacao.length; i += 2) {
      const num = Math.floor(i / 2) + 1;
      const branca = estado.historicoNotacao[i] || "";
      const preta = estado.historicoNotacao[i + 1] || "";
      const li = document.createElement("li");
      li.innerHTML = `<span>${num}.</span><strong>${branca}</strong><span>${preta}</span>`;
      listaHistoricoEl.appendChild(li);
    }
    listaHistoricoEl.scrollTop = listaHistoricoEl.scrollHeight;
  }

  function atualizarStatus(texto, classe) {
    statusTexto.textContent = texto;
    statusBanner.className = `status-banner ${classe}`;
  }

  async function atualizarRaioX() {
    const fenAlvo = estado.fen;
    const partidaAtual = estado.partidaId;
    try {
      const resp = await fetch("/api/analisar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: fenAlvo }),
      });
      const dados = await resp.json();
      if (
        resp.ok &&
        dados.avaliacoes &&
        partidaAtual === estado.partidaId &&
        fenAlvo === estado.fen &&
        estado.modoRaioX
      ) {
        desenharSetas(dados.avaliacoes);
      }
    } catch (_) {}
  }

  async function pedirDica() {
    if (estado.bloqueado || estado.terminou) return;
    const fenAlvo = estado.fen;
    const partidaAtual = estado.partidaId;
    try {
      const resp = await fetch("/api/analisar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: fenAlvo }),
      });
      const dados = await resp.json();
      if (!resp.ok || !dados.melhor_lance || partidaAtual !== estado.partidaId || fenAlvo !== estado.fen) {
        return;
      }

      desenharSetas([dados.melhor_lance]);
      const caminho = dados.melhor_lance.caminho;
      const origem = caminho[0];
      const destino = caminho[caminho.length - 1];
      tabuleiroEl.querySelectorAll(".square").forEach((s) => {
        s.classList.remove("hint-square");
        if (s.dataset.square === origem || s.dataset.square === destino) {
          s.classList.add("hint-square");
        }
      });
      telMotivoEl.textContent = `Dica tática: jogue ${dados.melhor_lance.notacao} (${dados.nos_avaliados.toLocaleString("pt-BR")} nós analisados).`;
    } catch (_) {}
  }

  async function iniciarNovaPartida() {
    cancelarRequisicaoAtiva();
    estado.partidaId += 1;
    const partidaAtual = estado.partidaId;

    estado.fen = FEN_INICIAL;
    estado.turno = "brancas";
    estado.casaSelecionada = null;
    estado.caminhoParcial = [];
    estado.ultimoCaminho = [];
    estado.capturaObrigatoria = false;
    estado.terminou = false;
    estado.bloqueado = false;
    estado.pilhaEstados = [];
    estado.historicoNotacao = [];
    estado.historicoFens = [FEN_INICIAL];
    estado.invertido = estado.corHumano === "pretas";
    estado.lancesLegais = [...LANCES_INICIAIS];

    atualizarHistoricoUI();
    atualizarBarraAvaliacao(0);
    telNosEl.textContent = "—";
    telTempoEl.textContent = "—";
    telMotivoEl.textContent = "Nova partida iniciada.";
    renderizarTabuleiro();

    if (estado.corHumano === "pretas") {
      await turnoIA(partidaAtual);
    } else {
      atualizarStatus("Sua vez! Selecione uma peça branca para jogar.", "turno-humano");
    }
  }

  async function desfazerJogada() {
    if (estado.bloqueado || !estado.pilhaEstados.length) return;

    const anterior = estado.pilhaEstados.pop();
    estado.fen = anterior.fen;
    estado.lancesLegais = anterior.lancesLegais;
    estado.capturaObrigatoria = anterior.capturaObrigatoria;
    estado.historicoNotacao = anterior.historicoNotacao;
    estado.historicoFens = anterior.historicoFens;
    estado.ultimoCaminho = anterior.ultimoCaminho;
    estado.terminou = false;
    estado.casaSelecionada = null;
    estado.caminhoParcial = [];
    estado.turno = estado.corHumano;

    atualizarHistoricoUI();
    atualizarBarraAvaliacao(anterior.evalBrancasCp || 0);
    renderizarTabuleiro();
    atualizarStatus("Jogada desfeita. Sua vez!", "turno-humano");
  }

  function configurarSegmented(id, cb) {
    const el = document.getElementById(id);
    el.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        el.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        cb(btn.dataset.value);
      });
    });
  }

  configurarSegmented("grupo-dificuldade", (v) => {
    estado.dificuldade = v;
    iniciarNovaPartida();
  });

  configurarSegmented("grupo-cor", (v) => {
    estado.corHumano = v;
    iniciarNovaPartida();
  });

  document.getElementById("btn-reiniciar").addEventListener("click", iniciarNovaPartida);
  document.getElementById("btn-desfazer").addEventListener("click", desfazerJogada);
  document.getElementById("btn-zerar-placar").addEventListener("click", () => {
    estado.placar = { vitorias: 0, empates: 0, derrotas: 0 };
    salvarPlacar();
  });

  document.getElementById("btn-inverter").addEventListener("click", () => {
    estado.invertido = !estado.invertido;
    renderizarTabuleiro();
  });

  const btnRaioX = document.getElementById("btn-raiox");
  btnRaioX.addEventListener("click", () => {
    estado.modoRaioX = !estado.modoRaioX;
    btnRaioX.classList.toggle("active", estado.modoRaioX);
    renderizarTabuleiro();
  });

  document.getElementById("btn-dica").addEventListener("click", pedirDica);

  const btnSom = document.getElementById("btn-som");
  btnSom.addEventListener("click", () => {
    estado.somAtivo = !estado.somAtivo;
    btnSom.textContent = estado.somAtivo ? "🔊" : "🔇";
  });

  document.getElementById("btn-copiar-fen").addEventListener("click", () => {
    navigator.clipboard?.writeText(estado.fen);
    telMotivoEl.textContent = "Código FEN copiado para a área de transferência!";
  });

  document.addEventListener("keydown", (e) => {
    if (e.key.toLowerCase() === "r") iniciarNovaPartida();
    if (e.key.toLowerCase() === "z") desfazerJogada();
  });

  carregarPlacar();
  iniciarNovaPartida();
})();
