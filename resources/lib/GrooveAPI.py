import urllib, urllib2, unicodedata, re, os, traceback, sys, pickle, socket, string, time, random, sha, md5
from operator import itemgetter, attrgetter

sys.path.append('/home/solver/.xbmc/addons/script.module.simplejson/lib')
import simplejson as json

import traceback
from gw import Request as Request
from gw import JsonRPC as gwAPI

CLIENT_NAME = "gslite" #htmlshark #jsqueue
CLIENT_VERSION = "20101012.37" #"20100831.25"

RANDOM_CHARS = "1234567890abcdef"
VALIDITY_SESSION = 172800 #2 days
VALIDITY_TOKEN = 1000 # ca. 16 min.

class LoginTokensExceededError(Exception):
	def __init__(self):
		self.value = 'You have created to many tokens. Only 12 are allowed'
	def __str__(self):
		return repr(self.value)
		
class LoginUnknownError(Exception):
	def __init__(self):
		self.value = 'Unable to get a new session ID. Wait a few minutes and try again'
	def __str__(self):
		return repr(self.value)

class SessionIDTryAgainError(Exception):
	def __init__(self):
		self.value = 'Unable to get a new session ID. Wait a few minutes and try again'
	def __str__(self):
		return repr(self.value)

class AuthRequest(Request):
	def __init__(self, api, parameters, method, type="default", clientVersion=None):
		if clientVersion != None:
			if float(clientVersion) < float(CLIENT_VERSION):
				clientVersion = CLIENT_VERSION
		if clientVersion == None:
			clientVersion = CLIENT_VERSION
		postData = {
			"header": {
				"client": CLIENT_NAME,
				"clientRevision": clientVersion,
				"uuid": api._uuid,
				"session": api._session},
				"country": {"IPR":"1021", "ID":"223", "CC1":"0", "CC2":"0", "CC3":"0", "CC4":"2147483648"},
				"privacy": 1,
			"parameters": parameters,
			"method": method}
			
		headers = {
			"Content-Type": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 (.NET CLR 3.5.30729)",			
			"Referer": "http://listen.grooveshark.com/main.swf?cowbell=fe87233106a6cef919a1294fb2c3c05f"
			}
		url = 'https://cowbell.grooveshark.com/more.php?' + method
		postData["header"]["token"] = api._generateToken(method)
		postData = json.dumps(postData)
		self._request = urllib2.Request(url, postData, headers)
		

class GrooveAPI(gwAPI):
	def __init__(self, cwd = None, enableDebug = False, clientUuid = None, clientVersion = None):
