from threading import Thread

class Processor(Thread):
    def __init__(self, flag, command, data_queue):
        super(Processor, self).__init__()
