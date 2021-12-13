#!/usr/bin/env python 
# coding:utf-8
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import subprocess

host = ('localhost', 8886)

def read_json_data():
    with open('../data_process/data/package.json', 'r') as file_to_read:
        load_dict = json.load(file_to_read)
        print(load_dict)
        return load_dict



class Resquest(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        data = read_json_data()
        self.wfile.write(json.dumps(data).encode())



def run_code_inCMD():
    start = time.time()
    clean_command = 'python3 -m http.server 8080'
    clean_command_run = subprocess.Popen(clean_command, shell=True)
    clean_command_run.wait()
    end = time.time()
    clean_result_code = clean_command_run.returncode
    print(clean_result_code)


def run_code_test():
    ret = subprocess.check_output(['cd', '/Users/xuwei/Code'])
    print(ret)
    # run_code_inCMD()

if __name__ == '__main__':
    # run_code_test()
    server = HTTPServer(host, Resquest)
    print("Starting server, listen at: %s:%s" % host)
    server.serve_forever()



