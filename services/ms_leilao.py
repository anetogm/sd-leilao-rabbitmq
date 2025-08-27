
import pika
import time
from datetime import datetime, timedelta
import threading

"""
							TODO 
Mantém internamente uma lista pré-configurada (hardcoded)
de leilões com: ID do leilão, descrição, data e hora de início e fim,
status (ativo, encerrado).

							TODO 
O leilão de um determinado produto deve ser iniciado quando
o tempo definido para esse leilão for atingido. Quando um leilão
começa, ele publica o evento na fila: leilao_iniciado.

							TODO 
O leilão de um determinado produto deve ser finalizado
quando o tempo definido para esse leilão expirar. Quando um leilão
termina, ele publica o evento na fila: leilao_finalizado.

"""

leiloes = [
	{
		'id': 1,
		'descricao': 'Notebook',
		'inicio': '?',
		'fim': '?',
		'status': 'pendente'
	},
	{
		'id': 2,
		'descricao': 'Celular',
		'inicio': '?',
		'fim': '?',
		'status': 'pendente'
	}
]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='leilao_iniciado')
channel.queue_declare(queue='leilao_finalizado')

def publicar_evento(fila, mensagem):
	channel.basic_publish(exchange='', routing_key=fila, body=mensagem)
	print(f"[x] Evento publicado em {fila}: {mensagem}")

def gerenciar_leilao(leilao):
	tempo_ate_inicio = (leilao['inicio'] - datetime.now()).total_seconds()
	if tempo_ate_inicio > 0:
		time.sleep(tempo_ate_inicio)
	leilao['status'] = 'ativo'
	publicar_evento('leilao_iniciado', f"{leilao['id']};{leilao['descricao']};{leilao['inicio']}")

	tempo_ate_fim = (leilao['fim'] - datetime.now()).total_seconds()
	if tempo_ate_fim > 0:
		time.sleep(tempo_ate_fim)
	leilao['status'] = 'encerrado'
	publicar_evento('leilao_finalizado', f"{leilao['id']};{leilao['descricao']};{leilao['fim']}")

def main():
	threads = []
	for leilao in leiloes:
		t = threading.Thread(target=gerenciar_leilao, args=(leilao,))
		t.start()
		threads.append(t)
	for t in threads:
		t.join()

if __name__ == "__main__":
	print("[MS Leilao] Gerenciando leilões...")
	main()
