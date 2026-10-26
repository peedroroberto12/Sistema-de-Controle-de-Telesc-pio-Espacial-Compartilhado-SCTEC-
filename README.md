# SCTEC - Sistema de Controle de Telescópio Espacial Compartilhado

Entregas 1, 2 e 3.

```
sctec-projeto/
├── MODELOS.md, API.md, LOGGING.md   -> Entrega 1 (documentação)
├── servico-agendamento/             -> Flask (o "Cérebro")
│   ├── app.py
│   ├── teste_estresse.py
│   └── requirements.txt
├── servico-coordenador/             -> Node (o "Porteiro")
│   ├── server.js
│   └── package.json
└── evidencias/
    ├── entrega2/  -> app_sem_lock.py + app.log mostrando a condição de corrida
    └── entrega3/  -> app.log + coordenador.log mostrando o lock funcionando
```

## Instalação

```bash
cd servico-agendamento
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cd ../servico-coordenador
npm install
```

## Entrega 2: mostrando a condição de corrida

Usa a versão sem lock (`evidencias/entrega2/app_sem_lock.py`).

```bash
# terminal 1
cd evidencias/entrega2
rm -f app.log instance/sctec.db
python app_sem_lock.py

# terminal 2
cd servico-agendamento
python teste_estresse.py
```

Resultado esperado: as 10 requisições retornam 201 e o banco fica com 10 agendamentos para o mesmo horário.
No `app.log` aparecem os logs entrelaçados e 10 auditorias `AGENDAMENTO_CRIADO`.

## Entrega 3: com o coordenador

```bash
# terminal 1
cd servico-coordenador
node server.js

# terminal 2
cd servico-agendamento
rm -f app.log instance/sctec.db
python app.py

# terminal 3
cd servico-agendamento
python teste_estresse.py
```

Resultado esperado: uma requisição retorna 201 e nove retornam 409. O banco fica com um único registro.
O Node mostra 1 lock concedido e 9 negados, e o `app.log` mostra 1 sucesso, 9 falhas e uma única auditoria.

Comandos úteis pra conferir:
```bash
grep AGENDAMENTO_CRIADO app.log          # auditorias
grep "Falha ao adquirir lock" app.log    # requisições barradas
curl http://localhost:5000/agendamentos  # ver o banco pela API
```

O banco de dados fica em `servico-agendamento/instance/sctec.db`. O app cria sozinho o telescópio Hubble-Acad e 10 cientistas pra teste.
