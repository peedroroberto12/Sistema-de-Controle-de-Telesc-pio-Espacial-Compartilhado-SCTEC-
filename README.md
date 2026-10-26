# SCTEC - Agendamento de Telescópio

Projeto de Computação Distribuída (Entregas 1, 2 e 3).

- `MODELOS.md`, `API.md`, `LOGGING.md`: documentação (Entrega 1)
- `servico-agendamento/`: API em Flask
- `servico-coordenador/`: serviço de lock em Node
- `evidencias/`: logs dos testes

## Instalar

```bash
pip install -r servico-agendamento/requirements.txt
cd servico-coordenador && npm install
```

## Entrega 2 (sem lock)

```bash
cd evidencias/entrega2 && python app_sem_lock.py
# outro terminal
cd servico-agendamento && python teste_estresse.py
```
Resultado: as 10 requisições conseguem reservar o mesmo horário.

## Entrega 3 (com lock)

```bash
cd servico-coordenador && node server.js
# outro terminal
cd servico-agendamento && python app.py
# outro terminal
cd servico-agendamento && python teste_estresse.py
```
Resultado: só 1 consegue reservar e as outras 9 recebem 409.
