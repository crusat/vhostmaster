#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Must be started from root
"""
import re
import shutil
import zipfile

PORT = 4242

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
from json import dumps, loads
from pwd import getpwnam
import urllib


class myHandler(BaseHTTPRequestHandler):

    LAST_JOOMLA_DOWNLOAD_URL = 'http://joomlacode.org/gf/download/frsrelease/18622/83487/Joomla_3.1.5-Stable-Full_Package.zip'
    ENGINE_DOWNLOAD_URL_OPENCART_LAST = 'http://www.opencart.com/index.php?route=download/download/download&download_id=32'
    ENGINE_DOWNLOAD_URL_BITRIX_SMALLBUSINESS_LAST = 'http://www.1c-bitrix.ru/download/small_business_encode_php5.zip'

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

    def nginxRestart(self):
        bashCommand = 'sudo service nginx restart'
        import subprocess
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        return process.communicate()[0]

    def phpfpmRestart(self):
        bashCommand = 'sudo service php5-fpm restart'
        import subprocess
        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        return process.communicate()[0]

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
                output = self.nginxRestart()
                mimetype = 'application/json'
                self.send_response(200)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(dumps({
                    'output': output
                }))
                return
            if self.path == "/api/restart/php-fpm":
                output = self.phpfpmRestart()
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

    def addConfig(self, server_name, root_dir, public_dir, engine):
        if engine == 'joomla' or engine == 'opencart' or engine == 'phpmyadmin':
            source_config_filename = os.curdir + os.sep + 'configs' + os.sep + 'nginx' + os.sep + 'default_php_site.conf'
        elif engine == 'bitrix_smallbusiness':
            source_config_filename = os.curdir + os.sep + 'configs' + os.sep + 'nginx' + os.sep + 'bitrix.conf'
        else:
            source_config_filename = os.curdir + os.sep + 'configs' + os.sep + 'nginx' + os.sep + 'none.conf'
        dest_config_filename = '/etc/nginx/sites-available/'+server_name
        #shutil.copy2(source_config_filename, dest_config_filename)
        o = open(dest_config_filename, "a")
        for line in open(source_config_filename):
           line = line.replace("{{server_name}}", server_name)
           line = line.replace("{{root_dir}}", root_dir)
           line = line.replace("{{public_dir}}", public_dir)
           o.write(line)
        o.close()
        os.symlink('/etc/nginx/sites-available/'+server_name, '/etc/nginx/sites-enabled/'+server_name)

    def installEngine(self, root_dir, public_dir, engine):
        if engine == 'joomla':
            if not os.path.exists(os.curdir + os.sep + 'tmp' + os.sep + "joomla.zip"):
                urllib.urlretrieve(self.LAST_JOOMLA_DOWNLOAD_URL, os.curdir + os.sep + 'tmp' + os.sep + "joomla.zip")
            with zipfile.ZipFile(os.curdir + os.sep + 'tmp' + os.sep + "joomla.zip", "r") as z:
                z.extractall(root_dir + public_dir + os.sep)
                #phpMyAdmin-4.0.8-all-languages
        elif engine == 'phpmyadmin':
            if not os.path.exists(os.curdir + os.sep + 'tmp' + os.sep + "phpmyadmin"):
                with zipfile.ZipFile(os.curdir + os.sep + 'engines' + os.sep + "phpmyadmin" + os.sep + "phpMyAdmin-4.0.8-all-languages.zip", "r") as z:
                    z.extractall(os.curdir + os.sep + 'tmp' + os.sep + "phpmyadmin")
            os.rmdir(root_dir + public_dir + os.sep)
            shutil.copytree(os.curdir + os.sep + 'tmp' + os.sep + "phpmyadmin" + os.sep + "phpMyAdmin-4.0.8-all-languages",
                            root_dir + public_dir + os.sep)
        elif engine == 'opencart':
            if not os.path.exists(os.curdir + os.sep + 'tmp' + os.sep + "opencart.zip"):
                urllib.urlretrieve(self.ENGINE_DOWNLOAD_URL_OPENCART_LAST, os.curdir + os.sep + 'tmp' + os.sep + "opencart.zip")
            if not os.path.exists(os.curdir + os.sep + 'tmp' + os.sep + "opencart"):
                with zipfile.ZipFile(os.curdir + os.sep + 'tmp' + os.sep + "opencart.zip", "r") as z:
                    z.extractall(os.curdir + os.sep + 'tmp' + os.sep + "opencart")
            os.rmdir(root_dir + public_dir + os.sep)
            shutil.copytree(os.curdir + os.sep + 'tmp' + os.sep + "opencart" + os.sep + "opencart-1.5.6" + os.sep + "upload",
                            root_dir + public_dir + os.sep)
            # specially for opencart configs
            #print root_dir + public_dir + os.sep + "config-dist.php", root_dir + public_dir + os.sep + "config.php"
            os.rename(root_dir + public_dir + os.sep + "config-dist.php",
                      root_dir + public_dir + os.sep + "config.php")
            os.rename(root_dir + public_dir + os.sep + "admin" + os.sep + "config-dist.php",
                      root_dir + public_dir + os.sep + "admin" + os.sep + "config.php")
        elif engine == 'bitrix_smallbusiness':
            if not os.path.exists(os.curdir + os.sep + 'tmp' + os.sep + "bitrix_smallbusiness.zip"):
                urllib.urlretrieve(self.ENGINE_DOWNLOAD_URL_BITRIX_SMALLBUSINESS_LAST, os.curdir + os.sep + 'tmp' + os.sep + "bitrix_smallbusiness.zip")
            if not os.path.exists(os.curdir + os.sep + 'tmp' + os.sep + "bitrix_smallbusiness"):
                with zipfile.ZipFile(os.curdir + os.sep + 'tmp' + os.sep + "bitrix_smallbusiness.zip", "r") as z:
                    z.extractall(os.curdir + os.sep + 'tmp' + os.sep + "bitrix_smallbusiness")
            os.rmdir(root_dir + public_dir + os.sep)
            shutil.copytree(os.curdir + os.sep + 'tmp' + os.sep + "bitrix_smallbusiness",
                            root_dir + public_dir + os.sep)
            ## specially for opencart configs
            #print root_dir + public_dir + os.sep + "config-dist.php", root_dir + public_dir + os.sep + "config.php"
            #os.rename(root_dir + public_dir + os.sep + "config-dist.php",
            #          root_dir + public_dir + os.sep + "config.php")
            #os.rename(root_dir + public_dir + os.sep + "admin" + os.sep + "config-dist.php",
            #          root_dir + public_dir + os.sep + "admin" + os.sep + "config.php")
        else:
            shutil.copyfile(os.curdir + os.sep + 'engines' + os.sep + 'none' + os.sep + 'index.html',
                            root_dir + public_dir + os.sep + 'index.html')

    def chowntree(self, path, uid, gid):
        os.chown(path, uid, gid)
        for item in os.listdir(path):
            itempath = os.path.join(path, item)
            if os.path.isfile(itempath):
                os.chown(itempath, uid, gid)
            elif os.path.isdir(itempath):
                os.chown(itempath, uid, gid)
                self.chowntree(itempath, uid, gid)


    def addHost(self, server_name, root_dir, public_dir, user, engine):
        self.addHostToEtcHosts(server_name)
        self.powerDirCreate(root_dir)
        self.powerDirCreate(root_dir + public_dir)
        uid = getpwnam(user)[2]
        gid = getpwnam(user)[3]
        self.installEngine(root_dir, public_dir, engine)
        self.chowntree(root_dir, uid, gid)
        self.addConfig(server_name, root_dir, public_dir, engine)
        self.nginxRestart()
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
                if len(s) > 0:
                    m = re.match(r"#\s*vhostmaster_root_dir\s+([^;]*);", s)
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
                self.addHost(data['server_name'], data['root_dir'], data['public_dir'], data['user'], data['engine'])
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