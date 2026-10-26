# Logs do SCTEC

O sistema vai ter dois tipos de log:

- **Log de aplicação:** serve pra gente (desenvolvedores) entender o que o código está fazendo e achar erro.
- **Log de auditoria:** serve pra provar quem fez o quê e quando. Se dois cientistas brigarem por um horário, é esse log que resolve.

No Flask os logs vão pro arquivo `app.log` e também pro terminal. No Node vão só pro terminal com `console.log`.

## Log de aplicação

Formato:

```
NIVEL:DATA_HORA_UTC:SERVICO:MENSAGEM
```

Mensagens que vamos usar no Flask:

- Requisição recebida em GET /time
- Requisição recebida para POST /agendamentos
- Tentando adquirir lock para o recurso X
- Lock adquirido com sucesso
- Falha ao adquirir lock, recurso ocupado
- Iniciando verificação de conflito no BD
- Salvando novo agendamento no BD
- Liberando lock para o recurso X

Mensagens no Node:

- Recebido pedido de lock para o recurso X
- Lock concedido para o recurso X
- Recurso X já em uso, negando lock
- Lock para o recurso X liberado

Exemplo de duas requisições chegando quase juntas:

```
INFO:2025-10-26T18:00:04.500Z:servico-agendamento:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.505Z:servico-agendamento:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:04.800Z:servico-agendamento:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.805Z:servico-agendamento:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:05.120Z:servico-agendamento:Lock adquirido com sucesso
INFO:2025-10-26T18:00:05.121Z:servico-agendamento:Falha ao adquirir lock, recurso ocupado
INFO:2025-10-26T18:00:05.122Z:servico-agendamento:Iniciando verificação de conflito no BD
INFO:2025-10-26T18:00:05.123Z:servico-agendamento:Salvando novo agendamento no BD
INFO:2025-10-26T18:00:05.130Z:servico-agendamento:Liberando lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
```

## Log de auditoria

É gerado em JSON, uma linha por evento, e só depois que a operação foi salva no banco. Esse log nunca é alterado.

Formato do agendamento criado:

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.123Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CRIADO",
  "service": "servico-agendamento",
  "details": {
    "agendamento_id": 123,
    "cientista_id": 7,
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "timestamp_requisicao": "2025-10-26T18:00:04.480Z"
  }
}
```

Formato do cancelamento:

```json
{
  "timestamp_utc": "2025-10-27T10:00:00.456Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CANCELADO",
  "service": "servico-agendamento",
  "details": {
    "agendamento_id": 123,
    "cientista_id": 7,
    "horario_inicio_utc": "2025-12-01T03:00:00Z"
  }
}
```

Guardamos tanto a hora do clique (`timestamp_requisicao`) quanto a hora em que salvou (`timestamp_utc`). Com isso dá pra saber quem pediu primeiro em caso de disputa.

## O que esperamos ver nos logs em cada entrega

- **Entrega 2 (sem lock):** vários `AGENDAMENTO_CRIADO` pro mesmo horário. Isso prova que existe a condição de corrida.
- **Entrega 3 (com lock):** só um `AGENDAMENTO_CRIADO`, e nove mensagens de "Falha ao adquirir lock".
- **Entrega 4:** aparecem os logs do GET /time e o `AGENDAMENTO_CANCELADO`.
- **Entrega 5:** com `docker-compose logs -f` aparecem os logs dos dois serviços misturados no mesmo terminal.
