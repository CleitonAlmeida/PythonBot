#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
An IRC Python Bot
"""
import argparse
import yaml
import socket
import re

# my ficking version
VERSION = '1.0'

# another consts
SOCKET_TIMEOUT = 1000.0
BUFFER_SIZE = 4096


class Bot(object):
    """
    Bot controller class
    """
    def __init__(self, config):
        self.config = config
        self.sock = None
        self.must_quit = False

    def log(self, message):
        """
        An log method who print only if DEBUG is enabled
        """
        if self.config['DEBUG']:
            print message

    def connect(self):
        """
        Create connection and enter channels
        """
        # create connection socket
        self.log('*** connecting ***')
        self.sock = socket.create_connection((self.config['SERVER'], self.config['PORT']))
        self.sock.settimeout(SOCKET_TIMEOUT)

        # initially use __nick__ (I hope nobody will connect using it :)
        self.log('*** authenticating ***')
        self.send_command('NICK', ['__%s__' % self.config['NICK']])
        self.send_command('USER', [self.config['NICK'], "''", "''"], 'python')

        # regain nick, if it is in use
        self.send_command('NICKSERV', ['REGAIN', self.config['NICK'], self.config['PASSWORD']])

        # change to the real nick
        self.send_command('NICK', [self.config['NICK']])
        self.send_command('NICKSERV', ['IDENTIFY', self.config['PASSWORD']])

        self.log('*** joining channels [%s] ***' % ', '.join(self.config['CHANNELS']))
        # join the channel
        for channel in self.config['CHANNELS']:
            self.send_command('JOIN', [channel])

    def close(self):
        """
        Close connections
        :return:
        """
        self.log('*** disconnecting ***')
        self.sock.close()

    def run(self):
        """
        Run listening to messages and commands
        """
        self.log('*** now listening ***')
        while not self.must_quit:
            self.receive_command()

    def send_command(self, command, params, args=None):
        """
        Send a command
        :param command: command name
        :param params: command parameters
        :param args: command and parameters arguments
        """
        message = '%s ' % command
        for item in params:
            message += '%s ' % item
        if args is not None:
            message += ':%s' % args
        message += '\r\n'
        self.log('>>> sending command: %s' % message)
        self.sock.send(message)

    def receive_command(self):
        """
        Receive commands and messages from the server
        """
        for line in self._receive_package():
            self.log('<<< message: %s' % line)

    def _receive_package(self):
        """
        Private method to receive server packages
        :return: formated Message
        """
        newline = re.compile('\r*\n')
        buf = ''
        while True:
            data = self.sock.recv(BUFFER_SIZE)
            if not data:
                self.log('<<< no returned data (EOF?)')
                break
            self.log('<<< raw data: %s' % repr(data))
            buf += data
            while newline.search(buf):
                line, rest = newline.split(buf, 1)
                self.log('=== line: %s, rest: %s' % (line, rest))
                yield line
                buf = rest

def main(cmd_args):
    stream = file(cmd_args.config, 'r')
    config = yaml.load(stream)
    bot = Bot(config)
    bot.connect()
    bot.run()
    bot.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='config.yaml', help='configuration file to load', dest='config')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
    args = parser.parse_args()
    main(args)
