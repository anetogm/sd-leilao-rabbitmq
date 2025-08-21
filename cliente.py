import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='leilao')

def callback(ch, method, properties, body):
    print("Mensagem recebida da fila 'leilao':", body.decode())

channel.basic_consume(queue='leilao', on_message_callback=callback, auto_ack=True)
channel.start_consuming()   