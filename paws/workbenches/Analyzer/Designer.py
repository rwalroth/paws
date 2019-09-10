from threading import Thread

class Designer(Thread):
    def __init__(self, flag, stdin, command_queue):
        super(Designer, self).__init__()