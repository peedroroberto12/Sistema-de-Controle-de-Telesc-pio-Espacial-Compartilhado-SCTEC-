# Modelos do SCTEC

Aqui estão as entidades que o sistema vai usar. Os horários ficam todos em UTC pra não ter confusão de fuso entre os cientistas.

Cada reserva ocupa um slot de 5 minutos (ex: 03:00 até 03:05).

## Cientista

Quem pede tempo no telescópio.

- id (int, gerado automático)
- nome (texto)
- email (texto, não pode repetir)
- instituicao (texto)
- pais (texto)
- data_cadastro (data/hora, o servidor preenche)

Exemplo:
```json
{
  "id": 7,
  "nome": "Marie Curie",
  "email": "marie@sorbonne.fr",
  "instituicao": "Sorbonne",
  "pais": "França",
  "data_cadastro": "2025-10-20T14:00:00Z"
}
```

## Telescopio

O equipamento que todo mundo quer usar. Por enquanto só existe um, o Hubble-Acad.

- id (int)
- nome (texto, ex: "Hubble-Acad")
- descricao (texto, opcional)
- ativo (true/false)

```json
{ "id": 1, "nome": "Hubble-Acad", "descricao": "Telescópio acadêmico", "ativo": true }
```

## Agendamento

A reserva em si.

- id (int)
- cientista_id (quem reservou)
- telescopio_id (qual telescópio)
- horario_inicio_utc (início do slot)
- horario_fim_utc (início + 5 min, o servidor calcula)
- objeto_celeste (o que vai observar, opcional)
- status (AGENDADO ou CANCELADO)
- timestamp_requisicao (hora em que o cientista clicou, já sincronizada com o servidor)
- data_criacao (hora em que salvou no banco)

```json
{
  "id": 123,
  "cientista_id": 7,
  "telescopio_id": 1,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:05:00Z",
  "objeto_celeste": "Andrômeda",
  "status": "AGENDADO",
  "timestamp_requisicao": "2025-10-26T18:00:04.480Z",
  "data_criacao": "2025-10-26T18:00:05.123Z"
}
```

**Regra principal:** não pode ter dois agendamentos com status AGENDADO no mesmo telescópio e no mesmo horário. Essa é justamente a regra que quebra quando acontece a condição de corrida.

Quando um agendamento é cancelado, ele não é apagado do banco. Só muda o status pra CANCELADO, assim fica o histórico.

## Relacionamentos

- Um cientista pode ter vários agendamentos
- Um telescópio pode ter vários agendamentos
- Cada agendamento é de um cientista e de um telescópio

```
Cientista 1 ---- N Agendamento N ---- 1 Telescopio
```

## Lock (fica no coordenador, não no banco)

O serviço em Node guarda os locks na memória. Cada lock é identificado por uma string assim:

`Hubble-Acad_2025-12-01T03:00:00Z`

ou seja, nome do telescópio + horário. Se essa chave já está travada, ninguém mais consegue reservar aquele horário até ela ser liberada.
