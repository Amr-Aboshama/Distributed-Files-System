import multiprocessing
from multiprocessing import Lock
import sys
import zmq
import random

ip1 = "127.0.0.1";	port = int(sys.argv[1]);	n = int(sys.argv[2])
keepers_num = 0;	processes_num = 0

lookup_table = multiprocessing.Manager().dict()
available_table = multiprocessing.Manager().dict()
ports_list = multiprocessing.Manager().list()

class value:
	def __init__(self, user_id, datakeepers_list, paths_list):
		self.user_id= user_id
		self.datakeepers_list= datakeepers_list
		self.paths_list= paths_list

	def valPrint(self):
		print(self.user_id, self.datakeepers_list, self.paths_list)



def updateLookup(proc_num,filename, value):
	print("i am process numberrr : %i"  %proc_num)
	lookup_table[filename]=value


def printLookup(proc_num,lookup_table):
	print("i am process number : %i inside print"  %proc_num)
	for k, v in lookup_table.items():
		print(k)
		lookup_table[k].valPrint()

def printAvailable(proc_num):
	print("i am process number : %i inside print Available"  %proc_num)
	for k, v in available_table.items():
		print(k, v)	

def configure():
	f = open("config.txt", "r")
	keepers_num = int(f.readline())
	processes_num = int(f.readline())
	for i in range(0,keepers_num):
		ip = f.readline().rstrip()			#.rstrip to erase "\n" from the ip end
		ip_port = int(f.readline())
		for j in range(0,processes_num):
			available_table[ip+"/"+str(ip_port+j)] = "available"
			ports_list.append(ip+"/"+str(ip_port+j))
	return keepers_num, processes_num

def master_client(port1):
	my_id = random.randrange(10000)
	starting_dk_port_index = random.randrange(keepers_num*processes_num)

	context = zmq.Context()
    
	client = context.socket(zmq.REP)            #REP because it needs to receive then send
	client.bind("tcp://%s:%i"%(ip1,port1))      #client will connect to this port

	while True:
		data = client.recv_pyobj()              #Receive message from client 
		
		#receiving dictionary contains command(upload/download) and file(file_Data for upload/file_name for download)
		print("master_client_id %i received command type %s" %(my_id, data['command']))
		

		if(data['command']=="upload"):
			my_mutex.acquire()
			while(available_table[ports_list[starting_dk_port_index]] == "busy"):
				starting_dk_port_index=(starting_dk_port_index+1)%(keepers_num*processes_num)
			available_table[ports_list[starting_dk_port_index]] = "busy"
			my_mutex.release()
			client.send_pyobj(ports_list[starting_dk_port_index])


		elif(data['command']=="download"):
			val = lookup_table[data[filename]]
			datakeeper_list= val.datakeepers_list
			i=0
			my_mutex.acquire()
			while(availible_table[datakeeper_list[i]] == "busy"):
				i= (i+1)%(len(datakeeper_list))
			availible_table[datakeeper_list[i]] = "busy"
			my_mutex.release()
			client.send_pyobj(datakeeper_list[i])	
			

		else:
			print("master_client_id %i received invalid command" %(my_id))


if __name__ == "__main__":
	with multiprocessing.Manager() as manager:
		my_mutex = Lock()
		my_id = random.randrange(10000)

		keepers_num, processes_num = configure()
		
		p = []
		for i in range(0,n):
			p.append(multiprocessing.Process(target=master_client, args=(port,)))
			p[i].start()
			port = port + 1

		for i in range(0,n):
			p[i].join()