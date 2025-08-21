import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='leilao')
channel.basic_publish(exchange='', routing_key='leilao', body='Mensagem de teste')

print("Mensagem enviada para a fila 'leilao'")
connection.close()

class Leilao:
    def __init__(self, nome):
        self.nome = nome

    def iniciar_leilao(self):
        print(f"Iniciando leilão: {self.nome}")
        