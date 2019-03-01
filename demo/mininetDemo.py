# Create a dataflow for the demo

from utils.dataflow import *
import sys
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
	print('running act container')
	labels = dataflow.getData(inport=10002) #get the labels
	print(labels)
	return '{}'.format(str(labels))


#internal port of docker listening on the machine 19000

#receiving ports
recv = {} #these are external ports of docker
recv['cam']=20000
recv['tx2']=20001
recv['act']=20002

#Send ip and ports
send = {}
send['cam']    = '10.0.0.102'   #  sending to tx2 container over port 19000 (internal port)
send['tx21']    = '172.17.49.71'#  sending to tx2 machine over port 19000
send['tx22']    = '10.0.0.103'  #  sending to act container over port 19005, different port
send['act']    = '172.17.15.21' #  sending to android server over port 19000

if __name__ == "__main__":
	if len(sys.argv)!=2:
		print('usage: python3 mininetDemo.py container')
		print('Example: python3 mininetDemo.py cam')
		exit(0)

	#Parsing the input argument
	type=str(sys.argv[1])

	print(recv,send)
	while True:
		#receive images on port 20000 and forward them to tx2 container on 10.0.0.102
		if type=='cam':
			print('Starting cam container')
			data = dataflow.getData(inport=20000)
			print('cam received data')
			res = dataflow.sendData('tx2_container_data',data)
			print('res is:',res)
			# We need to send data with id

		#Tx2 container receives data from cam container
		#tx2 container sends data to the tx2 machine
		if type =='tx2':
			print('starting tx2 container')
			data = dataflow.getData(inport=10001) #get the image
			print('image data received')
			#send data to tx2 machine
			res = dataflow.sendData('tx2_machine_inference',data)
			print('sending tx2 machine res is:',res)

			#receive the labels from tx2 machine only if we send data
			if res:
				labels = dataflow.getData(inport=20001) #get the labels
				print('labels are:',labels)

				#send labels to the actuator container
				res = dataflow.sendData('act_container',labels)
				print('sending act_container res is:',res)

		#act listens for the label from the tx2 container
		if type =='act':
			web_ip, web_port = '10.0.0.103','20002'
			app.run(host=web_ip, port=int(web_port))
			#print('lables are:',labels)
