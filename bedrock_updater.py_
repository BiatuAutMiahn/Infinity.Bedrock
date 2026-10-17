from zeroconf import ServiceBrowser, Zeroconf
from ipaddress import ip_address
from ppadb.client import Client as AdbClient
from packaging.version import parse as parse_version
from gplaycli import gplaycli
import time
import os
import json
import datetime
import requests
from zipfile import ZipFile
import re
import subprocess
import datetime

# Constants
Magic = "c8i7CmMkDd17YrEf"
Alias = "bedrock_updater"
pkg_id="com.mojang.minecraftpe"
cwd=os.path.abspath('.')

# Initial Vars
node=None
logging=None
services={}
devices={}
adb=None

def _UpdateServer():
	global logging
	global node
	try:
		modules=node.getModules()
		if not 'bedrock_server' in modules:
			logging.info("["+node.name+"]:\tbedrock_server module not found.")
			return
		logging.info("["+node.name+"]:\tChecking for Server Update")
		headers = requests.utils.default_headers()
		headers['User-Agent']="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
		srv='https://www.minecraft.net/en-us/download/server/bedrock'
		r=requests.get(srv,headers=headers)
		u=''.join(re.findall('https?\://.*linux/.*bedrock-server-.*\\.zip',r.text))
		v=''.join(re.findall('bedrock-server-(.*)\.zip',u))
		if node.minecraft_version['current']==None:
			node.minecraft_version['current']="0.0.0.0"
		if parse_version(v) <= parse_version(node.minecraft_version['current']):
			logging.info("["+node.name+"]:\tServer is up to date (%s==%s)"%(v,node.minecraft_version['current']))
			return
		logging.info("["+node.name+"]:\tUpdating Server (%s -> %s)"%(node.minecraft_version['current'],v))
		logging.info("["+node.name+"]:\tDownloading Update...")
		r = requests.get(u)
		with open("server_update.zip", "wb") as f:
			f.write(r.content)
		logging.info("["+node.name+"]:\tDownload Complete")
		logging.info("["+node.name+"]:\tNotifying Users...")
		has_users=False
		for v in modules['bedrock_server'].users:
			if v['is_online']:
				has_users=True
				break
		if has_users:
			modules['bedrock_server'].cmd('msg @a Server update is available.')
			time.sleep(5)
			modules['bedrock_server'].cmd('msg @a Server update is available.')
			time.sleep(5)
			modules['bedrock_server'].cmd('msg @a Server Update will take up to 5 minutes.')
			time.sleep(5)
			modules['bedrock_server'].cmd('msg @a Server Update will take up to 5 minutes.')
			time.sleep(5)
			modules['bedrock_server'].cmd('msg @a Server will shutdown in 30 seconds')
			time.sleep(15)
			modules['bedrock_server'].cmd('msg @a Server will shutdown in 15 seconds')
			time.sleep(5)
			modules['bedrock_server'].cmd('msg @a Server will shutdown in 10 seconds')
			for i in range(9,-1,-1):
				modules['bedrock_server'].cmd('msg @a Server will shutdown in '+str(i)+' seconds')
				time.sleep(1)
			time.sleep(5)
			modules['bedrock_server'].cmd('msg @a Server is closing...')
			logging.info("["+node.name+"]:\tUsers Notified!")
		else:
			logging.info("["+node.name+"]:\tNo Users to Notify.")
		logging.info("["+node.name+"]:\tStopping Server")
		modules['bedrock_server'].stop()
		# modules['bedrock_server'].kill()
		logging.info("["+node.name+"]:\tExtracting Update")
		with ZipFile("server_update.zip",'r') as zip:
			zip.extractall()
		logging.info("["+node.name+"]:\tFinished Update")
		os.chmod('bedrock_server',0o744)
		node.minecraft_version['current']=v
		node.minecraft_version['tstamp']=datetime.datetime.now().astimezone().isoformat()
	    # Update Version File
		# logging.info("["+node.name+"]:\tVerInfo,"+node.minecraft_version)
		with open('mc_ver.json','w') as f:
			print(node.minecraft_version)
			json.dump(node.minecraft_version,f)
		modules['bedrock_server'].start()
		return True
	except Exception as e:
		node.handle_exception(e)

