"""
Workbech is a persistent script which manages a server interface and analyzer.
Object is to decouple the server side from data processing side for ease of
moving between different servers.
"""
import multiprocessing
import os
import sys


class Workbech(object):
    def __init__(self, server, analyzer):
        self.server = server
        self.analyzer = analyzer
        self.stdin = sys.stdin.fileno()
    
    def run(self):
        data_queue = multiprocessing.Queue()
        command_queue = multiprocessing.Queue()

        server = self.server(data_queue, command_queue)
        analyzer = self.analyzer(data_queue, command_queue, self.stdin)

        server.start()
        analyzer.start()

        server.join()
        analyzer.join()
    


