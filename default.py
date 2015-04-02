# -*- coding: utf-8 -*-
# default.py
import urllib,urllib2,re,xbmcplugin,xbmcgui,subprocess,sys,os,os.path,xbmcaddon,xbmcvfs,random,hashlib
import json,cookielib,gzip,time
import xbmc
from bt import TorrentFile
from xbmcswift2 import Plugin, CLI_MODE, xbmcaddon,ListItem
from StringIO import StringIO
reload(sys)
sys.setdefaultencoding('utf-8')

__addonid__ = "plugin.video.115"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__cwd__ = __addon__.getAddonInfo('path')
__resource__  = xbmc.translatePath( os.path.join( __cwd__, 'lib' ) )
sys.path.append (__resource__)
colors = {'back': '7FFF00','dir': '8B4513','video': 'FF0000','next': 'CCCCFF','bt': 'FF0066','-1':'FF0000','0':'8B4513','1':'CCCCFF','2':'7FFF00'}
class api_115(object):
	def __init__(self, cookiefile):
		self.cookiejar = cookielib.LWPCookieJar()
		if os.path.exists(cookiefile):
			self.cookiejar.load(
				cookiefile, ignore_discard=True, ignore_expires=True)
		self.opener = urllib2.build_opener(
			urllib2.HTTPCookieProcessor(self.cookiejar))

		self.headers = {
			'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.71 Safari/537.36',
			'Accept-encoding': 'gzip,deflate',
		}

	def urlopen(self, url, **args):
		#plugin.log.error(url)
		if 'data' in args and type(args['data']) == dict:
			args['data'] = json.dumps(args['data'])
			self.headers['Content-Type'] = 'application/json'
		else:
			self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
		rs = self.opener.open(
			urllib2.Request(url, headers=self.headers, **args), timeout=60)
		#urlcache[url] = rs
		return rs

	def fetch(self,wstream):
		if wstream.headers.get('content-encoding', '') == 'gzip':
			content = gzip.GzipFile(fileobj=StringIO(wstream.read())).read()
		else:
			content = wstream.read()
		return content

	def getcookieatt(self, domain, attr):
		if domain in self.cookiejar._cookies and attr in \
		   self.cookiejar._cookies[domain]['/']:
			return self.cookiejar._cookies[domain]['/'][attr].value
	def depass(self,ac,ps,co):
		eac=hashlib.sha1(ac).hexdigest()
		eps=hashlib.sha1(ps).hexdigest()
		return hashlib.sha1(hashlib.sha1(eps+eac).hexdigest()+co.upper()).hexdigest()
	def encodes(self):
		prefix = ""
		phpjs=int(random.random() * 0x75bcd15)
		retId = prefix
		retId += self.encodess(int(time.time()),8)
		retId += self.encodess(phpjs, 5)
		return retId
	def encodess(self,seed, reqWidth):
		seed = hex(int(seed))[2:]
		if (reqWidth < len(seed)):
			return seed[len(seed) - reqWidth:]
		if (reqWidth >  len(seed)):
			return (1 + (reqWidth - seed.length)).join('0') + seed
		return seed
plugin = Plugin()
ppath = plugin.addon.getAddonInfo('path')
cookiefile = os.path.join(ppath, 'cookie.dat')
xl = api_115(cookiefile)
urlcache = plugin.get_storage('urlcache', TTL=5)

@plugin.route('/login')
def login():
	plugin.open_settings()
	user = plugin.get_setting('username')
	passwd = plugin.get_setting('password')
	if not (user and passwd):
		return
	vcode=xl.encodes()
	data = urllib.urlencode({'login[ssoent]': 'B1', 'login[version]': '2.0', 'login[ssoext]': vcode,
							 'login[ssoln]':user, 'login[ssopw]':xl.depass(user,passwd,vcode),'login[ssovcode]':vcode,
							 'login[safe]':'1','login[time]':'1','login[safe_login]':'1','goto':'http://m.115.com/?ac=home'})
	xl.cookiejar.clear()
	login_page = xl.urlopen('http://passport.115.com/?ct=login&ac=ajax&is_ssl=1', data=data)
	msgs=json.loads(xl.fetch(login_page))
	if msgs['state']==True:
		plugin.notify(msg='登陆成功')
		xl.cookiejar.save(cookiefile, ignore_discard=True)
		return
	else:
		plugin.notify(msg='登陆失败,错误代码:'+str(msgs['err_msg']))
		xl.cookiejar.save(cookiefile, ignore_discard=True)
		return

