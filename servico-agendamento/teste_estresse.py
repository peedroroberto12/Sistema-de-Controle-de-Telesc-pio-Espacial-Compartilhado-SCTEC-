# Dispara 10 requisições AO MESMO TEMPO tentando reservar o mesmo horário.
# Uso: python teste_estresse.py

import threading
from datetime import datetime, timezone

import requests

URL = "http://localhost:5000/agendamentos"
HORARIO = "2025-12-01T03:00:00Z"
QTD = 10

resultados = []
largada = threading.Barrier(QTD)  # segura todas as threads e solta juntas


def reservar(cientista_id):
    corpo = {
        "cientista_id": cientista_id,
        "telescopio_id": 1,
        "horario_inicio_utc": HORARIO,
        "objeto_celeste": "Andrômeda",
        "timestamp_requisicao": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    largada.wait()
    r = requests.post(URL, json=corpo)
    resultados.append((cientista_id, r.status_code))


threads = [threading.Thread(target=reservar, args=(i,)) for i in range(1, QTD + 1)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print("\n=== Resultado ===")
for cientista, status in sorted(resultados):
    print(f"Cientista {cientista:2d} -> HTTP {status}")

criados = sum(1 for _, s in resultados if s == 201)
print(f"\n{criados} de {QTD} requisições conseguiram reservar o MESMO horário ({HORARIO})")

r = requests.get("http://localhost:5000/agendamentos").json()
no_horario = [a for a in r["itens"] if a["horario_inicio_utc"] == HORARIO and a["status"] == "AGENDADO"]
print(f"Registros no banco para esse horário: {len(no_horario)}")
if len(no_horario) > 1:
    print("CONDIÇÃO DE CORRIDA: o mesmo slot foi vendido mais de uma vez!")
