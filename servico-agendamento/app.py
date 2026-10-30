# Serviço de Agendamento (o "Cérebro") - Entrega 3
# Agora pede lock ao Serviço Coordenador antes de mexer no banco.
# (a versão sem lock da Entrega 2 está em evidencias/entrega2/app_sem_lock.py)

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# Na Entrega 5 (Docker) vira http://servico-coordenador:3000
COORDENADOR_URL = os.getenv("COORDENADOR_URL", "http://localhost:3000")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sctec.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"timeout": 30}}
db = SQLAlchemy(app)


# ---------------- LOGGING ----------------
# Nível customizado AUDIT (fica entre INFO=20 e WARNING=30)
AUDIT = 25
logging.addLevelName(AUDIT, "AUDIT")


class FormatoUTC(logging.Formatter):
    # deixa a data no formato 2025-10-26T18:00:04.500Z
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(record.msecs):03d}Z"


formato = FormatoUTC("%(levelname)s:%(asctime)s:servico-agendamento:%(message)s")

log = logging.getLogger("sctec")
log.setLevel(logging.INFO)

arquivo = logging.FileHandler("app.log", encoding="utf-8")
arquivo.setFormatter(formato)
console = logging.StreamHandler()
console.setFormatter(formato)
log.addHandler(arquivo)
log.addHandler(console)


def agora_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def iso_curto(dt):
    # sem milissegundos, usado nos horários de slot
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def ler_data(texto):
    # aceita "2025-12-01T03:00:00Z"
    dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def log_auditoria(event_type, details):
    registro = {
        "timestamp_utc": iso(agora_utc()),
        "level": "AUDIT",
        "event_type": event_type,
        "service": "servico-agendamento",
        "details": details,
    }
    log.log(AUDIT, json.dumps(registro, ensure_ascii=False))


# ---------------- MODELOS ----------------
class Cientista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    instituicao = db.Column(db.String(120), nullable=False)
    pais = db.Column(db.String(60), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=lambda: agora_utc().replace(tzinfo=None))

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "instituicao": self.instituicao,
            "pais": self.pais,
            "data_cadastro": iso(self.data_cadastro),
            "_links": {
                "self": {"href": f"/cientistas/{self.id}", "method": "GET"},
                "agendamentos": {"href": f"/cientistas/{self.id}/agendamentos", "method": "GET"},
            },
        }


class Telescopio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), unique=True, nullable=False)
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "ativo": self.ativo,
            "_links": {
                "self": {"href": f"/telescopios/{self.id}", "method": "GET"},
            },
        }


class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cientista_id = db.Column(db.Integer, db.ForeignKey("cientista.id"), nullable=False)
    telescopio_id = db.Column(db.Integer, db.ForeignKey("telescopio.id"), nullable=False)
    horario_inicio_utc = db.Column(db.DateTime, nullable=False)
    horario_fim_utc = db.Column(db.DateTime, nullable=False)
    objeto_celeste = db.Column(db.String(120))
    status = db.Column(db.String(20), default="AGENDADO")
    timestamp_requisicao = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=lambda: agora_utc().replace(tzinfo=None))

    def to_dict(self):
        links = {
            "self": {"href": f"/agendamentos/{self.id}", "method": "GET"},
            "cientista": {"href": f"/cientistas/{self.cientista_id}", "method": "GET"},
            "telescopio": {"href": f"/telescopios/{self.telescopio_id}", "method": "GET"},
        }
        # HATEOAS: só oferece cancelar se ainda estiver agendado
        if self.status == "AGENDADO":
            links["cancelar"] = {"href": f"/agendamentos/{self.id}", "method": "DELETE"}

        return {
            "id": self.id,
            "cientista_id": self.cientista_id,
            "telescopio_id": self.telescopio_id,
            "horario_inicio_utc": iso_curto(self.horario_inicio_utc),
            "horario_fim_utc": iso_curto(self.horario_fim_utc),
            "objeto_celeste": self.objeto_celeste,
            "status": self.status,
            "timestamp_requisicao": iso(self.timestamp_requisicao),
            "data_criacao": iso(self.data_criacao),
            "_links": links,
        }


def erro(status, mensagem):
    return jsonify({
        "erro": mensagem,
        "_links": {"agendamentos": {"href": "/agendamentos", "method": "GET"}},
    }), status


# ---------------- ROTAS ----------------
@app.get("/")
def raiz():
    return jsonify({
        "servico": "servico-agendamento",
        "_links": {
            "time": {"href": "/time", "method": "GET"},
            "cientistas": {"href": "/cientistas", "method": "GET"},
            "telescopios": {"href": "/telescopios", "method": "GET"},
            "agendamentos": {"href": "/agendamentos", "method": "GET"},
            "criar_agendamento": {"href": "/agendamentos", "method": "POST"},
        },
    })


