from multiprocessing import Process
from threading import Thread
import sys
import os
from .Commander import Commander
from .Processor import Processor, ProcEventHandler

class Server(Process):
    def __init__(self, data_queue, command_queue, data_path, client, host, 
                 port):
        super(Server, self).__init__()
        self.command_q = command_queue
        self.data_q = data_queue
        self.commander = Commander()
        self.processor = Processor
        self.data_path = data_path
        self.client = client(host, port)
    
    def run(self):
        self.client.start()
        while True:
            flag, command = self.command_q.get()
            self.command_q.task_done()
            if flag == "TERMINATE" and command is None:
                break

            else:
                cmd, points = self.commander.translate(flag, command)
                self.client.run_cmd(cmd)

                processor = self.processor(points, self.data_path,
                                           self.data_q)
                processor.start()
                processor.join()