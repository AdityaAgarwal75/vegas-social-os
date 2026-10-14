"""Non-root client. Broker checks peer UID and owns privileged approval/job state."""
import json
import os
import socket


def call(message):
    raw=json.dumps(message).encode()+b'\n'
    if len(raw)>65536:raise ValueError('Administrator request exceeds 64 KiB')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as conn:
        conn.settimeout(20)
        try:conn.connect(os.getenv('VSO_ADMIN_SOCKET','/run/vegas-social-admin/broker.sock'));conn.sendall(raw)
        except OSError:raise ValueError('Administrator broker is unavailable; install/inspect the local broker service') from None
        data=bytearray()
        while not data.endswith(b'\n'):
            chunk=conn.recv(8192)
            if not chunk:raise ValueError('Broker disconnected')
            data.extend(chunk)
            if len(data)>262144:raise ValueError('Broker response exceeded bound')
    result=json.loads(data)
    if 'error' in result:raise ValueError(result['error'])
    return result['result']


def request(engine,operation,arguments,request_id):
    result=call({'action':'request','operation':operation,'arguments':arguments,'request_id':request_id})
    result['approval_url']=engine.base+'/admin#'+result['id']
    return result
