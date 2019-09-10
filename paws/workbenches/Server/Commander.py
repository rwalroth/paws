from threading import Thread

class Commander(Thread):
    def __init__(self, flag, command):
        super(Commander, self).__init__()