@plugin.route('/')
def index():
	item = [
		{'label': '网盘', 'path': plugin.url_for('getfile',cid='0',offset=0)},
		{'label': '记事本', 'path': plugin.url_for('note',cid='0',offset=0)},
		{'label': '离线任务列表', 'path': plugin.url_for('offline_list')},
		{'label': '登入115网盘', 'path': plugin.url_for('login')},
		{'label': '清空缓存','path': plugin.url_for('clear_cache'),'is_playable': True,'properties': {'isPlayable': ''}}
	]
	return item
@plugin.route('/getfile/<cid>/<offset>')
def getfile(cid,offset):
	if cid+"/"+offset in urlcache:
		#plugin.log.error("缓存输出:"+cid+"/"+offset)
		return urlcache[cid+"/"+offset]
	else:
		#plugin.log.error("数据更新:"+cid+"/"+offset)
		data=xl.urlopen('http://web.api.115.com/files?aid=1&cid='+str(cid)+'&type=&star=0&o=user_ptime&asc=0&offset='+str(offset)+'&show_dir=1&limit=25&format=json')
		data= xl.fetch(data).replace('\n','').replace('\r','')
		data=json.loads(data[data.index('{'):])
		if data['state']:
			items=[]
			for item in data['path']:
				if item['cid']!=0 and item['cid']!=cid:
					items.append({'label': colorize_label('返回到【'+item['name']+"】", 'back'), 'path': plugin.url_for('getfile',cid=item['cid'],offset=0)})
			items.append({'label': colorize_label("制作播放列表", 'back'), 'path': plugin.url_for('lxlist',cid=cid,name=data['path'][len(data['path'])-1]['name'].encode('UTF-8'))})
			for item in data['data']:
				if item.has_key('sha'):
					if item.has_key('iv'):
						items.append({'label': colorize_label(item['n'], 'video'),'thumbnail':item['u'], 'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8')),'is_playable': True,'properties': {'isPlayable': ''}})
					elif item['ico']=='torrent':
						items.append({'label': colorize_label(item['n'], 'bt'), 'path': plugin.url_for('offline_bt',pc=item['pc']),'is_playable': True,'properties': {'isPlayable': ''}})
				else:
					items.append({'label': colorize_label(item['n'], 'dir'), 'path': plugin.url_for('getfile',cid=item['cid'],offset=0)})
			if data['count']>int(offset)+25:
				items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('getfile',cid=cid,offset=str(int(offset)+25))})
			urlcache[cid+"/"+offset] = items
			return items
		else:
			plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
			return

@plugin.route('/offline_bt/<pc>')
def offline_bt(pc):
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno('115网盘提示', '是否离线文件?')
	if ret:
		data=xl.urlopen("http://115.com/?ct=app&ac=get&flag=3&pick_code="+pc+"&_="+str(time.time()))
		data=xl.fetch(data)
		data=json.loads(data[data.index('{'):])
		if data['state']:
			bturl=data['data']['source_url']
			data=xl.urlopen(bturl)
			data=xl.fetch(data)
			try:
				tor = TorrentFile(data)
				offline("magnet:?xt=urn:btih:"+tor.btih)
			except:
				plugin.notify('读取torrent文件失败！', delay=2000)
				return
			
	else:
		return

@plugin.route('/play/<pc>/<name>')
def play(pc,name):
	stm=plugin.get_setting('select')
	dialog = xbmcgui.Dialog()
	if stm=='3':
		qtyps = [('普清', '0'),('高清', '1'), ('原码', '2')]
		sel = dialog.select('清晰度', [q[0] for q in qtyps])
		if sel is -1: return 'cancel'
		stm=str(sel)
	if stm=='2':
		data=xl.urlopen("http://web.api.115.com/files/download?pickcode="+pc+"&_="+str(time.time()))
		data=xl.fetch(data)
		data=json.loads(data[data.index('{'):])
		if data['state']:
			videourl=data['file_url']
		else:
			plugin.notify(msg='无视频文件.')
			return
	else:
		data=xl.urlopen('http://115.com/api/video/m3u8/'+pc+'.m3u8')
		data=xl.fetch(data)
		url= re.compile(r'http:(.*?)\r', re.DOTALL).findall(data)
		if len(url)==2:
			videourl='http:'+url[int(stm)]
		elif len(url)==1:
			videourl='http:'+url[0]
		else:
			plugin.notify(msg='无视频文件.')
			return
	data=xl.urlopen('http://web.api.115.com/movies/subtitle?pickcode='+pc)
	data=xl.fetch(data)
	data=json.loads(data[data.index('{'):])
	sublist = None
	if data['state']:
		sublist = [s['url'] for s in data['data']]
	#plugin.log.error(sublist)
	listitem=xbmcgui.ListItem()
	listitem.setInfo(type="Video", infoLabels={'Title': name})
	player = Player()
	player.play(videourl, listitem, sublist=sublist)
	return
