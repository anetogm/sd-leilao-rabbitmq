import pika

"""
						TODO
Possui as chaves públicas de todos os clientes.

						TODO
Escuta os eventos das filas lance_realizado, leilao_iniciado
e leilao_finalizado.

						TODO
Recebe lances de usuários (ID do leilão; ID do usuário, valor
do lance) e checa a assinatura digital da mensagem utilizando a
chave pública correspondente. Somente aceitará o lance se:
	- A assinatura for válida;
	- O ID do leilão existir e se o leilão estiver ativo;
	- O lance for maior que o último lance registrado;
 
						TODO
Se o lance for válido, o MS Lance publica o evento na fila
lance_validado.

						TODO
Ao finalizar um leilão, publicar na fila leilao_vencedor,
informando o ID do leilão, o ID do vencedor do leilão e o valor
negociado. O vencedor é o que efetuou o maior lance válido até o
encerramento.

"""

# como que eu sei qual o valor que ta maior no leilao?
# como que eu faço a verificacao pra ver se o valor que o cliente ta tentando é maior que o atual?

def callback_lance_realizado(ch, method, properties, body):
	print("Recebido em lance_realizado:", body)

def callback_leilao_iniciado(ch, method, properties, body):
	print("Recebido em leilao_iniciado:", body)

def callback_leilao_finalizado(ch, method, properties, body):
	print("Recebido em leilao_finalizado:", body)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='lance_realizado')
channel.queue_declare(queue='leilao_iniciado')
channel.queue_declare(queue='leilao_finalizado')

channel.basic_consume(queue='lance_realizado', on_message_callback=callback_lance_realizado, auto_ack=True)
channel.basic_consume(queue='leilao_iniciado', on_message_callback=callback_leilao_iniciado, auto_ack=True)
channel.basic_consume(queue='leilao_finalizado', on_message_callback=callback_leilao_finalizado, auto_ack=True)

print(' [*] Esperando mensagens. Para sair pressione CTRL+C')
channel.start_consuming()