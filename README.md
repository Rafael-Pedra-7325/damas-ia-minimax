# ⚪⚫ IA de Damas Brasileiras — Minimax + Poda Alfa-Beta + Quiescence

Aplicação Web e CLI em Python (Flask + motor próprio em Python puro) com Inteligência Artificial baseada em **Minimax com Poda Alfa-Beta**, **Busca de Quiescência** para sequências de captura, **Aprofundamento Iterativo** com orçamento de tempo e **Tabela de Transposição Zobrist**.

## ✨ Funcionalidades
- **Regras Oficiais de Damas Brasileiras (8x8)**: captura obrigatória, captura para trás, captura em cadeia (múltipla), **Lei da Maioria** e **Dama Voadora** (movimento e captura de longo alcance nas diagonais).
- **Tabuleiro Interativo & UX Inteligente**: peças vetoriais SVG esculpidas com coroa dourada para Damas, destaque automático de peças com captura obrigatória, pré-visualização de trajetórias em saltos múltiplos, inversão de lado e desfazer jogada (`Z`).
- **Barra de Avaliação em Tempo Real**: exibe a vantagem em pedras (centipawns) lance a lance.
- **Cérebro da IA & Visão Raio-X**: desenha setas com as 3 melhores variantes calculadas, mostra nós analisados, profundidade atingida e diagnóstico tático em milissegundos.
- **3 Níveis de Dificuldade**: Fácil (Aprendiz), Médio (Desafiante) e Mestre.

## 🚀 Como Executar Localmente
```bash
pip install -r requirements.txt
python app.py
