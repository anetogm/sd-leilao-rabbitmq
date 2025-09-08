import argparse
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import json
import os
import pika
import threading
import tkinter as tk
from tkinter import messagebox



parser = argparse.ArgumentParser(description="Script de cliente")

parser.add_argument("--client", help='Choose de client ID ("A" OR "B")')
args = parser.parse_args()

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()


def callback(ch, method, properties, body):
    print("Notificação recebida:", body.decode())
    root.after(0, lambda: messagebox.showinfo("Mensagem recebida:", f"{body.decode()}"))

channel.exchange_declare(exchange='inicio', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='inicio', queue=queue_name)

channel.basic_consume(queue='leilao_1', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

if args.client == "B":
    print("Sou o cliente B")
    channel.basic_consume(queue='leilao_2', on_message_callback=callback, auto_ack=True)


class Cliente:
    def __init__(self, nome, id_cliente):
        self.nome = nome
        self.id_cliente = id_cliente
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.private_key_path = os.path.join(base_dir, 'chaves', f'private_{id_cliente}.pem')
        self.public_key_path = os.path.join(base_dir, 'chaves_publicas', f'public_key_{id_cliente}.pem')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        self.channel = self.connection.channel()
        
        # Gerar chaves se não existirem
        if not os.path.exists(self.private_key_path):
            key = RSA.generate(2048)
            private_key = key.export_key()
            with open(self.private_key_path, "wb") as f:
                f.write(private_key)
            public_key = key.publickey().export_key()
            os.makedirs(os.path.dirname(self.public_key_path), exist_ok=True)
            with open(self.public_key_path, "wb") as f:
                f.write(public_key)
        
        self.private_key = RSA.import_key(open(self.private_key_path).read())

    def enviar_lance(self, leilao_id, valor):
        msg = {'leilao_id': leilao_id, 'id_cliente': self.id_cliente, 'valor': float(valor)}
        msg_str = json.dumps(msg)
        h = SHA256.new(msg_str.encode())
        assinatura = pkcs1_15.new(self.private_key).sign(h)
        msg['assinatura'] = base64.b64encode(assinatura).decode()
        self.channel.basic_publish(exchange='', routing_key='lance_realizado', body=json.dumps(msg))
        print(f"Lance enviado: {msg}")

# GUI
# Gerar id_cliente automaticamente baseado em chaves existentes
base_dir = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(base_dir, "chaves_publicas"), exist_ok=True)
chaves_existentes = [f for f in os.listdir(os.path.join(base_dir, "chaves_publicas")) if f.startswith("public_key_")]
id_cliente = len(chaves_existentes) + 1
nome_cliente = f"Cliente{id_cliente}"

cliente = Cliente(nome_cliente, id_cliente)

root = tk.Tk()
root.title(f"Cliente de Leilão - {nome_cliente}")

tk.Label(root, text="ID do Leilão:").grid(row=0, column=0)
leilao_entry = tk.Entry(root)
leilao_entry.grid(row=0, column=1)

tk.Label(root, text="Valor do Lance:").grid(row=1, column=0)
valor_entry = tk.Entry(root)
valor_entry.grid(row=1, column=1)

def enviar():
    try:
        leilao_id = int(leilao_entry.get())
        valor = valor_entry.get()
        cliente.enviar_lance(leilao_id, valor)
        messagebox.showinfo("Sucesso", "Lance enviado!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

tk.Button(root, text="Enviar Lance", command=enviar).grid(row=3, column=0, columnspan=2)

# Iniciar consumo em thread separada

def consumir():
    channel.start_consuming()

threading.Thread(target=consumir, daemon=True).start()

root.mainloop()