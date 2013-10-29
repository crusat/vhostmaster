#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Must be started from root
"""
import SocketServer
import SimpleHTTPServer
import re
import shutil

PORT = 4242

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
from json import dumps, loads
from pwd import getpwnam


class myHandler(BaseHTTPRequestHandler):

    def getEtcHosts(self):
        f = open("/etc/hosts", "r")
        result = []
        s = f.readline()
        while s:
            if len(s) > 0 and s[0] != '#':
                m = re.match(r"(\s*127\.0\.0\.1)\s+(.+)", s)
                if m is not None:
                    result.append({
                    "address": m.group(1),
                    "server_name": m.group(2),
                    "webserver": '-'
                    })
            s = f.readline()
        f.close()
        return result

    def getNginxHosts(self):
        NGINX_CONFIG_DIRECTORY = '/etc/nginx/sites-enabled/'
        # get files
        from os import listdir
        from os.path import isfile, join
        config_files = [f for f in listdir(NGINX_CONFIG_DIRECTORY) if isfile(join(NGINX_CONFIG_DIRECTORY, f))]
        # get contents
        result = []
        for config in config_files:
            f = open(NGINX_CONFIG_DIRECTORY + config, "r")
            s = f.readline()
            while s:
                m = re.match(r"\s*server_name\s+(.+);", s)
                if m is not None:
                    result.append({
                        "config_name": config,
                        "server_name": m.group(1),
                    })
                s = f.readline()
            f.close()
        return result

    def getHosts(self):
        etc_hosts = self.getEtcHosts()
        nginx_hosts = self.getNginxHosts()
        for i in range(len(etc_hosts)):
            for nginx_host in nginx_hosts:
                if etc_hosts[i]["server_name"] == nginx_host["server_name"]:
                    etc_hosts[i]['webserver'] = 'nginx'
                    etc_hosts[i]['config_name'] = nginx_host['config_name']
        return etc_hosts

    def getLog(self, path):
        f = open(path, "r")
        result = self.tail(f, 50)
        f.close()
        return {'log': result}

    def tail(self, f, window=20 ):
        BUFSIZ = 1024
        f.seek(0, 2)
        bytes = f.tell()
        size = window
        block = -1
        data = []
        while size > 0 and bytes > 0:
            if (bytes - BUFSIZ > 0):
                # Seek back one whole BUFSIZ
                f.seek(block*BUFSIZ, 2)
                # read BUFFER
                data.append(f.read(BUFSIZ))
            else:
                # file too small, start from begining
                f.seek(0,0)
                # only read what was not read
                data.append(f.read(bytes))
            linesFound = data[-1].count('\n')
            size -= linesFound
            bytes -= BUFSIZ
            block -= 1
        return '\n'.join(''.join(data).splitlines()[-window:])

    #Handler for the GET requests
    def do_GET(self):
        try:
            #Check the file extension required and
            #set the right mime type
            if self.path == "/api/get_hosts":
                hosts = self.getHosts()
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps(hosts))
                return
            if self.path == "/api/get_log/nginx/access":
                log = self.getLog('/var/log/nginx/access.log')
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps(log))
                return
            if self.path == "/api/get_log/nginx/error":
                log = self.getLog('/var/log/nginx/error.log')
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps(log))
                return
            if self.path == "/api/restart/nginx":
                bashCommand = 'sudo service nginx restart'
                import subprocess
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output = process.communicate()[0]
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps({
                    'output': output
                }))
                return
            if self.path == "/api/restart/php-fpm":
                bashCommand = 'sudo service php5-fpm restart'
                import subprocess
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output = process.communicate()[0]
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps({
                    'output': output
                }))
                return

            sendReply = False
            if self.path.endswith(".html"):
                mimetype = 'text/html'
                sendReply = True
            if self.path.endswith(".jpg"):
                mimetype = 'image/jpg'
                sendReply = True
            if self.path.endswith(".png"):
                mimetype = 'image/png'
                sendReply = True
            if self.path.endswith(".gif"):
                mimetype = 'image/gif'
                sendReply = True
            if self.path.endswith(".js"):
                mimetype = 'application/javascript'
                sendReply = True
            if self.path.endswith(".css"):
                mimetype = 'text/css'
                sendReply = True
            if not sendReply:
                self.path = "/index.html"
                mimetype = 'text/html'
                sendReply = True

            if sendReply == True:
                #Open the static file requested and send it
                f = open(os.curdir + os.sep + self.path)
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return



        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)


    def addHostToEtcHosts(self, server_name):
        # Проверяем, если эта запись уже есть в /etc/hosts
        f = open("/etc/hosts", "r")
        s = f.readline()
        found = False
        while s and not found:
            if len(s) > 0 and s[0] != '#':
                m = re.match(r"(\s*127\.0\.0\.1)\s+"+re.escape(server_name), s)
                if m is not None:
                    found = True
            s = f.readline()
        f.close()
        if not found:
            with open("/etc/hosts", "a") as f:
                f.write("127.0.0.1    %s\r\n" % (server_name,))
        return True

    def powerDirCreate(self, dir):
        try:
            os.makedirs(dir, 0755)
        except:
            pass
        return

    def addConfig(self, server_name, root_dir, engine):
        source_config_filename = os.curdir + os.sep + 'configs' + os.sep + 'nginx' + os.sep + 'joomla.conf'
        dest_config_filename = '/etc/nginx/sites-available/'+server_name
        #shutil.copy2(source_config_filename, dest_config_filename)
        o = open(dest_config_filename, "a")
        for line in open(source_config_filename):
           line = line.replace("{{server_name}}", server_name)
           line = line.replace("{{root_dir}}", root_dir)
           o.write(line + "\n")
        o.close()
        os.symlink('/etc/nginx/sites-available/'+server_name, '/etc/nginx/sites-enabled/'+server_name)


    def addHost(self, server_name, root_dir, public_dir, user):
        self.addHostToEtcHosts(server_name)
        self.powerDirCreate(root_dir)
        self.powerDirCreate(root_dir + public_dir)
        uid = getpwnam(user)[2]
        gid = getpwnam(user)[3]
        os.chown(root_dir, uid, gid)
        os.chown(root_dir + public_dir, uid, gid)
        self.addConfig(server_name, root_dir, None)
        return

    def delHostToEtcHosts(self, server_name):
        fn = '/etc/hosts'
        f = open(fn)
        output = []
        regex = "^\s*127\.0\.0\.1\s+"+re.escape(server_name)+"\s*$"
        for line in f:
            if not re.match(regex, line):
                output.append(line)
        f.close()
        f = open(fn, 'w')
        f.writelines(output)
        f.close()
        return

    def delConfig(self, server_name):
        config_filename = '/etc/nginx/sites-available/'+server_name
        config_symlink = '/etc/nginx/sites-enabled/'+server_name
        #shutil.copy2(source_config_filename, dest_config_filename)
        try:
            os.remove(config_filename)
        except OSError:
            pass
        try:
            os.remove(config_symlink)
        except OSError:
            pass

    def delFiles(self, server_name):
        # search directory path of server_name
        try:
            config_filename = '/etc/nginx/sites-available/'+server_name
            directory = None
            f = open(config_filename, 'r')
            s = f.readline()
            while s:
                if len(s) > 0 and s[0] != '#':
                    m = re.match(r"\s*root\s+([^;]*);", s)
                    if m is not None:
                        directory = m.group(1)
                s = f.readline()
            f.close()
            # rm files
            if directory is not None:
                shutil.rmtree(directory)
        except:
            pass
        return

    def delHost(self, server_name):
        self.delFiles(server_name)
        self.delConfig(server_name)
        self.delHostToEtcHosts(server_name)

    #Handler for the GET requests
    def do_POST(self):
        try:
            content_len = int(self.headers.getheader('content-length'))
            post_body = self.rfile.read(content_len)
            #Check the file extension required and
            #set the right mime type
            if self.path == "/api/addhost":
                output = {"error": 0}
                data = loads(post_body)
                self.addHost(data['server_name'], data['root_dir'], data['public_dir'], data['user'])
                # response
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps(output))
                return
            if self.path == "/api/deletehost":
                output = {"error": 0}
                data = loads(post_body)
                self.delHost(data['server_name'])
                # response
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps(output))
                return
            return
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)


try:
    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPServer(('', PORT), myHandler)
    print 'Started httpserver on port ', PORT

    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()