from threading import Thread
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class Processor(Thread):
    def __init__(self, client, data_path, data_queue, recursive=True):
        super(Processor, self).__init__()
        self.end_line = ""
        self.client = client
        self.data_q = data_queue
        self.data_path = data_path
        self.watch_q = Queue()
        self.observer = Observer()
        self.recursive = recursive
        self.event_handler = ProcEventHandler(self.watch_q)
    
    def run(self):
        self.observer.schedule(self.event_handler, self.data_path,
                               self.recursive)
        self.observer.start()
        line = None
        while line:
            event = self.watch_q.get()
            self.watch_q.task_done()
            self.process(event)
            line = self.client.receive_line()
            if line == self.end_line:
                break
        else:
            self.observer.stop()

    
    def process(self, event):
        self.data_q.put(event)


class ProcEventHandler(PatternMatchingEventHandler):
    def __init__(self, watch_queue, patterns="*", **skwargs):
        super(ProcEventHandler, self).__init__(patterns, **skwargs)
        self.watch_q = watch_queue
    
    def on_any_event(self, event):
        self.watch_q.put(event)

