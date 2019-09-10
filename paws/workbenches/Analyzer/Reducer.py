from threading import Thread

class Reducer(Thread):
    def __init__(self, data_queue):
        super(Reducer, self).__init__()
        self.data = None
