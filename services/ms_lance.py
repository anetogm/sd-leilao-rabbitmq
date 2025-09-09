import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import json
import os
import pika

leiloes_ativos = {}
lances_atuais = {}


def callback_lance_realizado(ch, method, properties, body):
    print("Recebido em lance_realizado:", body)
    try:
        msg = json.loads(body.decode())
        leilao_id = msg['leilao_id']
        id_cliente = msg['id_cliente']
        valor = msg['valor']
        assinatura = base64.b64decode(msg['assinatura'])
        
        if leilao_id not in leiloes_ativos:
            print("Leilão não ativo.")
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(script_dir, '..', 'chaves_publicas', f'public_key_{id_cliente}.pem')
        key = RSA.import_key(open(key_path).read())
        msg_para_assinar = json.dumps({'leilao_id': leilao_id, 'id_cliente': id_cliente, 'valor': valor}).encode()
        h = SHA256.new(msg_para_assinar)
        try:
            pkcs1_15.new(key).verify(h, assinatura)
            print("Assinatura válida.")
            
            if leilao_id not in lances_atuais or valor > lances_atuais[leilao_id]['valor']:
                lances_atuais[leilao_id] = {'id_cliente': id_cliente, 'valor': valor}
                channel.basic_publish(exchange='', routing_key='lance_validado', body=json.dumps(msg))
                print("Lance válido e registrado.")
            else:
                print("Lance não é maior que o atual.")
        except (ValueError, TypeError):
            print("Assinatura inválida.")
    except Exception as e:
        print(f"Erro ao processar lance: {e}")

def callback_leilao_iniciado(ch, method, properties, body):
    print("Recebido em leilao_iniciado:", body)
    leilao_id = int(body.decode().split(';')[0])
    leiloes_ativos[leilao_id] = True

def callback_leilao_finalizado(ch, method, properties, body):
    print("Recebido em leilao_finalizado:", body)
    leilao_id = int(body.decode().split(';')[0])
    if leilao_id in leiloes_ativos:
        del leiloes_ativos[leilao_id]
    if leilao_id in lances_atuais:
        vencedor = lances_atuais[leilao_id]
        msg_vencedor = json.dumps({'leilao_id': leilao_id, 'id_vencedor': vencedor['id_cliente'], 'valor': vencedor['valor']})
        channel.basic_publish(exchange='', routing_key='leilao_vencedor', body=msg_vencedor)
        print(f"Vencedor publicado: {msg_vencedor}")
        del lances_atuais[leilao_id]

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

#definição da fanout
channel.exchange_declare(exchange='inicio', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='inicio', queue=queue_name)


channel.basic_consume(queue='lance_realizado', on_message_callback=callback_lance_realizado, auto_ack=True)
channel.basic_consume(queue='leilao_finalizado', on_message_callback=callback_leilao_finalizado, auto_ack=True)
channel.basic_consume(queue=queue_name, on_message_callback=callback_leilao_iniciado, auto_ack=True)

print(' [*] Esperando mensagens. Para sair pressione CTRL+C')
channel.start_consuming()