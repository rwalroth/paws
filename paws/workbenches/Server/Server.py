from multiprocessing import Process
from threading import Thread
import sys
import os
from .Commander import Commander
from .Processor import Processor

class Server(Process):
    def __init__(self, data_queue, command_queue):
        super(Server, self).__init__()
        self.command_q = command_queue
        self.data_q = data_queue
        self.commander = Commander
        self.processor = Processor
    
    def run(self):
        self.connect()
        while True:
            flag, command = self.command_q.get()
            self.command_q.task_done()
            if flag == "TERMINATE" and command is None:
                break

            else:
                commander = self.commander(flag, command)
                commander.start()

                processor = self.processor(flag, command, self.data_q)
                processor.start()

                commander.join()
                processor.join()

    def connect(self):
        pass