@plugin.route('/offline/<url>')
def offline(url):
	xbmc.executebuiltin( "ActivateWindow(busydialog)" )
	xbmc.sleep(1000)
	data=xl.urlopen("http://115.com/?ct=offline&ac=space&_="+str(time.time()))
	data=xl.fetch(data)
	data=json.loads(data[data.index('{'):])
	sign=data['sign']
	time1=data['time']
	uid = xl.getcookieatt('.115.com', 'ssoinfoB1')
	uid=uid[:uid.index('%')]
	data = urllib.urlencode({'url': url,'uid':uid,'sign':sign,'time':time1})
	data=xl.urlopen("http://115.com/lixian/?ct=lixian&ac=add_task_url",data=data)
	data=xl.fetch(data)
	#plugin.log.error(data)
	data=json.loads(data[data.index('{'):])
	if data['state']:
		plugin.notify(u' 添加离线成功'.encode('utf-8'),delay=1000)
	else:
		plugin.notify(u' 添加离线失败,错误代码:'.encode('utf-8')+data['error_msg'],delay=1000)
	xbmc.executebuiltin( "Dialog.Close(busydialog)" )
	return
@plugin.route('/offline_list')
def offline_list():
	msg_st={'-1': '任务失败','0': '任务停止','1': '下载中','2': '下载完成'}
	data=xl.urlopen("http://115.com/?ct=offline&ac=space&_="+str(time.time()))
	data=xl.fetch(data)
	data=json.loads(data[data.index('{'):])
	sign=data['sign']
	time1=data['time']
	uid = xl.getcookieatt('.115.com', 'ssoinfoB1')
	uid=uid[:uid.index('%')]
	page=1
	task=[]
	items=[]
	while True:
		data = urllib.urlencode({'page': str(page),'uid':uid,'sign':sign,'time':time1})
		data=xl.urlopen("http://115.com/lixian/?ct=lixian&ac=task_lists",data=data)
		data=xl.fetch(data)
		data=json.loads(data[data.index('{'):])
		if data['state']:
			for item in data['tasks']:
				task.append(item)
			if data['page_count']>page:
				page=page+1
			else:
				break
		else:
			break
	for item in task:
		items.append({'label': item['name']+colorize_label("["+msg_st[str(item['status'])]+"]", str(item['status'])), 
					'path': plugin.url_for('getfile',cid=item['file_id'],offset='0')})
	return items
@plugin.route('/lxlist/<cid>/<name>')
def lxlist(cid,name):
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno('115网盘提示', '是否包含子文件夹?')
	lists=getlxlist(cid,ret)
	x=0
	#plugin.log.error(lists)
	if len(lists)>0:
		strs=name+'\n'
		for item in lists:
			strs += item['n']+"|115:"+item['pc']+"|"+item['u']+'\n'
			if len(strs)>40000:
				data = urllib.urlencode({'nid': '', 'content': strs, 'cid': '0'})		
				data=xl.urlopen("http://115.com/note/?ct=note&ac=save",data=data)
				x=x+1
				strs=name+"-"+str(x)+'\n'
		data = urllib.urlencode({'nid': '', 'content': strs, 'cid': '0'})		
		data=xl.urlopen("http://115.com/note/?ct=note&ac=save",data=data)
		data= xl.fetch(data).replace('\n','').replace('\r','')
		data=json.loads(data[data.index('{'):])
		#plugin.log.error(data)
		if data['state']:
			plugin.notify(msg='制作成功！')
		else:
			plugin.notify(msg='制作失败！'+str(data['msg']))

def getlxlist(cid,alls):
	lists=[]
	offsets=0
	if alls:
		while True:
			data=xl.urlopen("http://web.api.115.com/files?aid=1&cid="+cid+"&type=4&star=0&o=user_ptime&asc=0&offset="+str(offsets)+"&show_dir=1&limit=80&format=json")
			data= xl.fetch(data).replace('\n','').replace('\r','')
			data=json.loads(data[data.index('{'):])
			if data['state']:
				for item in data['data']:
					if item.has_key('sha'):
						if item.has_key('iv'):
							lists.append({'n':item['n'],'pc':item['pc'],'u':item['u']})
				if data['count']>data['offset']+80:
					offsets=data['offset']+80
				else:
					break;
			else:
				break;
		return lists
	else:
		while True:
			data=xl.urlopen("http://web.api.115.com/files?aid=1&cid="+cid+"&type=&star=0&o=user_ptime&asc=0&offset="+str(offsets)+"&show_dir=1&limit=80&format=json")
			data= xl.fetch(data).replace('\n','').replace('\r','')
			data=json.loads(data[data.index('{'):])
			if data['state']:
				for item in data['data']:
					if item.has_key('sha'):
						if item.has_key('iv'):
							lists.append({'n':item['n'],'pc':item['pc'],'u':item['u']})
				if data['count']>data['offset']+80:
					offsets=data['offset']+80
				else:
					break;
			else:
				break;
		return lists

