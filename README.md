# SCTEC - Agendamento de Telescópio
 
Projeto de Computação Distribuída (Entregas 1 a 5).
 
Sistema de agendamento de um telescópio espacial disputado por cientistas. Cada slot de 5 minutos só pode ter um dono, mesmo com várias requisições chegando ao mesmo tempo.
 
- **Aluno:** Pedro Roberto Fernandes Noronha
- **RA:** 10443434
- **Professor:** Mario
## Estrutura
 
- `MODELOS.md`, `API.md`, `LOGGING.md`: documentação (Entrega 1)
- `servico-agendamento/`: API em Flask (o "cérebro"), com a página web em `static/index.html`
- `servico-coordenador/`: serviço de lock em Node (o "porteiro")
- `docker-compose.yml`: sobe os dois serviços juntos (Entrega 5)
- `evidencias/`: logs dos testes e a versão sem lock da Entrega 2
- `SCTEC_Entregas_1_2_3.pdf` e `SCTEC_Entregas_4_5.pdf`: relatórios com prints e análise
## Rodar com Docker (jeito mais fácil)
 
```bash
docker compose up --build
```
 
- Flask: http://localhost:5000
- Página web: http://localhost:5000/web
- Coordenador: http://localhost:3000
Pra ver os logs dos dois serviços juntos:
 
```bash
docker compose logs -f
```
 
## Rodar sem Docker
 
```bash
pip install -r servico-agendamento/requirements.txt
cd servico-coordenador && npm install
```
 
```bash
# terminal 1
cd servico-coordenador && node server.js
# terminal 2
cd servico-agendamento && python app.py
```
 
## Entregas
 
### Entrega 1 - Blueprint
Especificação dos modelos, da API (com HATEOAS) e dos logs. Ver `MODELOS.md`, `API.md` e `LOGGING.md`.
 
### Entrega 2 - Condição de corrida (sem lock)
 
```bash
cd evidencias/entrega2 && python app_sem_lock.py
# outro terminal
cd servico-agendamento && python teste_estresse.py
```
Resultado: as 10 requisições conseguem reservar o mesmo horário.
 
### Entrega 3 - Coordenador (com lock)
 
Com o coordenador e o Flask rodando:
 
```bash
cd servico-agendamento && python teste_estresse.py
```
Resultado: só 1 consegue reservar e as outras 9 recebem 409.
 
### Entrega 4 - Relógio e cliente HATEOAS
- `GET /time`: hora oficial do servidor em UTC
- `DELETE /agendamentos/{id}`: cancela (muda o status para CANCELADO, não apaga)
- Página `/web`: sincroniza o relógio com o algoritmo de Cristian, agenda e cancela. Ela só conhece a raiz da API (`/`) e usa os links que o servidor manda. O botão Cancelar só aparece quando vem o link `cancelar`.
### Entrega 5 - Docker
Um Dockerfile para cada serviço e o `docker-compose.yml` na raiz. Dentro do Docker o Flask acha o coordenador pelo nome (`http://servico-coordenador:3000`), passado pela variável `COORDENADOR_URL`.
 
## Rotas
 
| Serviço | Método | Rota | Pra que serve |
|---|---|---|---|
| Flask | GET | / | raiz com os links da API |
| Flask | GET | /time | hora oficial |
| Flask | GET/POST | /cientistas | listar / cadastrar cientista |
| Flask | GET | /telescopios | listar telescópios |
| Flask | GET/POST | /agendamentos | listar / reservar horário |
| Flask | GET | /agendamentos/{id} | ver uma reserva |
| Flask | DELETE | /agendamentos/{id} | cancelar reserva |
| Flask | GET | /web | página do cliente |
| Node | POST | /lock | travar recurso |
| Node | POST | /unlock | liberar recurso |
| Node | GET | /locks | ver locks ativos |
| Node | GET | /health | status do serviço |
 
## Observação
 
O teste de estresse sempre usa o mesmo horário (`2025-12-01T03:00:00Z`). Pra rodar de novo do zero, apague o banco antes (`servico-agendamento/instance/sctec.db`, ou `docker compose down` e `up` de novo no Docker).
 