@app.get("/time")
def hora_oficial():
    log.info(f"Requisição recebida em GET /time do IP {request.remote_addr}")
    return jsonify({"timestamp_utc": iso(agora_utc())})


@app.post("/cientistas")
def criar_cientista():
    dados = request.get_json(silent=True) or {}
    for campo in ["nome", "email", "instituicao", "pais"]:
        if not dados.get(campo):
            return erro(400, f"Campo obrigatório: {campo}")

    if Cientista.query.filter_by(email=dados["email"]).first():
        return erro(409, "Email já cadastrado")

    c = Cientista(nome=dados["nome"], email=dados["email"],
                  instituicao=dados["instituicao"], pais=dados["pais"])
    db.session.add(c)
    db.session.commit()
    log_auditoria("CIENTISTA_CRIADO", {"cientista_id": c.id, "nome": c.nome})
    return jsonify(c.to_dict()), 201, {"Location": f"/cientistas/{c.id}"}


@app.get("/cientistas")
def listar_cientistas():
    return jsonify({
        "itens": [c.to_dict() for c in Cientista.query.all()],
        "_links": {"self": {"href": "/cientistas", "method": "GET"},
                   "criar": {"href": "/cientistas", "method": "POST"}},
    })


@app.get("/cientistas/<int:id>")
def ver_cientista(id):
    c = db.session.get(Cientista, id)
    if not c:
        return erro(404, "Cientista não encontrado")
    return jsonify(c.to_dict())


@app.get("/cientistas/<int:id>/agendamentos")
def agendamentos_do_cientista(id):
    lista = Agendamento.query.filter_by(cientista_id=id).all()
    return jsonify({"itens": [a.to_dict() for a in lista]})


@app.get("/telescopios")
def listar_telescopios():
    return jsonify({
        "itens": [t.to_dict() for t in Telescopio.query.all()],
        "_links": {"self": {"href": "/telescopios", "method": "GET"}},
    })


@app.get("/telescopios/<int:id>")
def ver_telescopio(id):
    t = db.session.get(Telescopio, id)
    if not t:
        return erro(404, "Telescópio não encontrado")
    return jsonify(t.to_dict())


@app.post("/agendamentos")
def criar_agendamento():
    dados = request.get_json(silent=True) or {}

    # 1) validação
    for campo in ["cientista_id", "telescopio_id", "horario_inicio_utc"]:
        if not dados.get(campo):
            return erro(400, f"Campo obrigatório: {campo}")

    try:
        inicio = ler_data(dados["horario_inicio_utc"])
        ts_req = ler_data(dados["timestamp_requisicao"]) if dados.get("timestamp_requisicao") else None
    except ValueError:
        return erro(400, "Data inválida, use o formato 2025-12-01T03:00:00Z")

    if inicio.minute % 5 != 0 or inicio.second != 0:
        return erro(400, "O horário precisa começar em múltiplo de 5 minutos")

    cientista = db.session.get(Cientista, dados["cientista_id"])
    telescopio = db.session.get(Telescopio, dados["telescopio_id"])
    if not cientista or not telescopio:
        return erro(404, "Cientista ou telescópio não encontrado")

    recurso = f"{telescopio.nome}_{iso_curto(inicio)}"
    dono = f"req-{uuid.uuid4().hex[:8]}"  # identifica esta requisição no coordenador
    log.info(f"Requisição recebida para POST /agendamentos (recurso {recurso})")

    # 2) pede permissão ao Porteiro antes de mexer no banco
    log.info(f"Tentando adquirir lock para o recurso {recurso}")
    try:
        r = requests.post(f"{COORDENADOR_URL}/lock",
                          json={"recurso": recurso, "dono": dono}, timeout=3)
    except requests.RequestException as e:
        log.error(f"Coordenador indisponível: {e}")
        return erro(503, "Coordenador indisponível, tente novamente")

    if r.status_code == 409:
        log.warning(f"Falha ao adquirir lock para o recurso {recurso}, recurso ocupado")
        return erro(409, "Horário ocupado ou sendo reservado por outra pessoa")
    if r.status_code != 200:
        log.error(f"Resposta inesperada do coordenador: {r.status_code}")
        return erro(503, "Erro no coordenador")

    log.info(f"Lock adquirido com sucesso para o recurso {recurso}")

    # 3) área crítica: só uma requisição por vez chega aqui pra esse recurso
    try:
        log.info("Iniciando verificação de conflito no BD")
        conflito = Agendamento.query.filter_by(
            telescopio_id=telescopio.id,
            horario_inicio_utc=inicio,
            status="AGENDADO",
        ).first()

        if conflito:
            log.warning(f"Conflito no BD: slot {recurso} já agendado")
            return erro(409, "Horário ocupado")

        # Mesma "janela" da Entrega 2. Agora não tem problema,
        # porque ninguém mais entra aqui enquanto seguramos o lock.
        time.sleep(0.2)

        log.info("Salvando novo agendamento no BD")
        ag = Agendamento(
            cientista_id=cientista.id,
            telescopio_id=telescopio.id,
            horario_inicio_utc=inicio,
            horario_fim_utc=inicio + timedelta(minutes=5),
            objeto_celeste=dados.get("objeto_celeste"),
            timestamp_requisicao=ts_req,
        )
        db.session.add(ag)
        db.session.commit()

        # auditoria, só depois de salvar
        log_auditoria("AGENDAMENTO_CRIADO", {
            "agendamento_id": ag.id,
            "cientista_id": cientista.id,
            "horario_inicio_utc": iso_curto(inicio),
            "timestamp_requisicao": iso(ts_req),
            "request_id": dono,
        })
        return jsonify(ag.to_dict()), 201, {"Location": f"/agendamentos/{ag.id}"}

    finally:
        # 4) libera o lock SEMPRE, mesmo se deu erro ou conflito
        log.info(f"Liberando lock para o recurso {recurso}")
        try:
            requests.post(f"{COORDENADOR_URL}/unlock",
                          json={"recurso": recurso, "dono": dono}, timeout=3)
        except requests.RequestException as e:
            # se falhar, o TTL do coordenador libera sozinho
            log.error(f"Não foi possível liberar o lock: {e}")


