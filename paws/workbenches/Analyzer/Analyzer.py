from multiprocessing import Process
from threading import Thread
import sys
import os
from .Designer import Designer
from .Reducer import Reducer

class Analyzer(Process):
    def __init__(self, data_queue, command_queue, stdin): # TODO: replace stdin with relevant gui interface
        super(Analyzer, self).__init__()
        self.command_q = command_queue
        self.data_q = data_queue
        self.designer = Designer
        self.reducer = Reducer
        self.data = None
        self.stdin = stdin
        sys.stdin = os.fdopen(stdin)
    
    def run(self):
        while True:
            flag = input("Command: ")
            if flag.lower() == "quit" or flag.lower() == 'q':
                self.command_q.put(("TERMINATE", None))
                break

            else:
                designer = self.designer(flag, self.stdin, self.command_q)
                designer.start()

                reducer = self.reducer(self.data_q)
                reducer.start()

                designer.join()
                reducer.join()
                self.update_data(reducer.data)
    
    def update_data(self, data):
        pass


    

