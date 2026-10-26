# API do SCTEC

São dois serviços:

- **servico-agendamento** (Flask, porta 5000): cuida dos dados e das regras
- **servico-coordenador** (Node, porta 3000): só cuida dos locks

Tudo em JSON e horários em UTC.

Sobre o HATEOAS: as respostas trazem um campo `_links` com as ações que dá pra fazer a seguir. Por exemplo, um agendamento ativo vem com o link de cancelar, e um que já foi cancelado não vem. Assim o cliente não precisa adivinhar o que pode fazer.

---

## Serviço de Agendamento (Flask)

### GET /time

Devolve a hora oficial do servidor. O cliente usa isso pra acertar o próprio relógio (algoritmo de Cristian).

```json
{ "timestamp_utc": "2025-10-26T18:00:04.123Z" }
```

Como o cliente usa:
- anota a hora local antes de pedir (t0)
- recebe a hora do servidor
- anota a hora local quando a resposta chega (t1)
- hora certa = hora do servidor + (t1 - t0) / 2

### POST /cientistas

Cadastra um cientista.

Envia:
```json
{ "nome": "Marie Curie", "email": "marie@sorbonne.fr", "instituicao": "Sorbonne", "pais": "França" }
```

Resposta 201:
```json
{
  "id": 7,
  "nome": "Marie Curie",
  "email": "marie@sorbonne.fr",
  "instituicao": "Sorbonne",
  "pais": "França",
  "_links": {
    "self": { "href": "/cientistas/7", "method": "GET" },
    "agendamentos": { "href": "/cientistas/7/agendamentos", "method": "GET" }
  }
}
```

Se faltar campo, retorna 400. Se o email já existe, retorna 409.

### GET /cientistas e GET /cientistas/{id}

Lista todos ou busca um. Retorna 404 se o id não existir.

### GET /telescopios

Lista os telescópios.

### POST /agendamentos

Essa é a rota mais importante, é aqui que acontece a disputa.

Envia:
```json
{
  "cientista_id": 7,
  "telescopio_id": 1,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "objeto_celeste": "Andrômeda",
  "timestamp_requisicao": "2025-10-26T18:00:04.480Z"
}
```

O que acontece por dentro (a partir da entrega 3):
1. valida os dados
2. pede o lock pro coordenador
3. se conseguiu: verifica no banco se o horário está livre e salva
4. libera o lock (sempre, mesmo se der erro, usando try/finally)

Resposta 201:
```json
{
  "id": 123,
  "cientista_id": 7,
  "telescopio_id": 1,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:05:00Z",
  "status": "AGENDADO",
  "_links": {
    "self": { "href": "/agendamentos/123", "method": "GET" },
    "cancelar": { "href": "/agendamentos/123", "method": "DELETE" },
    "cientista": { "href": "/cientistas/7", "method": "GET" }
  }
}
```

Possíveis erros:
- 400: dados errados ou faltando
- 404: cientista ou telescópio não existe
- 409: o horário já está ocupado ou outra pessoa está reservando ao mesmo tempo

```json
{ "erro": "Horário ocupado", "_links": { "agendamentos": { "href": "/agendamentos", "method": "GET" } } }
```

### GET /agendamentos

Lista os agendamentos, cada um com seus links.

### GET /agendamentos/{id}

Busca um agendamento. Se ele estiver cancelado, o link `cancelar` não aparece na resposta.

### DELETE /agendamentos/{id}

Cancela o agendamento (só muda o status, não apaga).

- 200: cancelado
- 404: não existe
- 409: já estava cancelado

---

## Serviço Coordenador (Node)

### POST /lock

Envia:
```json
{ "recurso": "Hubble-Acad_2025-12-01T03:00:00Z" }
```

- 200: lock concedido
- 409: alguém já está usando esse recurso

### POST /unlock

Envia:
```json
{ "recurso": "Hubble-Acad_2025-12-01T03:00:00Z" }
```

- 200: lock liberado

---

## Resumo

| Serviço | Método | Rota | Pra que serve |
|---|---|---|---|
| Flask | GET | /time | hora oficial |
| Flask | POST | /cientistas | cadastrar cientista |
| Flask | GET | /cientistas | listar cientistas |
| Flask | GET | /telescopios | listar telescópios |
| Flask | POST | /agendamentos | reservar horário |
| Flask | GET | /agendamentos | listar reservas |
| Flask | GET | /agendamentos/{id} | ver uma reserva |
| Flask | DELETE | /agendamentos/{id} | cancelar reserva |
| Node | POST | /lock | travar recurso |
| Node | POST | /unlock | liberar recurso |