@app.get("/agendamentos")
def listar_agendamentos():
    lista = Agendamento.query.order_by(Agendamento.id).all()
    return jsonify({
        "total": len(lista),
        "itens": [a.to_dict() for a in lista],
        "_links": {"self": {"href": "/agendamentos", "method": "GET"},
                   "criar": {"href": "/agendamentos", "method": "POST"}},
    })


@app.get("/agendamentos/<int:id>")
def ver_agendamento(id):
    a = db.session.get(Agendamento, id)
    if not a:
        return erro(404, "Agendamento não encontrado")
    return jsonify(a.to_dict())

@app.delete("/agendamentos/<int:id>")
def cancelar_agendamento(id):
    log.info(f"Requisição recebida para DELETE /agendamentos/{id}")
    a = db.session.get(Agendamento, id)
    if not a:
        return erro(404, "Agendamento não encontrado")
    if a.status == "CANCELADO":
        return erro(409, "Agendamento já estava cancelado")

    # nao apaga do banco, so muda o status (mantem o historico)
    a.status = "CANCELADO"
    db.session.commit()

    log_auditoria("AGENDAMENTO_CANCELADO", {
        "agendamento_id": a.id,
        "cientista_id": a.cientista_id,
        "horario_inicio_utc": iso_curto(a.horario_inicio_utc),
        "status_anterior": "AGENDADO",
        "status_novo": "CANCELADO",
    })
    # a resposta volta sem o link "cancelar"
    return jsonify(a.to_dict())


@app.get("/web")
def pagina_web():
    # pagina do cliente (index.html)
    return app.send_static_file("index.html")
def popular_banco():
    # cria um telescópio e alguns cientistas pra facilitar os testes
    
    if not Telescopio.query.first():
        db.session.add(Telescopio(nome="Hubble-Acad", descricao="Telescópio espacial acadêmico"))
    if not Cientista.query.first():
        nomes = ["Marie Curie", "Carl Sagan", "Vera Rubin", "Edwin Hubble", "Cesar Lattes",
                 "Johannes Kepler", "Galileu Galilei", "Jocelyn Bell", "Neil Tyson", "Katherine Johnson"]
        for i, n in enumerate(nomes, start=1):
            db.session.add(Cientista(nome=n, email=f"cientista{i}@sctec.org",
                                     instituicao="Universidade", pais="Brasil"))
    db.session.commit()


with app.app_context():
    db.create_all()
    popular_banco()
    log.info("Conexão com o banco de dados estabelecida")


if __name__ == "__main__":
    log.info("Serviço iniciado na porta 5000")
    # threaded=True: atende várias requisições ao mesmo tempo
    app.run(host="0.0.0.0", port=5000, threaded=True)