#		import simplejson
#		self.simplejson = simplejson
		sys.path.append(os.path.join(cwd,'uuid'))
		import uuid
		self.clientVersion = clientVersion
		timeout = 40
		socket.setdefaulttimeout(timeout)
		self.enableDebug = enableDebug
		self.loggedIn = 0
		self.radioEnabled = 0
		self.userId = 0
		self.seedArtists = []
		self.frowns = []
		self.songIDsAlreadySeen = []
		self.recentArtists = []
		self.rootDir = cwd
		self.dataDir = 'addon_data'
		self.confDir = cwd
		#self.startSession()
		self._isAuthenticated = False
		self._authenticatedUserId = -1
		self._authenticatedUser = ''
		self._username = ''
		self._password = ''

	def authenticate(self):
		if self._isAuthenticated == True:
			if self._authenticatedUser == self._username:
				self.debug('Already logged in')
				return True
			else:
				self.generateInstance()
		if (self._username != '') and (self._password != ''):
			parameters = {
				"username": self._username,
				"password": self._password,
				"savePassword": 0,
				}
			try:
				response = AuthRequest(self, parameters, "authenticateUser").send()
				res = response['result']
				self._authenticatedUserId= res['userID']
				self._authenticatedUser = self._username
				self._isAuthenticated = True
			except:
				self.debug('Failed to log in')
				self._isAuthenticated = False
				self._authenticatedUserId = -1
				self._authenticatedUser = ''
		else:
			self._isAuthenticated = False
			self._authenticatedUserId = -1
			self._authenticatedUser = ''
		
		self.saveInstance()
		return self._isAuthenticated

	def getUserId(self):
		return self._authenticatedUserId

	def isLoggedIn(self):
		return self._isAuthenticated

	def _generateToken(self, method):
		#Overload _generateToken()
		if (time.time() - self._lastTokenTime) >= VALIDITY_TOKEN:
			self.debug('_generateToken(): Token has expired')
			self._token = self._getToken()
			self._lastTokenTime = time.time()
			self.saveInstance()

		randomChars = ""
		while 6 > len(randomChars):
			randomChars = randomChars + random.choice(RANDOM_CHARS)

		token = sha.new(method + ":" + self._token + ":quitStealinMahShit:" + randomChars).hexdigest()
				#:quitBasinYoBidnessPlanOnBuildingALargeUserbaseViaCopyrightInfringment:

		if (time.time() - self._lastSessionTime) >= VALIDITY_SESSION:
			self.debug('_generateToken(): Session has expired')
			self.generateInstance()

		return randomChars + token

	def startSession(self, username = '', password = ''):
		#Overload startSession()
		self._username = username
		self._password = password
		self.debug('Starting session')
		s = self.loadInstance()
		self.debug('Saved instance: ' + str(s))
		try:
			self._session, self._lastSessionTime, self._token, self._lastTokenTime, self._uuid, self._authenticatedUser, self._isAuthenticated, self._authenticatedUserId = s
			if (time.time() - self._lastSessionTime) >= VALIDITY_SESSION:
				self.debug('_startSession(): Session has expired')
				self.generateInstance()
		except:
			self.generateInstance()
			traceback.print_exc()

	def generateInstance(self):
		self.debug('Generating new instance')
		self._uuid = self._generateUUID()
		self._session = self._parseHomePage()
		self._token = self._getToken()
		self._lastTokenTime = time.time()
		self._lastSessionTime = time.time()
		self._isAuthenticated = False
		self._authenticatedUserId = -1
		self._authenticatedUser = ''
		self.saveInstance()

	def __del__(self):
		try:
			if self.loggedIn == 1:
				self.logout()
		except:
			pass

	def enabledDebug(self, v):
		if v == True:
			self.enableDebug == True
		if v == False:
			self.enableDebug == False
			
	def debug(self, msg):
		if self.enableDebug == True:
			print 'GrooveAPI: ' + str(msg)
			
	def setRemoveDuplicates(self, enable):
		if enable == True or enable == 'true' or enable == 'True':
			self.removeDuplicates = True
		else:
			self.removeDuplicates = False

	def loadInstance(self):
		path = os.path.join(self.confDir, 'instance.txt')
		try:
			f = open(path, 'rb')
			res = pickle.load(f)
			f.close()
		except:
			res = None
			pass	
		return res

	def saveInstance(self):
		print 'Saving instance'
		try:
			var = (self._session, self._lastSessionTime, self._token, self._lastTokenTime, self._uuid, self._authenticatedUser, self._isAuthenticated, self._authenticatedUserId)
			print 'Saving: ' + str(var)
			path = os.path.join(self.confDir, 'instance.txt')
			self.savePickle(path, var)
		except:
			print 'Exception in saveSession: ' + str(sys.exc_info()[0])		
			traceback.print_exc()

	def saveSettings(self):
		try:
			dir = os.path.join(self.rootDir, 'data')
			# Create the 'data' directory if it doesn't exist.
			if not os.path.exists(dir):
				os.mkdir(dir)
			path = os.path.join(dir, 'settings.txt')
			self.savePickle(path, self.settings)
		except:
			print 'Exception in saveSettings()'

	def loadPickle(self, path):
		try:
			f = open(path, 'rb')
			res = pickle.load(f)
			f.close()
		except:
			res = None
			pass				
		return res

	def savePickle(self, path, var):
		try:
			f = open(path, 'wb')
			pickle.dump(var, f, protocol=pickle.HIGHEST_PROTOCOL)
			f.close()
		except IOError, e:
			print 'There was an error while saving the settings pickle (%s)' % e
			pass
		except:
			print "An unknown error occured during save settings\n"
			pass

	def getStreamURL(self, songID):
		parameters = {
			"songID": songID,
			"prefetch": False,
			"mobile": False, 
			"country": {"IPR":"1021","ID":"223", "CC1":"0", "CC2":"0", "CC3":"0", "CC4":"2147483648"}
			}
		response = Request(self, parameters,"getStreamKeyFromSongIDEx").send()
		try:
			streamKey = response["result"]["streamKey"]
			streamServer = response["result"]["ip"]
			streamServerID = response["result"]["streamServerID"]
			postData = {"streamKey": streamKey}
			postData = urllib.urlencode(postData)
			url = "http://" + streamServer + "/stream.php?" + str(postData)
			return url
		except:
			traceback.print_exc()
			return ''
		
	def login(self, username, password):
		if self.loggedIn == 1:
			return self.userId
		result = self.createUserAuthToken(username, password)
		if result == -1:
			raise LoginTokensExceededError()
		elif result == -2:
			raise LoginUnknownError()
		else:
			self.token = result[0]
			self.debug('Token:' + self.token)
			self.userId = self.loginViaAuthToken(self.token)
			if self.userId == 0:
				raise LoginUnknownError()
			else:
				self.loggedIn = 1
				return self.userId

	def loginExt(self, username, password):
		if self.loggedIn == 1:
			return self.userId
		token = md5.new(username.lower() + md5.new(password).hexdigest()).hexdigest()
		result = self.callRemote("session.loginExt", {"username": username, "token": token})
		if 'result' in result:
			if 'userID' in result['result']:
				self.loggedIn = 1
				self.userId = result['result']['userID']
				return result['result']['userID'] 
		else:
			return 0

	def loggedInStatus(self):
		return self.loggedIn
	
	def logout(self):
		self.callRemote("session.logout", {})
		self.loggedIn = 0
		
	def getSongInfo(self, songID):
		return self.callRemote("song.about", {"songID": songID})['result']['song']
	
	def userGetFavoriteSongs(self, userID):
		result = self.callRemote("user.getFavoriteSongs", {"userID": userID})
		list = self.parseSongs(result)
		return list
	
	def userGetPlaylists(self, limit=25):
		if self.loggedIn == 1:
			result = self.callRemote("user.getPlaylists", {"userID": self.userId, "limit": limit})
			if 'result' in result:
				playlists = result['result']['playlists']
			else:
				return []
			i = 0
			list = []
			while(i < len(playlists)):
				p = playlists[i]
				list.append([p['playlistName'].encode('ascii', 'ignore'), p['playlistID']])
				i = i + 1	
			return sorted(list, key=itemgetter(0))
		else:
			return []

	def playlistCreate(self, name, about):
		if self.loggedIn == 1:
			result = self.callRemote("playlist.create", {"name": name, "about": about})
			if 'result' in result:
				return result['result']['playlistID']
			else:
				return 0
		else:
			return 0
			
	def playlistGetSongs(self, playlistId, limit=25):
		result = self.callRemote("playlist.getSongs", {"playlistID": playlistId})
		list = self.parseSongs(result)
		return list
			
	def playlistDelete(self, playlistId):
		if self.loggedIn == 1:
			return self.callRemote("playlist.delete", {"playlistID": playlistId})

	def playlistRename(self, playlistId, name):
		if self.loggedIn == 1:
			result = self.callRemote("playlist.rename", {"playlistID": playlistId, "name": name})
			if 'fault' in result:
				return 0
			else:
				return 1
		else:
			return 0

	def playlistClearSongs(self, playlistId):
		if self.loggedIn == 1:
			return self.callRemote("playlist.clearSongs", {"playlistID": playlistId})

	def playlistAddSong(self, playlistId, songId, position):
		if self.loggedIn == 1:
			result = self.callRemote("playlist.addSong", {"playlistID": playlistId, "songID": songId, "position": position})
			if 'fault' in result:
				return 0
			else:
				return 1
		else:
			return 0
			
	def playlistReplace(self, playlistId, songIds):
		if self.loggedIn == 1:
			result = self.callRemote("playlist.replace", {"playlistID": playlistId, "songIDs": songIds})
			if 'fault' in result:
				return 0
			else:
				return 1
		else:
			return 0

	def autoplayStartWithArtistIDs(self, artistIds):
		result = self.callRemote("autoplay.startWithArtistIDs", {"artistIDs": artistIds})
		if 'fault' in result:
			self.radioEnabled = 0
			return 0
		else:
			self.radioEnabled = 1
			return 1		

	def autoplayStart(self, songIds):
		result = self.callRemote("autoplay.start", {"songIDs": songIds})
		if 'fault' in result:
			self.radioEnabled = 0
			return 0
		else:
			self.radioEnabled = 1
			return 1

	def autoplayGetNextSongEx(self, seedArtists = [], frowns = [], songIDsAlreadySeen = [], recentArtists = []):
		result = self.callRemote("autoplay.getNextSongEx", {"seedArtists": seedArtists, "frowns": frowns, "songIDsAlreadySeen": songIDsAlreadySeen, "recentArtists": recentArtists})
		if 'fault' in result:
			return []
		else:
			return result
	
	def radioGetNextSong(self):
		radio = self.getSavedRadio()
		if radio == None:
			return None
		else:
			seedArtists = []
			for song in radio['seedArtists']:
				seedArtists.append(song[7])
			result = self.autoplayGetNextSongEx(seedArtists, radio['frowns'], radio['songIDsAlreadySeen'], radio['recentArtists'])
			if 'fault' in result:
				return []
			else:
				song = self.parseSongs(result)
				self.radioSetAlreadyListenedSong(songId = song[0][1])
				return song

	def radioFrown(self, songId):
		self.frown.append(songId)

	def radioAlreadySeen(self, songId):
		self.songIDsAlreadySeen.append(songId)

	def radioAddArtist(self, song = None, radioName = None):
		radio = self.getSavedRadio(name = radioName)
		if radio != None and song != None:
			radio['seedArtists'].append(song)
			return self.saveRadio(radio = radio)
		else:
			return 0

	def radioStart(self):
		return 1
		radio = self.getSavedRadio()
		if radio == None:
			return 0
		else:
			seedArtists = []
			for song in radio['seedArtists']:
				seedArtists.append(song[7])
		if self.autoplayStartWithArtistIDs(seedArtists) == 1:
			self.radioEnabled = 1
			return 1
		else:
			self.radioEnabled = 0
			return 0

	def radioStop(self):
		self.seedArtists = []
		self.frowns = []
		self.songIDsAlreadySeen = []
		self.recentArtists = []
		self.radioEnabled = 0

	def radioTurnedOn(self):
		return self.radioEnabled

	def radioSetAlreadyListenedSong(self, name = None, songId = ''):
		radio = self.getSavedRadio(name = name)
		if radio != None and songId != '':
			radio['songIDsAlreadySeen'].append(songId)
			#while len(radio['songIDsAlreadySeen']) > 20:
			#	radio['songIDsAlreadySeen'].pop(0) # Trim
			return self.saveRadio(radio = radio)
		else:
			return 0

	def getSavedRadio(self, name = None):
		if name == None:
			path = os.path.join(self.confDir, 'radio', 'default.txt')
		else:
			path = os.path.join(self.confDir, 'radio', 'saved', name)
		try:
			f = open(path, 'rb')
			radio = pickle.load(f)
			f.close()
		except:
			radio = None
		return radio

	def saveRadio(self, name = None, radio = {}): #blaher
		try:
			dir = os.path.join(self.confDir, 'radio')
			# Create the 'data' directory if it doesn't exist.
			if not os.path.exists(dir):
				os.mkdir(dir)
				os.mkdir(os.path.join(dir, 'saved'))
			if name == None:
				path = os.path.join(dir, 'default.txt')
			else:
				path = os.path.join(dir, 'saved', name)
			f = open(path, 'wb')
			pickle.dump(radio, f, protocol=pickle.HIGHEST_PROTOCOL)
			f.close()
			return 1
		except IOError, e:
			print 'There was an error while saving the radio pickle (%s)' % e
			return 0
		except:
			print "An unknown error occured during save radio: " + str(sys.exc_info()[0])
			return 0

	def favoriteSong(self, songID):
		return self.callRemote("song.favorite", {"songID": songID})

	def unfavoriteSong(self, songID):
		return self.callRemote("song.unfavorite", {"songID": songID})
		
	def searchSongs(self, query, type = 'Songs'):
		parameters = {
			"query": query,
			"type": type}

		response = Request(self, parameters, "getSearchResultsEx").send()
		try:
			return self.parseSongs(response['result']['result'])
		except:
			return []

	def searchPlaylists(self, query):
		parameters = {
			"query": query,
			"type": "Playlists"}

		response = Request(self, parameters, "getSearchResultsEx").send()
		
		return response['result']['result']

	def parseSongs(self, items):
		for entry in items:
			if (entry['CoverArtFilename'] != None) and (entry['CoverArtFilename'] != ''):
				entry['CoverArtFilename'] = 'http://beta.grooveshark.com/static/amazonart/m' + entry['CoverArtFilename']
			else:
				entry['CoverArtFilename'] = os.path.join(self.rootDir, 'resources','skins','DefaultSkin','media','default-cover.png')
		return items
		try:
			if 'result' in items:
				i = 0
				list = []
				if 'songs' in items['result']:
					l = len(items['result']['songs'])
					index = 'songs'
				elif 'song' in items['result']:
					l = 1
					index = 'song'
				else:
					l = 0
					index = ''
				while(i < l):
					if index == 'songs':
						s = items['result'][index][i]
					else:
						s = items['result'][index]
					if 'estDurationSecs' in s:
						dur = s['estDurationSecs']
					else:
						dur = 0
					try:
						notIn = True
						for entry in list:
							songName = s['songName'].encode('ascii', 'ignore')
							albumName = s['albumName'].encode('ascii', 'ignore')
							artistName = s['artistName'].encode('ascii', 'ignore')
							if self.removeDuplicates == True:
								if (entry[0].lower() == songName.lower()) and (entry[3].lower() == albumName.lower()) and (entry[6].lower() == artistName.lower()):
									notIn = False
						if notIn == True:
							list.append([s['songName'].encode('ascii', 'ignore'),\
							s['songID'],\
							dur,\
							s['albumName'].encode('ascii', 'ignore'),\
							s['albumID'],\
							s['image']['tiny'].encode('ascii', 'ignore'),\
							s['artistName'].encode('ascii', 'ignore'),\
							s['artistID'],\
							s['image']['small'].encode('ascii', 'ignore'),\
							s['image']['medium'].encode('ascii', 'ignore')])
					except:
						print 'GrooveShark: Could not parse song number: ' + str(i)
						traceback.print_exc()
					i = i + 1
				return list
			else:
				return []
				pass
		except:
			print 'GrooveShark: Could not parse songs. Got this:'
			traceback.print_exc()
			return []

	def parseArtists(self, items):
		return items
		try:
			if 'result' in items:
				i = 0
				list = []
				artists = items['result']['artists']
				while(i < len(artists)):
					s = artists[i]
					try:
						list.append([s['artistName'].encode('ascii', 'ignore'),\
						s['artistID']])
					except:
						print 'GrooveShark: Could not parse album number: ' + str(i)
						traceback.print_exc()
					i = i + 1
				return list
			else:
				return []
		except:
			print 'GrooveShark: Could not parse artists. Got this:'
			traceback.print_exc()
			return []

	def parseAlbums(self, items):
		try:
			if 'result' in items:
				i = 0
				list = []
				albums = items['result']['albums']
				while(i < len(albums)):
					s = albums[i]
					try: # Avoid ascii ancoding errors
						list.append([s['artistName'].encode('ascii', 'ignore'),\
						s['artistID'],\
						s['albumName'].encode('ascii', 'ignore'),\
						s['albumID'],\
						s['image']['tiny'].encode('ascii', 'ignore')])
					except:
						print 'GrooveShark: Could not parse album number: ' + str(i)
						traceback.print_exc()
					i = i + 1
				return list
			else:
				return []
		except:
			print 'GrooveShark: Could not parse albums. Got this'
			traceback.print_exc()
			return []

	def parsePlaylists(self, items):
		try:
			if 'result' in items:
				i = 0
				list = []
				playlists = items['result']['playlists']
				while(i < len(playlists)):
					s = playlists[i]
					try: # Avoid ascii ancoding errors
						list.append([s['playlistID'],\
						s['playlistName'].encode('ascii', 'ignore'),\
						s['username'].encode('ascii', 'ignore')])
					except:
						print 'GrooveShark: Could not parse playlist number: ' + str(i)
						traceback.print_exc()
					i = i + 1
				return list
			else:
				return []
		except:
			print 'GrooveShark: Could not parse playlists. Got this:'
			print items
			return []
