import argparse
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import json
import os
import pika
import threading
import time
import tkinter as tk
from tkinter import messagebox

parser = argparse.ArgumentParser(description="Script de cliente")

parser.add_argument("--client", help='Choose de client ID ("A" OR "B")',default='A')
args = parser.parse_args()

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Lista de leilões ativos
leiloes_ativos = []
leiloes_ids = set()


def callback(ch, method, properties, body):
    mensagem = body.decode()
    print("Notificação recebida:", mensagem)
    
    # Verificar se é uma mensagem de início de leilão (contém ';')
    if ';' in mensagem:
        partes = mensagem.split(';')
        if len(partes) == 3:
            leilao_id, descricao, inicio = partes
            if leilao_id not in leiloes_ids:
                leilao = {'id': leilao_id, 'descricao': descricao, 'inicio': inicio}
                leiloes_ativos.append(leilao)
                leiloes_ids.add(leilao_id)
                root.after(0, atualizar_lista_leiloes)
                print(f"Leilão ativo adicionado: {leilao}")
    else:
        # É uma mensagem de lance ou vencedor
        root.after(0, lambda: adicionar_notificacao(mensagem))
        print(f"Notificação adicionada: {mensagem}")
    
channel.exchange_declare(exchange='inicio', exchange_type='fanout')
channel.basic_consume(queue='leilao_1', on_message_callback=callback, auto_ack=True)

if args.client == "B":
    channel.basic_consume(queue='notificacoes1', on_message_callback=callback, auto_ack=True)

if args.client == "A":
    print("Sou o cliente A")
    channel.basic_consume(queue='notificacoes2', on_message_callback=callback, auto_ack=True)
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
root.geometry("500x400")

# Configurar pesos para centralizar
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

tk.Label(root, text="ID do Leilão:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=5, sticky='w')
leilao_entry = tk.Entry(root, font=("Arial", 12))
leilao_entry.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

tk.Label(root, text="Valor do Lance:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=5, sticky='w')
valor_entry = tk.Entry(root, font=("Arial", 12))
valor_entry.grid(row=1, column=1, padx=10, pady=5, sticky='ew')

tk.Label(root, text="Feed:", font=("Arial", 12)).grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky='ew')
leiloes_listbox = tk.Listbox(root, height=10, font=("Arial", 12))
leiloes_listbox.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky='ew')

feed_label = tk.Label(root, text="Leilões ativos: 0", font=("Arial", 10))
feed_label.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky='ew')

def atualizar_lista_leiloes():
    leiloes_ativos.sort(key=lambda x: int(x['id']))  # Ordenar por ID
    leiloes_listbox.delete(0, tk.END)
    for leilao in leiloes_ativos:
        leiloes_listbox.insert(tk.END, f"ID: {leilao['id']} - {leilao['descricao']} (Início: {leilao['inicio']})")
    feed_label.config(text=f"Leilões ativos: {len(leiloes_ativos)}")

def adicionar_notificacao(mensagem):
    leiloes_listbox.insert(tk.END, f"Notificação: {mensagem}")
    # Não atualizar a contagem aqui, pois notificações não afetam a quantidade de leilões ativos

#flag para saber quando começar a consumir
canais_consumo = set()

def enviar():
    try:
        leilao_id = int(leilao_entry.get())
        valor = valor_entry.get()
        if(args.client == "B" and leilao_id != 1):
            messagebox.showerror("Erro", "Cliente B só pode participar do leilão 1")
            return
        cliente.enviar_lance(leilao_id, valor)
        messagebox.showinfo("Sucesso", "Lance enviado!")
        if False: #Isso pode vir a funcionar no futuro (porém ainda não)
            #tratamento de consumo por desejo do cliente
            if leilao_id in canais_consumo:
                print("você já está inscrito nesse canal")
            else:
                channel.basic_consume(queue=f'leilao_{leilao_id}', on_message_callback=callback, auto_ack=True)
                canais_consumo.add(leilao_id)
                print(f"Inscrito no canal leilao_{leilao_id}")

    except Exception as e:
        messagebox.showerror("Erro", str(e))


# Iniciar consumo em thread separada


def consumir():
    channel.start_consuming()

threading.Thread(target=consumir, daemon=True).start()
tk.Button(root, text="Enviar Lance", command=enviar, font=("Arial", 12)).grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

root.mainloop()