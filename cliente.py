import pika
import base64
import json
import argparse


parser = argparse.ArgumentParser(description="Script de cliente")

parser.add_argument("--client", help='Choose de client ID ("A" OR "B")')
args = parser.parse_args()

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='leilao_1')
channel.queue_declare(queue='leilao_2') 
channel.queue_declare(queue='leilao_iniciado')   

def input_usuario(channel):
    channel.start_consuming()
    leilao = input("Qual o ID do leilão que gostaria de participar?")
    valor = input("Qual o valor do lance a ser dado?")
    return leilao, valor

def callback_leilao_1(ch, method, properties, body):
    print("Mensagem recebida da fila 'leilao_1':", body.decode())

def callback_leilao_2(ch, method, properties, body):
    print("Mensagem recebida da fila 'leilao_2':", body.decode())
    
## Definindo quais filas o cliente deve consumir

channel.basic_consume(queue='leilao_1', on_message_callback=callback_leilao_1, auto_ack=True)
channel.basic_consume(queue='leilao_iniciado', on_message_callback=callback_leilao_1, auto_ack=True)

if args.client == "A":
    print("Sou o cliente A")
    channel.basic_consume(queue='leilao_2', on_message_callback=callback_leilao_2, auto_ack=True)

   
leilao,valor = input_usuario(channel)

## Declarando Fila Lance Realizado (as que os clientes publicam)
channel.queue_declare(queue='lance_realizado')   


def envia_mensagem(routing_key,mensagem):
    channel.basic_publish(exchange='', routing_key=routing_key, body=mensagem)
    print(f"Mensagem enviada para a fila '{routing_key}': {mensagem}")