@plugin.route('/note/<cid>/<offset>')
def note(cid,offset):
	if cid+"/note/"+offset in urlcache:
		#plugin.log.error("缓存输出:"+cid+"/note/"+offset)
		return urlcache[cid+"/note/"+offset]
	else:
		#plugin.log.error("数据更新:"+cid+"/note/"+offset)
		data=xl.urlopen('http://115.com/note/?ct=note&page_size=9999&cid='+str(cid)+'&start='+str(offset))
		data= xl.fetch(data).replace('\n','').replace('\r','')
		data=json.loads(data[data.index('{'):])
		if data['state']:
			items=[]
			for item in data['data']:
				items.append({'label': colorize_label(item['title'], 'dir'),'path': plugin.url_for('getnote',nid=item['nid'])})
			urlcache[cid+"/note/"+offset] = items
			return items
		else:
			plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
			return
@plugin.route('/getnote/<nid>')
def getnote(nid):
	if nid+"/note" in urlcache:
		#plugin.log.error("缓存输出:"+nid+"/note")
		return urlcache[nid+"/note"]
	else:
		#plugin.log.error("数据更新:"+nid+"/note")
		data=xl.urlopen('http://115.com/note/?ct=note&ac=detail&nid='+nid)
		data= xl.fetch(data).replace('\n','').replace('\r','')
		data=json.loads(data[data.index('{'):])
		if data['state']:
			items=[]
			content=data['data']['content'].split('\n')
			for item in content:
				if item != data['data']['title']:
					temp=item.split('|')
					if len(temp)==2:
						items.append({'label': colorize_label(temp[0], 'video'),'path': plugin.url_for('playnote',url=temp[1].encode('UTF-8'))})
					elif len(temp)==3:
						items.append({'label': colorize_label(temp[0], 'video'),'thumbnail':temp[2],'path': plugin.url_for('playnote',url=temp[1].encode('UTF-8'))})
					else:
						items.append({'label': colorize_label(item, 'video'),'path': plugin.url_for('playnote',url=item.encode('UTF-8'))})

			#plugin.log.error(content)
			#urlcache[nid+"/note"] = items
			return items
		else:
			plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
@plugin.route('/playnote/<url>')
def playnote(url):
	dialog = xbmcgui.Dialog()
	if 'magnet:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'http:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'ftp:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'https:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'ed2k:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif '115:' in url:
		play(url[4:],url)
@plugin.route('/clear_cache/')
def clear_cache():
    urlcache.clear()
    plugin.notify(u'缓存清除完毕！'.encode('utf-8'))

class Player(xbmc.Player):

    def play(self, item='', listitem=None, windowed=False, sublist=None):
        self._sublist = sublist

        super(Player, self).play(item, listitem, windowed)

        self._start_time = time.time()
        while True:
            # print self._start_time, time.time()
            if self._stopped or time.time() - self._start_time > 30:
                if self._totalTime == 999999:
                    raise PlaybackFailed(
                        'XBMC silently failed to start playback')
                break

            xbmc.sleep(500)
        # print 'play end'

    def __init__(self):
        self._stopped = False
        self._totalTime = 999999

        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)

    def onPlayBackStarted(self):
        self._totalTime = self.getTotalTime()
        self._start_time = time.time()

        sublist = self._sublist
        if sublist:
            for surl in sublist:
                # print '$'*50, surl
                self.setSubtitles(surl)
            self.setSubtitleStream(0)
            self.showSubtitles(False)

    def onPlayBackStopped(self):
        self._stopped = True

    def onPlayBackEnded(self):
        self.onPlayBackStopped()

class PlaybackFailed(Exception):

    '''Raised to indicate that xbmc silently failed to play the stream'''



def colorize_label(label, _class=None, color=None):
	color = color or colors.get(_class)

	if not color:
		return label

	if len(color) == 6:
		color = 'FF' + color

	return '[COLOR %s]%s[/COLOR]' % (color, label)


if __name__ == '__main__':
	plugin.run()
