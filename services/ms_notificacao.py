import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

def callback_lance_validado(ch, method, properties, body):
    print("Recebido em lance_validado:", body)
    msg = json.loads(body.decode())
    leilao_id = msg['leilao_id']
    cliente_id = msg['id_cliente']
    valor = msg['valor']
    msg = "O cliente " + str(cliente_id) + " realizou um lance de " + str(valor) + " no leilão " + str(leilao_id)
    channel.basic_publish(exchange='', routing_key=f'leilao_{leilao_id}', body=json.dumps(msg))

def callback_leilao_vencedor(ch, method, properties, body):
    print("Recebido em leilao_vencedor:", body)
    msg = json.loads(body.decode())
    leilao_id = msg['leilao_id']
    id_vencedor = msg['id_vencedor']
    msg = "O cliente " + str(id_vencedor) + " venceu o leilão " + str(leilao_id)
    channel.basic_publish(exchange='', routing_key=f'leilao_{leilao_id}', body=json.dumps(msg))

channel.basic_consume(queue='lance_validado', on_message_callback=callback_lance_validado, auto_ack=True)
channel.basic_consume(queue='leilao_vencedor', on_message_callback=callback_leilao_vencedor, auto_ack=True)

print(' [*] Esperando mensagens. Para sair pressione CTRL+C')
channel.start_consuming()