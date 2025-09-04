import pika
import json
import base64
import os
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import tkinter as tk
from tkinter import messagebox

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='lance_realizado')
channel.queue_declare(queue='leilao_1')
channel.queue_declare(queue='leilao_2')

def callback(ch, method, properties, body):
    print("Notificação recebida:", body.decode())

channel.basic_consume(queue='leilao_1', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue='leilao_2', on_message_callback=callback, auto_ack=True)

class Cliente:
    def __init__(self, nome, id_cliente):
        self.nome = nome
        self.id_cliente = id_cliente
        self.private_key_path = f"chaves/private_{id_cliente}.pem"
        self.public_key_path = f"chaves_publicas/public_key_{id_cliente}.pem"
        
        # Gerar chaves se não existirem
        if not os.path.exists(self.private_key_path):
            key = RSA.generate(2048)
            private_key = key.export_key()
            with open(self.private_key_path, "wb") as f:
                f.write(private_key)
            public_key = key.publickey().export_key()
            os.makedirs("chaves_publicas", exist_ok=True)
            with open(self.public_key_path, "wb") as f:
                f.write(public_key)
        
        self.private_key = RSA.import_key(open(self.private_key_path).read())

    def enviar_lance(self, leilao_id, valor):
        msg = {'leilao_id': leilao_id, 'id_cliente': self.id_cliente, 'valor': float(valor)}
        msg_str = json.dumps(msg)
        h = SHA256.new(msg_str.encode())
        assinatura = pkcs1_15.new(self.private_key).sign(h)
        msg['assinatura'] = base64.b64encode(assinatura).decode()
        channel.basic_publish(exchange='', routing_key='lance_realizado', body=json.dumps(msg))
        print(f"Lance enviado: {msg}")

# GUI
cliente = Cliente("Cliente1", 1)

root = tk.Tk()
root.title("Cliente de Leilão")

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

tk.Button(root, text="Enviar Lance", command=enviar).grid(row=2, column=0, columnspan=2)

# Iniciar consumo em thread separada
import threading
def consumir():
    channel.start_consuming()

threading.Thread(target=consumir, daemon=True).start()

root.mainloop()