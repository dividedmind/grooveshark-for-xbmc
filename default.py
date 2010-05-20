import xbmc, xbmcgui
import sys
import pickle
import os
import traceback
sys.path.append(os.path.join(os.getcwd().replace(";",""),'resources/lib'))

from GrooveAPI import GrooveAPI
from GroovePlayer import GroovePlayer

ACTION_PREVIOUS_MENU = 10

class GrooveClass(xbmcgui.WindowXML):

	STATE_LIST_EMPTY = 0
	STATE_LIST_SEARCH = 1
	STATE_LIST_SONGS = 2
	STATE_LIST_ARTISTS = 3
	STATE_LIST_ALBUMS = 4
	STATE_LIST_ALBUMS_BY_ARTIST = 5
	STATE_LIST_SONGS_ON_ALBUM = 6
	STATE_LIST_SONGS_ON_ALBUM_FROM_SEARCH = 7
	STATE_LIST_PLAYLIST = 8

	SEARCH_LIMIT = 100

	def onInit(self):
		self.initPlayer()
		self.initVars()
		self.login()

	def initPlayer(self):
		try:
			self.player = GroovePlayer(xbmc.PLAYER_CORE_MPLAYER)
			self.player.setCallBackFunc(self.playerChanged)
		except:
			xbmc.log('GrooveShark Exception (initPlayer): ' + str(sys.exc_info()[0]))
			traceback.print_exc()
			

	def initVars(self):
		self.setStateLabel('Start searching for songs or load a playlist')
		self.stateList = GrooveClass.STATE_LIST_EMPTY
		self.searchResultSongs = []
		self.searchResultAlbums = []
		self.searchResultArtists = []
		self.songs = []
		self.artists = []
		self.albums = []
		self.playlist = []
		self.playlistId = 0
		self.playlistName = 'Unsaved'
		self.searchText = ""
		self.settings = []
		self.rootDir = os.getcwd()
		self.nowPlaying = -1
		self.settings = self.getSavedSettings()
		self.gs = GrooveAPI()
		
	def onFocus(self, controlID):
		pass

	def onAction(self, action):
		if action.getId() == 10:
			self.close()
 
	def onClick(self, control):
		# The state machine should be rewritten at some point
		if control == 1002:
			text = self.getInput("Enter a search phrase:", "")
			if text != "":
				self.searchAll(text)
				self.stateList = GrooveClass.STATE_LIST_SEARCH
				self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums)
		elif control == 1001:
			self.stateList = GrooveClass.STATE_LIST_PLAYLIST
			self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
		elif control == 1003:
			self.showPlaylists()
		elif control == 1004:
			self.showSettings()
		elif control == 50:
			n = self.getCurrentListPosition()
			item = self.getListItem(n)
			if self.stateList == GrooveClass.STATE_LIST_EMPTY:
				pass
			elif self.stateList == GrooveClass.STATE_LIST_PLAYLIST:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_SEARCH
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums)	
				else:
					self.showOptionsPlaylist()
					pass
			elif self.stateList == GrooveClass.STATE_LIST_SEARCH:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_SONGS
					self.listSongs(self.searchResultSongs, 'Songs found when searching for "' + self.searchText + '"')
				elif n == 1:
					self.stateList = GrooveClass.STATE_LIST_ARTISTS
					self.listArtists(self.searchResultArtists, 'Artists found when searching for "' + self.searchText + '"')
				elif n == 2:
					self.stateList = GrooveClass.STATE_LIST_ALBUMS
					self.listAlbums(self.searchResultAlbums, 'Albums found when searching for "' + self.searchText + '"')
				else:
					pass
			elif self.stateList == GrooveClass.STATE_LIST_SONGS:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_SEARCH
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums)
				else:
					self.showOptionsSearch(self.searchResultSongs)
			elif self.stateList == GrooveClass.STATE_LIST_ARTISTS:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_SEARCH
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums)
				else:
					self.stateList = GrooveClass.STATE_LIST_ALBUMS_BY_ARTIST
					self.albums = self.gs.artistGetAlbums(self.searchResultArtists[n-1][1],GrooveClass.SEARCH_LIMIT)
					self.listAlbums(self.albums, 'Albums by "' + self.searchResultArtists[n-1][0] + '"', 1)
			elif self.stateList == GrooveClass.STATE_LIST_ALBUMS:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_SEARCH
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums)
				else:
					self.stateList = GrooveClass.STATE_LIST_SONGS_ON_ALBUM_FROM_SEARCH
					self.songs = self.gs.albumGetSongs(self.searchResultAlbums[n-1][3],GrooveClass.SEARCH_LIMIT)
					self.listSongs(self.songs, self.searchResultAlbums[n-1][2] + ' by ' + self.searchResultAlbums[n-1][0])
			elif self.stateList == GrooveClass.STATE_LIST_SONGS_ON_ALBUM_FROM_SEARCH:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_ALBUMS
					self.listAlbums(self.searchResultAlbums, 'Albums found when searching for "' + self.searchText + '"')
				else:
					self.showOptionsSearch(self.songs)
			elif self.stateList == GrooveClass.STATE_LIST_ALBUMS_BY_ARTIST:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_ARTISTS
					self.listArtists(self.searchResultArtists, 'Artists found when searching for "' + self.searchText + '"')
				else:
					self.stateList = GrooveClass.STATE_LIST_SONGS_ON_ALBUM
					self.songs = self.gs.albumGetSongs(self.albums[n-1][3],GrooveClass.SEARCH_LIMIT)
					self.listSongs(self.songs, self.albums[n-1][2] + ' by ' + self.albums[n-1][0])
			elif self.stateList == GrooveClass.STATE_LIST_SONGS_ON_ALBUM:
				if n == 0:
					self.stateList = GrooveClass.STATE_LIST_ALBUMS_BY_ARTIST
					self.listAlbums(self.albums, 'Albums by "' + self.albums[0][0] + '"', 1)
				else:
					self.showOptionsSearch(self.songs)
		else:
			pass

	def showOptionsSearch(self, songs):
		items = ['Queue','Play','Queue all','Back']
		result = xbmcgui.Dialog().select("Do what?", items)
		if result == 0:
			n = self.getCurrentListPosition()
			self.playlist.append(songs[n-1])
		elif result == 1:
			songId = self.getSongIdFromList(self.songs)
			listItem = self.getSongInfoFromListAsListItem(self.songs)
			self.playSong(songId, listItem)
		elif result == 2:
			l = len(songs)
			for n in range(0, l):
				self.playlist.append(songs[n])
		elif result == 3:
			pass
		else:
			pass

	def showOptionsPlaylist(self):
		items = ['Play','Remove Song','Save Playlist','Save Playlist As','Close Playlist', 'Delete Playlist']
		result = xbmcgui.Dialog().select("Do what?", items)
		if result == 0:
			songId = self.getSongIdFromList(self.playlist)
			listItem = self.getSongInfoFromListAsListItem(self.playlist)
			self.nowPlaying = self.getCurrentListPosition()
			self.playSong(songId, listItem)
		elif result == 1:
			self.removeSongFromList(self.playlist)
			self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
		elif result == 2:
			if self.savePlaylist(self.playlistId, self.playlistName) == 0:
					self.message('Could not save the playlist')
		elif result == 3:
			name = self.getInput('Type a name for the playlist')
			if name != '':
				pId = self.savePlaylist(0, name, '')
				if pId == 0:
					self.message('Could not save the playlist')
				else:
					self.playlistId = pId
					self.playlistName = name
					self.setStateLabel('Current Playlist (' + self.playlistName + ')')
			else:
				self.message('You have to type a name for the playlist')
		elif result == 4:
			self.closePlaylist()
		elif result == 5:
			if self.playlistId != -1:
				self.gs.playlistDelete(self.playlistId)
				self.closePlaylist()
		else:
			pass

	def removeSongFromList(self, sList, n = -1):
		if n == -1:
			nn = self.getCurrentListPosition()-1
		else:
			nn = n
		sList.pop(nn)

	def getSongIdFromList(self, songs, n = -1):
		if n == -1:
			nn = self.getCurrentListPosition()
		else:
			nn = n
		return songs[nn-1][1]

	def getSongInfoFromListAsListItem(self, songs, n = -1):
		if n == -1:
			nn = self.getCurrentListPosition()
		else:
			nn = n
		listItem = xbmcgui.ListItem('some music')
		listItem.setInfo( type = 'music', infoLabels = { 'title': songs[nn-1][0], 'artist': songs[nn-1][6] } )
		return listItem

	def playSong(self, songId, listItem):
		# Missing some sort of fallback mechanism if playback fails. 'playbackStarted' from callback func. from player might come in handy for this
		try:
			url = self.gs.getStreamURL(str(songId))
			if url != "":
				self.player.play(str(url), listItem)
				return 1
			else:
				return 0
		except:
			xbmc.log('GrooveShark Exception (playSong): ' + str(sys.exc_info()[0]))
			traceback.print_exc()
			return 0

	def message(self, message, title = ''):
		dialog = xbmcgui.Dialog()
		dialog.ok(title, message)
	
	def setStateLabel(self, msg):
		self.getControl(3000).setLabel(msg)
	
	def searchAll(self, text):
		self.searchText = text
		dialog = xbmcgui.DialogProgress()
		dialog.create('Please wait', 'Searching for songs...')
		dialog.update(1)
		try:
			self.searchResultSongs = self.gs.searchSongs(text, GrooveClass.SEARCH_LIMIT)
			dialog.update(33, 'Searching for artists...')
			self.searchResultArtists = self.gs.searchArtists(text, GrooveClass.SEARCH_LIMIT)
			dialog.update(66, 'Searching for albums...')
			self.searchResultAlbums = self.gs.searchAlbums(text, GrooveClass.SEARCH_LIMIT)
			dialog.update(100, 'Search complete')
			dialog.close()
			self.setFocus(self.getControl(50))
		except:
			dialog.close()
			self.message('Search failed. Try again')
	
	def listSearchResults(self, songs, artists, albums={}):
		self.clearList()
		self.setStateLabel('Search results for "' + self.searchText + '"')
		item = xbmcgui.ListItem (label='Songs', label2=str(len(songs)))			
		self.addItem(item)
		item = xbmcgui.ListItem (label='Artists', label2=str(len(artists)))			
		self.addItem(item)
		item = xbmcgui.ListItem (label='Albums', label2=str(len(albums)))			
		self.addItem(item)

	def listSongs(self, songs, text=''):
		i = 0
		self.clearList()
		self.addItem('..')
		self.setStateLabel(text)
		while(i < len(songs)):
			durMin = int(songs[i][2]/60.0)
			durSec = int(songs[i][2] - durMin*60)
			if durSec < 10:
				durStr = '(' + str(durMin) + ':0' + str(durSec) + ')'
			else:
				durStr = '(' + str(durMin) + ':' + str(durSec) + ')'
			songId = str(songs[i][1])
			item = xbmcgui.ListItem (label=songs[i][6] + ' - "' + songs[i][0] + '" (' + songs[i][3] + ')',label2=durStr)			
			self.addItem(item)
			i += 1

	def listArtists(self, artists, text=''):
		i = 0
		self.clearList()
		self.addItem('..')
		self.setStateLabel(text)
		while(i < len(artists)):
			item = xbmcgui.ListItem (label=artists[i][0])			
			self.addItem(item)
			i += 1

	def listAlbums(self, albums, text='', withArtist=0):
		i = 0
		self.clearList()
		self.addItem('..')
		self.setStateLabel(text)
		while(i < len(albums)):
			if withArtist == 0:
				item = xbmcgui.ListItem (label=albums[i][2])
			else:
				item = xbmcgui.ListItem (label=albums[i][0] + ' - ' + albums[i][2])
			self.addItem(item)
			i += 1

	def playerChanged(self, event):
		if event == 0: # Stopped
			pass
			
		elif event == 1: # Ended
			self.playNextSong()		
			
		elif event == 2: # Started
			pass
			
		elif event == 3: # Play next
			# Doesn't work. Perhaps because the player checks the playlist which is empty ande therefore never calls playnext()
			self.playNextSong()
			
	def playNextSong(self):
			# Try to play the next song on the current playlist
			if self.nowPlaying != -1:
				n = len(self.playlist)
				if n > 0:
					if (self.nowPlaying + 1) <= n:
						self.nowPlaying += 1
					else:
						self.nowPlaying = 0
					songId = self.getSongIdFromList(self.playlist, self.nowPlaying)
					listItem = self.getSongInfoFromListAsListItem(self.playlist, self.nowPlaying)
					self.playSong(songId, listItem)
				else:
					pass
			else:
				pass

	def getInput(self, title, default="", hidden=False):
		ret = ""
	
		keyboard = xbmc.Keyboard(default, title)
		keyboard.setHiddenInput(hidden)
		keyboard.doModal()

		if keyboard.isConfirmed():
			ret = keyboard.getText()

		return ret

	def login(self):
		if ((str(self.settings[0]) != "") and (str(self.settings[1]) != "")):
			dialog = xbmcgui.DialogProgress()
			dialog.update(0)
			dialog.create('Logging in', '')
			self.userId = self.gs.login(str(self.settings[0]), str(self.settings[1]))
			if self.userId == 0:
				dialog.close()
				self.message('Failed to login. Check your login details in settings')
			else:
				dialog.close()
		else:
			print 'No login details provided in settings'

	def showPlaylists(self):
		dialog = xbmcgui.DialogProgress()
		dialog.update(0)
		dialog.create('Getting your playlists...', '')		
		try:
			items = []
			playlists = self.gs.userGetPlaylists()
			i = 0
			while (i < len(playlists)):
				items.append(playlists[i][0])
				i += 1
			dialog.close()
			result = xbmcgui.Dialog().select("Playlists", items)
			if result != -1:
				self.playlistId = playlists[result][1]
				self.playlistName = playlists[result][0]
				self.playlist = self.gs.playlistGetSongs(self.playlistId)
				self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
				self.stateList = GrooveClass.STATE_LIST_PLAYLIST
			
		except:
			dialog.close()
			self.message('Could not get your playlists')
			
	def closePlaylist(self):
		self.playlistId = 0
		self.playlistName = 'Unsaved'
		self.playlist = []
		self.nowPlaying = -1
		self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
		self.stateList = GrooveClass.STATE_LIST_PLAYLIST
	
	#FIXME: Would be better to use playlist.replace - current implementation is rather slow and unsafe
	# Could be made safe by creating a duplicate playlist, try to save the playlist and only if everything went according to plan, delete the old playlist
	def savePlaylist(self, playlistId, name = '', about = ''):
		if playlistId == 0:
			if name != '':
				pId = self.gs.playlistCreate(name, about)
				if pId == 0:
					return 0
		else:
			pId = playlistId
			self.gs.playlistClearSongs(pId)
		
		i = 0
		n = len(self.playlist)
		dialog = xbmcgui.DialogProgress()
		dialog.create('Please wait', 'Saving the playlist: ' + name)
		#dialog.update(0)
		try:		
			while i < n:
				songId = self.getSongIdFromList(self.playlist, i)
				if self.gs.playlistAddSong(pId, songId, i) == 0:
					return 0 # Could not save the playlist
				dialog.update((i*100)/n)
				i += 1
			dialog.close()
			return pId
		except:
			dialog.close()
			return 0


	def getSavedSettings(self):
		settings = []
		path = os.path.join(self.rootDir, 'data', 'settings.txt')

		try:
			f = open(path, 'rb')
			settings = pickle.load(f)
			f.close()
		except:
			# [user, pass]
			settings = ["",""]
			# File not found, will be created upon save
			pass		
		
		return settings

	def saveSettings(self):			
		try:
			dir = os.path.join(self.rootDir, 'data')
			# Create the 'data' directory if it doesn't exist.
			if not os.path.exists(dir):
				os.mkdir(dir)
			path = os.path.join(dir, 'settings.txt')
			f = open(path, 'wb')
			pickle.dump(self.settings, f, protocol=pickle.HIGHEST_PROTOCOL)
			f.close()
		except IOError, e:
			print 'There was an error while saving the settings pickle (%s)' % e
			pass
		except:
			print "An unknown error occured during save settings\n"
			pass
	
	def showSettings(self):
		self.settings = self.getSavedSettings()
		if self.settings[0] != "" and self.settings[1] != "":
			loginSettings = 'Login details set (' + self.settings[0] + ')'
		else:
			loginSettings = 'Login details not set'
		
		items = [loginSettings,'Back']
		result = xbmcgui.Dialog().select("Settings", items)
		if result == 0:
			username = self.getInput('Username')
			if username != "":
				password = self.getInput('Password')
				if password != '':
					self.settings[0] = username
					self.settings[1] = password
					self.saveSettings()
					self.login()
		else:
			pass

rootDir = os.getcwd()
w = GrooveClass("grooveshark.xml", rootDir, "DefaultSkin")
w.doModal()
del w
