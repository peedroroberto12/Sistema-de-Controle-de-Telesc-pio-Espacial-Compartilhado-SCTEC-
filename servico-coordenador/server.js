// Serviço Coordenador (o "Porteiro") - Entrega 3
// Só sabe travar e destravar recursos. Não conhece telescópio nem cientista.

const express = require("express");

const app = express();
app.use(express.json());

const PORTA = process.env.PORT || 3000;
const TTL_PADRAO_MS = 10000; // se o Flask cair segurando o lock, ele expira sozinho

// recurso -> { dono, expiraEm }
const locks = new Map();

function log(msg) {
  console.log(`[${new Date().toISOString()}] [servico-coordenador] ${msg}`);
}

// remove o lock se já passou do tempo
function limparSeExpirou(recurso) {
  const lock = locks.get(recurso);
  if (lock && Date.now() > lock.expiraEm) {
    locks.delete(recurso);
    log(`Lock para o recurso ${recurso} expirou (TTL) e foi removido`);
  }
}

app.post("/lock", (req, res) => {
  const { recurso, dono = "desconhecido", ttl_ms = TTL_PADRAO_MS } = req.body || {};
  if (!recurso) return res.status(400).json({ erro: "Campo 'recurso' é obrigatório" });

  log(`Recebido pedido de lock para o recurso ${recurso} (dono ${dono})`);
  limparSeExpirou(recurso);

  // Verificar e travar acontecem juntos, sem nenhum await no meio.
  // Como o Node roda o JavaScript numa thread só, ninguém consegue
  // "entrar no meio" dessas duas linhas. É isso que garante a exclusão mútua.
  if (locks.has(recurso)) {
    log(`Recurso ${recurso} já em uso, negando lock`);
    return res.status(409).json({ recurso, status: "NEGADO", dono_atual: locks.get(recurso).dono });
  }

  const expiraEm = Date.now() + ttl_ms;
  locks.set(recurso, { dono, expiraEm });
  log(`Lock concedido para o recurso ${recurso}`);
  return res.status(200).json({ recurso, status: "CONCEDIDO", expira_em: new Date(expiraEm).toISOString() });
});

app.post("/unlock", (req, res) => {
  const { recurso, dono } = req.body || {};
  if (!recurso) return res.status(400).json({ erro: "Campo 'recurso' é obrigatório" });

  log(`Recebido pedido de unlock para o recurso ${recurso}`);
  const lock = locks.get(recurso);

  if (!lock) {
    return res.status(404).json({ recurso, status: "SEM_LOCK" });
  }
  // só quem travou pode destravar
  if (dono && lock.dono !== dono) {
    return res.status(403).json({ recurso, status: "NAO_E_O_DONO" });
  }

  locks.delete(recurso);
  log(`Lock para o recurso ${recurso} liberado`);
  return res.status(200).json({ recurso, status: "LIBERADO" });
});

// diagnóstico: mostra os locks ativos
app.get("/locks", (req, res) => {
  const lista = [];
  for (const [recurso, l] of locks) {
    lista.push({ recurso, dono: l.dono, expira_em: new Date(l.expiraEm).toISOString() });
  }
  res.json({ total: lista.length, locks: lista });
});

app.get("/health", (req, res) => res.json({ status: "ok" }));

app.listen(PORTA, () => log(`Serviço iniciado na porta ${PORTA}`));