def _UpdateClient(addr):
	global adb
	try:
		adb=AdbClient(host="127.0.0.1", port=5037)
		time.sleep(1)
		logging.info("["+node.name+"]:\t%s Connecting..."%addr)
		if not adb.remote_connect(addr,5555):
			logging.info("["+node.name+"]:\t%s Cannot Connect to device"%addr)
			return False
		device = adb.device(addr+":5555")
		device.wait_boot_complete()
		logging.info("["+node.name+"]:\t%s Connected"%addr)
		if not device.is_installed(pkg_id):
			logging.info("["+node.name+"]:\t%s MinecraftPE not installed."%addr)
			return False
		ver=device.get_package_version_name(pkg_id)
		if parse_version(ver) >= parse_version(node.minecraft_version['latest']):
			logging.info("["+node.name+"]:\t%s MinecraftPE is updated (%s==%s)"%(addr,ver,node.minecraft_version['latest']))
			return False
		logging.info("["+node.name+"]:\t%s Updating MinecraftPE (%s -> %s)"%(addr,ver,node.minecraft_version['latest']))
		device.install(cwd+os.path.sep+pkg_id+'.apk',grand_all_permissions=True,downgrade=True,reinstall=True)
		if not device.is_installed(pkg_id):
			logging.info("["+node.name+"]:\t%s MinecraftPE not installed."%addr)
			return False
		ver=device.get_package_version_name(pkg_id)
		if parse_version(ver) >= parse_version(node.minecraft_version['latest']):
			logging.info("["+node.name+"]:\t%s MinecraftPE is updated (%s==%s)"%(addr,ver,node.minecraft_version['latest']))
			return False
	except Exception as e:
		node.handle_exception(e)
	finally:
		logging.info("["+node.name+"]:\t%s Disconnecting"%addr)
		adb.remote_disconnect(addr)
		logging.info("["+node.name+"]:\t%s Disconnected"%addr)

class MyListener:
	def remove_service(self, zeroconf, type, name):
		global services
		services.pop(name)
	def add_service(self, zeroconf, type, name):
		global services
		if name[:11]=='AirTV-Mini-':
			if not name in services:
				info=zeroconf.get_service_info(type, name)
				services[name]=info
				if len(info.addresses)>1:
					addr=[]
					for a in info.addresses:
						addr.append(ip_address(a))
					logging.info("["+node.name+"]:\t%s has too many addresses."%name)
				else:
					addr=ip_address(info.addresses[0])
					_UpdateClient(str(addr))

def getUpdateVer():
	logging.info("["+node.name+"]:\tRetrieving %s details..."%pkg_id)
	try:
		detail=node.gpc.api.details(pkg_id)
	except gplaycli.RequestError as error:
		logging.info("["+node.name+"]:\tFailed to retrieve details for %s."%pkg_id)
		return node.minecraft_version['current']
	if not detail:
		logging.info("["+node.name+"]:\tDetails for %s not found."%pkg_id)
		return node.minecraft_version['current']
	return detail['details']['appDetails']['versionString']

# Called before _loop_
def __init__(n,l):
	global node
	global logging
	node=n
	logging=l
	node.id=Magic
	try:
	    with open('mc_ver.json','r') as f:
	        node.minecraft_version=json.load(f)
	except:
	    node.minecraft_version={'current':'0.0.0.0','latest':'255.255.255.255','tstamp':None}
	node.gpc=gplaycli.GPlaycli()
	node.gpc.token_enable = False
	node.gpc.gmail_address="MegaGamerNet@gmail.com"
	node.gpc.gmail_password="nrwfmlhwlcfcfpkj"
	node.gpc.progress_bar=True
	node.gpc.verbose=False
	node.gpc.download_folder = cwd
	node.loop_interval=3600
	node.UpdateClient=_UpdateClient
	node.UpdateClients=_UpdateClients
	node.UpdateServer=_UpdateServer
	node.proc=adb = subprocess.Popen(['adb', 'start-server'])
	logging.info("["+node.name+"]:\tInitialized")

# Called before node is reloaded after modification
def __reinit__(self):
	node.proc.terminate()

# Called before node is terminated
def __deinit__():
	node.proc.terminate()

# Called at intervals default is 0.1s

def _UpdateClients():
	global adb
	global services
	services={}
	logging.info("["+node.name+"]:\tUpdating AirTV Mini Clients")
	# Starting Client Updater
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf, "_googlecast._tcp.local.", listener)
	#zeroconf.close()

def __loop__(self):
	global adb
	try:
		logging.info("["+node.name+"]:\tConnecting to Google Play API")
		success,error=node.gpc.connect()
		if not success:
			logging.info("["+node.name+"]:\tCannot connect to Google Play API")
			return
		# Check Version
		lver=getUpdateVer()
		node.minecraft_version['latest']=lver
		# if node.minecraft_version['current']==None:
			# node.minecraft_version['current']=lver
		node.minecraft_version['tstamp']=datetime.datetime.now().astimezone().isoformat()
	    # Update Version File
		with open('mc_ver.json','w') as f:
			json.dump(node.minecraft_version,f)
		if parse_version(node.minecraft_version['latest'])<=parse_version(node.minecraft_version['current']):
			logging.info("["+node.name+"]:\tNo Update Available")
			return
		logging.info("["+node.name+"]:\tUpdate Available")
		node.gpc.download([pkg_id])
	except Exception as e:
		node.handle_exception(e)
	_UpdateServer()
	_UpdateClients()
