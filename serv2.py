#!/usr/bin/python


import os
import errno
import signal
import socket
import logging
import time


logger = logging.getLogger('main')


BIND_ADDRESS = ('localhost', 8999)
BACKLOG = 5


def collect_zombie_children(signum, frame):
    while True:
        try:
            # �� ����������� waitpid (���������)
            pid, status = os.waitpid(-1, os.WNOHANG)
            logger.info('Vanish children pid=%d status=%d' % (pid, status))
            if pid == 0: # ������ ������ ���
                break
        except ChildProcessError as e:
            if e.errno == errno.ECHILD:
                # ��, ������ �������� ���
                break
            raise


def handle(sock, clinet_ip, client_port):
    # ����������, ���������� � ��������-�������
    logger.info('Start to process request from %s:%d' % (clinet_ip, client_port))
    # �������� ��� ������ �� �������� ������
    # (��� �� ����� ������� ������, ����� ������� ����� ��������� �����,
    # ���� ��� ������ ����� �������; �� ��� ����� ����� -- �����)
    in_buffer = b''
    while not in_buffer.endswith(b'\n'):
        in_buffer += sock.recv(1024)
    logger.info('In buffer = ' + repr(in_buffer))
    # ���������� ������ ���������
    time.sleep(5)
    # �������� ���������
    try:
        result = str(eval(in_buffer, {}, {}))
    except Exception as e:
        result = repr(e)
    out_buffer = result.encode('utf-8') + b'\r\n'
    logger.info('Out buffer = ' + repr(out_buffer))
    # ����������
    sock.sendall(out_buffer)
    logger.info('Done.')


def serve_forever():
    # ������ ��������� �����
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # re-use port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(BIND_ADDRESS)
    sock.listen(BACKLOG)
    # ������� � ��� ��������� ������ ��������� ����������,
    # ��������� �������, ������� ����� ��� ������������
    logger.info('Listning no %s:%d...' % BIND_ADDRESS)
    while True:
        try:
            connection, (client_ip, clinet_port) = sock.accept()
        except IOError as e:
            if e.errno == errno.EINTR:
                continue
            raise

        pid = os.fork()
        if pid == 0:
            # ���� ��� ����������� � �������
            # ������� �� ������ ��������� �����; ����� ���������
            sock.close()
            # ������������ ������� ������ � ��������� �����
            handle(connection, client_ip, clinet_port)
            # ������� �� ����� � ��������� ������ ������
            break

        # ���� ��� ����������� � ��������
        # �������� �� ����� ������� �����������, �� ��� ���������
        connection.close()


def main():
    # ����������� �������
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(process)s] %(message)s',
        '%H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info('Run')
    # ���������� ������� ������
    signal.signal(signal.SIGCHLD, collect_zombie_children)
    # ��������� ������
    serve_forever()


main()
