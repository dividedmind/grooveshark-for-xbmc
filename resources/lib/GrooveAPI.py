import urllib2, simplejson, md5, unicodedata, re
#implement error checking and handling eventually
class GrooveAPI:
	def __init__(self):
		self.loggedIn = 0
		self.userId = 0
		self.sessionID = '74294e3e45b297fe70f462740e15f6c8'
		self.sessionID = self.getSessionFromAPI()
		if self.sessionID == '':
			self.sessionID = self.startSession()
		if self.sessionID == '':
			print 'Could not get a sessionID'

	def __del__(self):
		if self.loggedIn == 1:
			self.logout()

	def callRemote(self, method, params={}):
		data = {'header': {'sessionID': self.sessionID}, 'method': method, 'parameters': params}
		data = simplejson.dumps(data)
		#proxy_support = urllib2.ProxyHandler({"http" : "http://wwwproxy.kom.aau.dk:3128"})
		## build a new opener with proxy details
		#opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
		## install it
		#urllib2.install_opener(opener)
		req = urllib2.Request("http://api.grooveshark.com/ws/1.0/?json")
		req.add_header('Host', 'api.grooveshark.com')
		req.add_header('Content-type', 'text/json')
		req.add_header('Content-length', str(len(data)))
		req.add_data(data)
		response = urllib2.urlopen(req)
		result = response.read()
		result = simplejson.loads(result)
		response.close()
		return result
	
	def searchSongs(self, query, limit):
		songs = self.callRemote("search.songs", {"query": query, "limit": limit, "streamableOnly": 1})['result']['songs']
		i = 0
		list = []
		while(i < len(songs)):
			s = songs[i]
			list.append([s['songName'].encode('ascii', 'ignore'),\
			s['songID'],\
			s['estDurationSecs'],\
			s['albumName'].encode('ascii', 'ignore'),\
			s['albumID'],\
			s['image']['medium'].encode('ascii', 'ignore'),\
			s['artistName'].encode('ascii', 'ignore'),\
			s['artistID']])
			i = i + 1	
		return list

	def startSession(self):
		response = urllib2.urlopen("http://www.moovida.com/services/grooveshark/session_start")
		result = response.read()
		result = simplejson.loads(result)
		response.close()
		if 'header' in result:
			return result['header']['sessionID']
		else:
			return ''

	def sessionDestroy(self):
		return self.callRemote("session.destroy")
			
	def getSessionFromAPI(self):
		result = self.callRemote("session.get")
		if 'fault' in result:
			return ''
		else:
			return result['header']['sessionID']												

	def getStreamURL(self, songID):
		return self.callRemote("song.getStreamUrlEx", {"songID": songID})['result']['url']
	
	def createUserAuthToken(self, username, password):
		hashpass = md5.new(password).hexdigest()
		hashpass = username + hashpass
		hashpass = md5.new(hashpass).hexdigest()
		result = self.callRemote("session.createUserAuthToken", {"username": username, "hashpass": hashpass})
		if 'result' in result:
			return result['result']['token'], result['result']['userID']
		else:
			return None
	
	def destroyUserAuthToken(self, token):
		self.callRemote("session.destroyAuthToken", {"token": token})
		
	def loginViaAuthToken(self, token):
		result = self.callRemote("session.loginViaAuthToken", {"token": token})
		self.destroyUserAuthToken(token)
		if 'result' in result:
			self.userID = result['result']['userID']
			return result['result']['userID']
		else:
			return 0
	
	def login(self, username, password):
		if self.loggedIn == 1:
			return self.userId
		result = self.createUserAuthToken(username, password)
		if result != None:
			self.token = result[0]
			print self.token
			self.userId = self.loginViaAuthToken(self.token)
			self.loggedIn = 1
			return self.userId
		else:
			return 0
			
	def loggedInStatus(self):
		return self.loggedIn
	
	def logout(self):
		self.callRemote("session.logout", {})
		
	def getSongInfo(self, songID):
		return self.callRemote("song.about", {"songID": songID})['result']['song']
	
	#need to parse, same as search songs
	def userGetFavoriteSongs(self, userID):
		songs = self.callRemote("user.getFavoriteSongs", {"userID": userID})['result']['songs']
		i = 0
		list = []
		while(i < len(songs)):
			s = songs[i]
			list.append([str(s['songName']), s['songID'], s['estDurationSecs'], str(s['albumName']), s['albumID'], str(s['image']['medium']), str(s['artistName']), s['artistID']])
			i = i + 1
		return list
	
	def userGetPlaylists(self):
		if self.loggedIn == 1:
			result = self.callRemote("user.getPlaylists", {"userID": self.userId})
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
			return list
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
			
	def playlistGetSongs(self, playlistId):
		if self.loggedIn == 1:
			result = self.callRemote("playlist.getSongs", {"playlistID": playlistId})
			i = 0
			list = []
			#return songs
			while(i < len(result['result']['songs'])):
				s = result['result']['songs'][i]
				list.append([s['songName'].encode('ascii', 'ignore'),\
				s['songID'],\
				s['estDurationSecs'],\
				s['albumName'].encode('ascii', 'ignore'),\
				s['albumID'],\
				s['image']['medium'].encode('ascii', 'ignore'),\
				s['artistName'].encode('ascii', 'ignore'),\
				s['artistID']])
				i = i + 1	
			return list
		else:
			return []

	def playlistDelete(self, playlistId):
		if self.loggedIn == 1:
			return self.callRemote("playlist.delete", {"playlistID": playlistId})

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

	def favoriteSong(self, songID):
		return self.callRemote("song.favorite", {"songID": songID})

	def unfavoriteSong(self, songID):
		return self.callRemote("song.unfavorite", {"songID": songID})
	
	def getPopularSongs(self):
		return self.callRemote("popular.getArtists")
	
	def getMethods(self):
		return self.callRemote("service.getMethods")
	
	def searchArtists(self, query, limit):
		artists = self.callRemote("search.artists", {"query": query, "limit": limit, "streamableOnly": 1})['result']['artists']
		i = 0
		list = []
		while(i < len(artists)):
			s = artists[i]
			list.append([s['artistName'].encode('ascii', 'ignore'),\
			s['artistID']])
			i = i + 1	
		return list

	def searchAlbums(self, query, limit):
		albums = self.callRemote("search.albums", {"query": query, "limit": limit, "streamableOnly": 1})['result']['albums']
		i = 0
		list = []
		#return list
		while(i < len(albums)):
			s = albums[i]
			list.append([s['artistName'].encode('ascii', 'ignore'),\
			s['artistID'],\
			s['albumName'].encode('ascii', 'ignore'),\
			s['albumID'],\
			s['image']['medium'].encode('ascii', 'ignore')])
			i = i + 1
		return list
		
	def artistGetAlbums(self, artistId, limit):
		albums = self.callRemote("artist.getAlbums", {"artistID": artistId, "limit": limit})['result']['albums']
		i = 0
		list = []
		while(i < len(albums)):
			s = albums[i]
			list.append([s['artistName'].encode('ascii', 'ignore'),\
			s['artistID'],\
			s['albumName'].encode('ascii', 'ignore'),\
			s['albumID'],\
			s['image']['medium'].encode('ascii', 'ignore')])
			i = i + 1	
		return list

	def albumGetSongs(self, albumId, limit):
		songs = self.callRemote("album.getSongs", {"albumID": albumId, "limit": limit})['result']['songs']
		i = 0
		list = []
		#return albums
		while(i < len(songs)):
			s = songs[i]
			list.append([s['songName'].encode('ascii', 'ignore'),\
			s['songID'],\
			s['estDurationSecs'],\
			s['albumName'].encode('ascii', 'ignore'),\
			s['albumID'],\
			s['image']['medium'].encode('ascii', 'ignore'),\
			s['artistName'].encode('ascii', 'ignore'),\
			s['artistID']])
			i = i + 1	
		return list

