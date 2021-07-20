from subprocess import Popen, PIPE, STDOUT
import threading
import re
import os
import time
import datetime
import json

Magic = "vYK1JQ6DgAUdwORN"
Alias = "becrock_serve"
node=None
logging=None
cwd=os.path.abspath('.')
nLine=0

def _pOut():
    global node
    with node.proc:
        while True:
            if node.killio:
                break
            if node.proc is None:
                time.sleep(0.1)
                continue
            # if node.proc is None or node.proc.returncode or node.proc.poll() is not None:
            #     continue
            o=node.proc.stdout.readline().strip()
            if not o:
                continue
            logging.info("["+node.name+"]:\t"+o)
            node.stdout.append(o)
            time.sleep(0.1)

def _pIn():
    global node
    with node.proc:
        while True:
            if node.killio:
                break
            if node.proc is None:
                time.sleep(0.05)
                continue
            if not node.ready:
                time.sleep(0.05)
                continue
            for s in node.stdin.copy():
                node.proc.stdin.write(s+'\n')
                node.proc.stdin.flush()
                node.stdin.remove(s)
            time.sleep(0.05)

# Starts the minecraft server
def _start():
    if node.proc==None:
        logging.info("["+node.name+"]:\tStarting Bedrock Server")
        node.killio=False
        #node.thIO['stdin']=threading.Thread(target=_pIn)
        node.thIO['stdout']=threading.Thread(target=_pOut)
        node.proc=Popen([cwd+os.path.sep+'bedrock_server'], stdout=PIPE, stdin=PIPE, stderr=STDOUT, universal_newlines=True,cwd=cwd)
        node.stdin=[]
        node.stdout=[]
        node.users={}
        if os.path.isfile('users.json'):
            with open('users.json','r') as f:
                node.users=json.load(f)
            for v in node.users.keys():
                node.users[v]['is_online']=False
        node.watchers={'user_watch':[0,0]}
        time.sleep(2)
        # node.thIO['stdin'].start()
        node.thIO['stdout'].start()
        version=_watch('\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} INFO\] Version (.*)')
        _watch('\[INFO\] Server started\.')
        node.ready=True
        logging.info("["+node.name+"]:\tBedrock Server Started, Version: %s",version)
        return True
    return False

# Sends a command to stdin
def _cmd(c,a=None,rt=0):
    global node
    # await=regexp response
    node.stdin.append(c)
    for s in node.stdin.copy():
        node.proc.stdin.write(s+'\n')
        node.proc.stdin.flush()
        node.stdin.remove(s)
    if a==None:
        return
    return _watch(a,rt)

# Awaits stdout to match regex pattern
def _watch(r,t=0):
    global nLine
    while True:
        stdout=node.stdout.copy()
        if nLine<len(stdout):
            for l in stdout[nLine:]:
                if t==0:
                    m=re.search(r,l)
                    if m:
                        return True
                elif t==1:
                    m=re.match(r,l)
                    if m:
                        return m
                elif t==2:
                    return re.findall(r,l)
            nLine=len(stdout)
        time.sleep(1)

# Requests server shutdown
def _stop(force=False):
    logging.info("["+node.name+"]:\tStopping Bedrock Server")
    if node.proc!=None:
        if not force:
            _cmd('stop','Quit correctly')
            node.proc.wait(timeout=15)
        node.proc.terminate()
        node.proc=None
    logging.info("["+node.name+"]:\tBedrock Server Stopped")
    logging.info("["+node.name+"]:\tStopping Bedrock Server IO")
    node.killio=True
    # if node.thIO['stdin'].is_alive():
    # node.thIO['stdin'].join()
    # if node.thIO['stdout'].is_alive():
    node.thIO['stdout'].join()
    node.ready=False
    node.stdin=None
    logging.info("["+node.name+"]:\tStopped Bedrock Server IO")
    if not node.preserveLog:
        node.stdout=None

# Called before _loop_
def __init__(n,l):
    global node
    global logging
    global nLine
    node=n
    logging=l
    node.id=Magic
    # node.preserveLog=False
    node.proc=None
    node.thIO={'stdin':None,'stdout':None}
    node.stdin=[]
    node.stdout=[]
    node.ready=False
    node.start=_start
    node.stop=_stop
    node.cmd=_cmd
    node.watch=_watch
    node.preserveLog=False
    node.killio=False
    node.users={}
    node.watchers={'user_watch':[0,0]}
    _start()
    logging.info("["+node.name+"]:\tInitialized")

# Called before node is reloaded after modification
def __reinit__(self):
    if node.proc!=None:
        _stop()

# Called before node is terminated
def __deinit__():
    if node.proc!=None:
        _stop()

# Called at intervals default is 0.1s
def __loop__(self):
    global node
    if time.time()-node.watchers['user_watch'][0]>=1:
        node.watchers['user_watch'][0]=time.time()
        if not node.ready:
            return
        if node.stdout is None:
            return
        stdout=node.stdout.copy()
        oLine=node.watchers['user_watch'][1]
        if oLine<len(stdout):
            for l in stdout[oLine:]:
                    m=re.match('\[INFO\] Player disconnected: ([^,]*), xuid: (.+)$',l)
                    if m is not None:
                        m=list(m.groups())
                        td=datetime.datetime.now().astimezone().isoformat()
                        if not m[1] in node.users:
                            continue
                        node.users[m[1]]['is_online']=False
                        with open('users.json','w') as f:
                            json.dump(node.users,f)
                        continue
                    m=re.match('\[INFO\] Player connected: ([^,]*), xuid: (.+)$',l)
                    if m is not None:
                        m=list(m.groups())
                        print(m)
                        td=datetime.datetime.now().astimezone().isoformat()
                        logging.info("["+node.name+"]:\t%s"%({'username':m[0],'xuid':m[1],'last_seen':None,'last_login': None,'address':None,'is_online':True}))
                        if not m[1] in node.users:
                            node.users[m[1]]={'username':m[0],'xuid':m[1],'last_seen':None,'last_login': None,'address':None,'is_online':True}
                        node.users[m[1]]['last_seen']=td
                        node.users[m[1]]['first_login']=td
                        node.users[m[1]]['is_online']=True
                        with open('users.json','w') as f:
                            json.dump(node.users,f)
                        continue
            oLine=len(stdout)
            node.watchers['user_watch'][1]=oLine
        time.sleep(1)
        #
    pass
