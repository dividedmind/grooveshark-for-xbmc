import xbmc, xbmcgui
import sys
import pickle
import os
import traceback
sys.path.append(os.path.join(os.getcwd().replace(";",""),'resources/lib'))

from GrooveAPI import *
from GroovePlayer import GroovePlayer
from GrooveGUI import *
from operator import itemgetter, attrgetter

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
		try:
			if self.initialized == True:
				self.stateList = GrooveClass.STATE_LIST_PLAYLIST
				self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
		except:
			self.initVars()
			try:
				self.gs = GrooveAPI(enableDebug = self.settings[4])
			except:
				self.message('Unable to get a new session ID. Wait a few minutes and try again', 'Error')
				xbmc.log('GrooveShark Exception (onInit): ' + str(sys.exc_info()[0]))
				traceback.print_exc()
				self.close()
			self.initialized = True
			self.showPlayButton()
			self.initPlayer()
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
		self.listPos = [0]
		for i in range(GrooveClass.STATE_LIST_PLAYLIST-1):
			self.listPos.append(0)
		self.settings = self.getSavedSettings()
		
		
	def onFocus(self, controlID):
		pass

	def onAction(self, action):
		aId = action.getId()
		if aId == 10:
			self.close()
		elif aId == 14: # Skip
			self.playNextSong()
		elif aId == 15: # Replay
			self.playPrevSong()
		else:
			pass
 
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
			self.playlistHasFocus()
		elif control == 1003:
			self.showPlaylists()
		elif control == 1004:
			self.getPopular()
			self.stateList = GrooveClass.STATE_LIST_SEARCH
			self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums)
		elif control == 1005:
			self.showSettings()
		elif control == 2001: #Prev
			self.playPrevSong()
		elif control == 2002: #Stop
			self.playStop()
		elif control == 2003: #Play
			self.playPause()
		elif control == 2004: #Next
			self.playNextSong()
		elif control == 2005: #Pause
			self.playSong()
		elif control == 50:
			n = self.getCurrentListPosition()
			item = self.getListItem(n)
			if self.stateList == GrooveClass.STATE_LIST_EMPTY:
				pass
			elif self.stateList == GrooveClass.STATE_LIST_PLAYLIST:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_SEARCH)
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums, self.listPos[self.stateList])	
				else:
					self.showOptionsPlaylist()
					pass
			elif self.stateList == GrooveClass.STATE_LIST_SEARCH:
				if n == 0:
					self.setStateListDown(GrooveClass.STATE_LIST_SONGS)
					self.listSongs(self.searchResultSongs, 'Songs found when searching for "' + self.searchText + '"')
				elif n == 1:
					self.setStateListDown(GrooveClass.STATE_LIST_ARTISTS)
					self.listArtists(self.searchResultArtists, 'Artists found when searching for "' + self.searchText + '"')
				elif n == 2:
					self.setStateListDown(GrooveClass.STATE_LIST_ALBUMS)
					self.listAlbums(self.searchResultAlbums, 'Albums found when searching for "' + self.searchText + '"', withArtist=1)
				else:
					pass
			elif self.stateList == GrooveClass.STATE_LIST_SONGS:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_SEARCH)
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums, self.listPos[self.stateList])
				else:
					self.showOptionsSearch(self.searchResultSongs)
			elif self.stateList == GrooveClass.STATE_LIST_ARTISTS:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_SEARCH)
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums, self.listPos[self.stateList])
				else:
					if self.settings[2] == True: # Get verified albums. Disabled in API so skip it for now
						#self.albums = self.gs.artistGetVerifiedAlbums(self.searchResultArtists[n-1][1],GrooveClass.SEARCH_LIMIT)
						self.albums = self.gs.artistGetAlbums(self.searchResultArtists[n-1][1],GrooveClass.SEARCH_LIMIT)
					else: # Get all albums
						self.albums = self.gs.artistGetAlbums(self.searchResultArtists[n-1][1],GrooveClass.SEARCH_LIMIT)
					self.setStateListDown(GrooveClass.STATE_LIST_ALBUMS_BY_ARTIST)
					self.listAlbums(self.albums, 'Albums by "' + self.searchResultArtists[n-1][0] + '"')
			elif self.stateList == GrooveClass.STATE_LIST_ALBUMS:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_SEARCH)
					self.listSearchResults(self.searchResultSongs, self.searchResultArtists, self.searchResultAlbums, self.listPos[self.stateList])
				else:
					self.setStateListDown(GrooveClass.STATE_LIST_SONGS_ON_ALBUM_FROM_SEARCH)
					self.songs = self.gs.albumGetSongs(self.searchResultAlbums[n-1][3],GrooveClass.SEARCH_LIMIT)
					self.listSongs(self.songs, self.searchResultAlbums[n-1][2] + ' by ' + self.searchResultAlbums[n-1][0])
			elif self.stateList == GrooveClass.STATE_LIST_SONGS_ON_ALBUM_FROM_SEARCH:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_ALBUMS)
					self.listAlbums(self.searchResultAlbums, 'Albums found when searching for "' + self.searchText + '"', withArtist=1, p=self.listPos[self.stateList])
				else:
					self.showOptionsSearch(self.songs)
			elif self.stateList == GrooveClass.STATE_LIST_ALBUMS_BY_ARTIST:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_ARTISTS)
					self.listArtists(self.searchResultArtists, 'Artists found when searching for "' + self.searchText + '"', self.listPos[self.stateList])
				else:
					self.setStateListDown(GrooveClass.STATE_LIST_SONGS_ON_ALBUM)
					self.songs = self.gs.albumGetSongs(self.albums[n-1][3],GrooveClass.SEARCH_LIMIT)
					self.listSongs(self.songs, self.albums[n-1][2] + ' by ' + self.albums[n-1][0])
			elif self.stateList == GrooveClass.STATE_LIST_SONGS_ON_ALBUM:
				if n == 0:
					self.setStateListUp(GrooveClass.STATE_LIST_ALBUMS_BY_ARTIST)
					self.listAlbums(self.albums, 'Albums by "' + self.albums[0][0] + '"', p=self.listPos[self.stateList])
				else:
					self.showOptionsSearch(self.songs)
		else:
			pass
			
	def setStateListDown(self, state):
		self.listPos[self.stateList] = self.getCurrentListPosition()
		self.stateList = state

	def setStateListUp(self, state):
		self.stateList = state

	def showOptionsSearch(self, songs):
		items = ['Queue','Play','Queue all','Add to playlist']
		result = gSimplePopup(title='', items=items, width=300)
		if result == 0:
			n = self.getCurrentListPosition()
			self.playlist.append(songs[n-1])
		elif result == 1:
			n = self.getCurrentListPosition()
			self.playSong(songs[n-1])
		elif result == 2:
			l = len(songs)
			for n in range(0, l):
				self.playlist.append(songs[n])
		elif result == 3:
			items = []
			playlists = self.gs.userGetPlaylists()
			i = 0
			while (i < len(playlists)):
				items.append(playlists[i][0])
				i += 1
			result = gShowPlaylists(playlists=items,options=[])
			if result != -1:
				pId = playlists[result][1]
				n = self.getCurrentListPosition()
				songId = songs[n-1][1]
				self.gs.playlistAddSong(pId, songId, 0)
		else:
			pass

	def showOptionsPlaylist(self):
		items = ['Play','Remove Song','Save Playlist','Save Playlist As','Close Playlist']
		result = gSimplePopup(title='', items=items, width=300)
		if result == 0:
			self.nowPlaying = self.getCurrentListPosition()-1
			self.playSong(self.playlist[self.nowPlaying])
		elif result == 1:
			self.removeSongFromList(self.playlist)
			self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
		elif result == 2: # Save
			if self.playlistId != 0:
				if self.savePlaylist(self.playlistId, self.playlistName) == 0:
					self.message('Could not save the playlist')
			else:
				self.message('Unsaved playlist. Use \'Save Playlist As\' instead','Problem saving')
		elif result == 3: # Save As
			name = self.getInput('Type a name for the playlist')
			if name != '':
				pId = self.savePlaylist(0, name, '')
				if pId == 0:
					self.message('Could not save the playlist', 'Sorry')
				else:
					self.playlistId = pId
					self.playlistName = name
					self.setStateLabel('Current Playlist (' + self.playlistName + ')')
			else:
				self.message('You have to type a name for the playlist', 'Error')
		elif result == 4: #Close playlist
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
	
	def setPlayerLabel(self, msg):
		self.getControl(3001).reset(msg)
		self.getControl(3001).addLabel(msg)

	def message(self, message, title = ''):
		dialog = xbmcgui.Dialog()
		dialog.ok(title, message)
	
	def setStateLabel(self, msg):
		self.getControl(3000).setLabel(msg)

	def playlistHasFocus(self):
		self.setFocus(self.getControl(205))

	def getPopular(self):
		self.searchText = 'Popular'
		dialog = xbmcgui.DialogProgress()
		dialog.create('Please wait', 'Getting popular songs...')
		dialog.update(0)
		try:
			self.searchResultSongs = self.gs.popularGetSongs(GrooveClass.SEARCH_LIMIT)
			dialog.update(33, 'Getting popular artists...')
			self.searchResultArtists = self.gs.popularGetArtists(GrooveClass.SEARCH_LIMIT)
			dialog.update(66, 'Getting popular albums...')
			self.searchResultAlbums = self.gs.popularGetAlbums(GrooveClass.SEARCH_LIMIT)
			dialog.update(100, 'Done')
			dialog.close()
			self.playlistHasFocus()
		except:
			dialog.close()
			self.message('Could not get popular items','Sorry')
			traceback.print_exc()
	
	def searchAll(self, text):
		self.searchText = text
		dialog = xbmcgui.DialogProgress()
		dialog.create('Please wait', 'Searching for songs...')
		dialog.update(0)
		try:
			self.searchResultSongs = self.gs.searchSongs(text, GrooveClass.SEARCH_LIMIT)
			dialog.update(33, 'Searching for artists...')
			self.searchResultArtists = self.gs.searchArtists(text, GrooveClass.SEARCH_LIMIT)
			dialog.update(66, 'Searching for albums...')
			self.searchResultAlbums = self.gs.searchAlbums(text, GrooveClass.SEARCH_LIMIT)
			dialog.update(100, 'Search complete')
			dialog.close()
			self.playlistHasFocus()
		except:
			dialog.close()
			self.message('Search failed. Try again')
			traceback.print_exc()
	
	def listSearchResults(self, songs, artists, albums, p=0):
		xbmcgui.lock()
		self.clearList()
		self.setStateLabel('Search results for "' + self.searchText + '"')
		item = xbmcgui.ListItem (label='Songs', label2=str(len(songs)))			
		self.addItem(item)
		item = xbmcgui.ListItem (label='Artists', label2=str(len(artists)))			
		self.addItem(item)
		item = xbmcgui.ListItem (label='Albums', label2=str(len(albums)))			
		self.addItem(item)
		self.setCurrentListPosition(p)
		xbmcgui.unlock()

	def listSongs(self, songs, text='',p=0):
		try:
			xbmcgui.lock()
			i = 0
			self.clearList()
			self.addItem('..')
			self.setStateLabel(text)
			while(i < len(songs)):
				if songs[i][2] == -1:
					durStr = ''
				else:
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
			self.setCurrentListPosition(p)
			xbmcgui.unlock()
		except:
			xbmcgui.unlock()
			xbmc.log('GrooveShark Exception (listSongs): ' + str(sys.exc_info()[0]))
			traceback.print_exc()

	def listArtists(self, artists, text='',p=0):
		xbmcgui.lock()
		i = 0
		self.clearList()
		self.addItem('..')
		self.setStateLabel(text)
		while(i < len(artists)):
			item = xbmcgui.ListItem (label=artists[i][0])			
			self.addItem(item)
			i += 1
		self.setCurrentListPosition(p)
		xbmcgui.unlock()
		
	def listAlbums(self, albums, text='', withArtist=0, p=0):
		xbmcgui.lock()
		i = 0
		self.clearList()
		self.addItem('..')
		self.setStateLabel(text)
		while(i < len(albums)):
			if withArtist == 0:
				item = xbmcgui.ListItem (label=albums[i][2])
			else:
				item = xbmcgui.ListItem (label='"' + albums[i][2] + '" by ' + albums[i][0])
			self.addItem(item)
			i += 1
		self.setCurrentListPosition(p)
		xbmcgui.unlock()

	def playerChanged(self, event):
		if event == 0: # Stopped
			self.showPlayButton()
			
		elif event == 1: # Ended
			self.playNextSong()		
			
		elif event == 2: # Started
			pass
			
		elif event == 3: # Playback paused
			self.showPlayButton()
			
		elif event == 4: # Playback resumed
			self.showPauseButton()

		elif event == 5: # Play next
			pass
			
	def showPlayButton(self):
		playBtn = self.getControl(2003)
		pauseBtn = self.getControl(2005)
		stopBtn = self.getControl(2002)
		nextBtn = self.getControl(2004)
		pauseBtn.setVisible(False) # Pause button
		playBtn.setVisible(True) # Play button
		playBtn.controlLeft(stopBtn)
		playBtn.controlRight(nextBtn)
		stopBtn.controlRight(playBtn)
		nextBtn.controlLeft(playBtn)

	def showPauseButton(self):
		playBtn = self.getControl(2003)
		pauseBtn = self.getControl(2005)
		stopBtn = self.getControl(2002)
		nextBtn = self.getControl(2004)
		playBtn.setVisible(False) # Play button
		pauseBtn.setVisible(True) # Pause button
		pauseBtn.controlLeft(stopBtn)
		pauseBtn.controlRight(nextBtn)
		stopBtn.controlRight(pauseBtn)
		nextBtn.controlLeft(pauseBtn)
		pauseBtn.setVisible(True) # Pause button

	def playSong(self, song):
		# Missing some sort of fallback mechanism if playback fails. 'playbackStarted' from callback func. from player might come in handy for this
		songId = song[1]
		title = song[0]
		artist = song[6]
		listItem = xbmcgui.ListItem('some music')
		listItem.setInfo( type = 'music', infoLabels = {'title': title, 'artist': title})
		try:
			url = self.gs.getStreamURL(str(songId))
			if url != "":
				self.setPlayerLabel('Buffering...')
				self.player.play(str(url), listItem)
				self.setPlayerLabel('Now Playing: ' + artist + ' - ' + title)
				self.showPauseButton()
				return 1
			else:
				return 0
		except:
			xbmc.log('GrooveShark Exception (playSong): ' + str(sys.exc_info()[0]))
			traceback.print_exc()
			self.setPlayerLabel('Playback failed')
			self.showPlayButton()
			return 0
			
	def playNextSong(self):
		# Try to play the next song on the current playlist
		if self.nowPlaying != -1:
			n = len(self.playlist)-1
			if n > 0:
				if (self.nowPlaying + 1) > n:
					self.nowPlaying = 0
				else:
					self.nowPlaying += 1
				self.playSong(self.playlist[self.nowPlaying])
			else:
				pass
		else:
			self.setPlayerLabel('')

	def playPrevSong(self):
		# Try to play the previous song on the current playlist
		if self.nowPlaying != -1:
			n = len(self.playlist)
			if n > 0:
				if (self.nowPlaying - 1) < 0:
					self.nowPlaying = n-1 #Wrap around
				else:
					self.nowPlaying -= 1
				self.playSong(self.playlist[self.nowPlaying])
			else:
				pass
		else:
			self.setPlayerLabel('')

	def playStop(self):
		# Stop playback
		if self.player.isPlayingAudio():
			self.player.stop()
			self.setPlayerLabel('')
		self.showPlayButton()
					
	def playPause(self):
		if self.player.isPlayingAudio():
			self.player.pause()
			self.showPlayButton()
		else:
			self.player.play()
			self.showPauseButton()
						
	def getInput(self, title, default="", hidden=False):
		ret = ""
	
		keyboard = xbmc.Keyboard(default, title)
		keyboard.setHiddenInput(hidden)
		keyboard.doModal()

		if keyboard.isConfirmed():
			ret = keyboard.getText()

		return ret
	def loginBasic(self):
		self.login(1)

	def login(self, basic = 0):
		#return 0
		if self.gs.loggedInStatus() == 1:
			self.gs.logout()
		if ((str(self.settings[0]) != "") and (str(self.settings[1]) != "")):
			pDialog = xbmcgui.DialogProgress()
			pDialog.update(0)
			pDialog.create('Logging in', 'Please wait...')
			try:
				if basic == 1:
					self.userId = self.gs.loginBasic(str(self.settings[0]), str(self.settings[1]))
				else:
					self.userId = self.gs.login(str(self.settings[0]), str(self.settings[1]))

				if self.userId != 0:
					pDialog.update(0, 'Success')
					xbmc.sleep(500)
					pDialog.close()
				else:
					pDialog.close()
					self.message('Failed to login. Check your login details in settings')

			except LoginTokensExceededError:
				pDialog.close()
				dialog = xbmcgui.Dialog()
				result = dialog.yesno('Failed to login', 'Exceeded number of allowed authentication tokens.','Try plain text authentication?')
				if result == True:
					self.loginBasic()
				else:
					pass
			except:
				pDialog.close()
				self.message('Failed to login. Check your login details in settings')
				
		else:
			print 'No login details provided in settings'

	def showPlaylists(self):
		if self.gs.loggedInStatus() != 1:
			self.message('You have to be logged in. Set your login in settings','Unable to get playlists')
			return None
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
			result = gShowPlaylists(playlists=items,options=['Load','Rename','Delete']) #xbmcgui.Dialog().select("Playlists", items)
			action = result[0]
			n = result[1]
			if action == 0: #Load
				self.playlistId = playlists[n][1]
				self.playlistName = playlists[n][0]
				self.playlist = self.gs.playlistGetSongs(self.playlistId)
				self.listSongs(self.playlist, 'Current Playlist (' + self.playlistName + ')')
				self.stateList = GrooveClass.STATE_LIST_PLAYLIST
			elif action == 1: #Rename
				name = self.getInput('New name for playlist', default=playlists[n][0])
				if name != '':
					if self.gs.playlistRename(playlists[n][1], name) == 0:
						self.message('Could not rename playlist')
				self.showPlaylists()
			elif action == 2: #Delete
				dialog = xbmcgui.Dialog()
				result = dialog.yesno('Delete playlist', 'Are you sure you want to delete the playlist:',playlists[n][0])
				if result == True:
					self.gs.playlistDelete(playlists[n][1])
				else:
					pass
				self.showPlaylists()
			
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
		pDialog = xbmcgui.DialogProgress()
		pDialog.update(0)
		pDialog.create('Saving playlist', 'Please wait...')
		if playlistId == 0:
			if name != '':
				pId = self.gs.playlistCreate(name, about)
				if pId == 0:
					return 0
		else:
			pId = playlistId
		
		i = 0
		n = len(self.playlist)
		songIds = []
		while i < n:
			songIds.append(self.getSongIdFromList(self.playlist, i))
			i += 1
		if self.gs.playlistReplace(pId, songIds) == 0:
			pDialog.update(0, 'Could not save playlist')
			xbmc.sleep(1000)
			pDialog.close()
		else:
			pDialog.update(0, 'Playlist saved')
			xbmc.sleep(1000)
			pDialog.close()
		return pId

	def getSavedSettings(self):
		settings = []
		path = os.path.join(self.rootDir, 'data', 'settings.txt')

		try:
			f = open(path, 'rb')
			settings = pickle.load(f)
			f.close()
		except:
			# [user, pass, get verified albums, exact match for songs, debug]
			settings = ["","", False, False, False]
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
		popup = settingsUI(settings=self.getSavedSettings())
		popup .doModal()
		if popup.settingsSaved() == True:
			self.settings = popup.getSettings()
			self.saveSettings()
			self.login()
		del popup

			
rootDir = os.getcwd()
w = GrooveClass("grooveshark.xml", rootDir, "DefaultSkin")
w.doModal()
del w
