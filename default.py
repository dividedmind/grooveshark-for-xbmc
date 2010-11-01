import os
import sys
import xbmcplugin
import xbmc
import xbmcgui
import traceback
import threading

sys.path.append(os.path.join(os.getcwd().replace(";",""),'resources','lib'))


class tools(object):
	def __init__(self):
		pass
	def loadParameters(self, params):
		self.cmds = {}
		splitCmds = params[params.find('?')+1:].split('&')    
		for cmd in splitCmds: 
			if (len(cmd) > 0):
				splitCmd = cmd.split('=')
				name = splitCmd[0]
				value = splitCmd[1]
				self.cmds[name] = value

	def getCmd(self, cmd):
		if cmd in self.cmds:
			return self.cmds[cmd]
		else:
			return None

BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )
sys.path.append (BASE_RESOURCE_PATH)

__scriptid__ = "script.audio.grooveshark"
__scriptname__ = "GrooveShark"
__author__ = "Solver"
__url__ = "http://code.google.com/p/grooveshark-for-xbmc/"
__svn_url__ = ""
__credits__ = ""
__version__ = "0.2.9"
__XBMC_Revision__ = "31000"

try: #It's post-dharma
	import xbmcaddon
	__settings__ = xbmcaddon.Addon(id=__scriptid__)
	__language__ = __settings__.getLocalizedString
	__debugging__ = __settings__.getSetting("debug")
	__isXbox__ = False
	print 'GrooveShark: Initialized as a post-dharma plugin'

except: #It's an XBOX/pre-dharma
	__settings__ = xbmc.Settings(path=os.getcwd())
	__language__ = xbmc.Language(os.getcwd().replace( ";", "" )).getLocalizedString
	__debugging__ = __settings__.getSetting("debug")
	__isXbox__ = True
	print 'GrooveShark: Initialized as a XBOX plugin'

if __debugging__ == 'true':
	__debugging__ = True
	print 'GrooveShark: Debugging enabled'
else:
	__debugging__ = False
	print 'GrooveShark: Debugging disabled'

def startGUI():
	print "GrooveShark version " + str(__version__)
	w = GrooveClass("grooveshark.xml", os.getcwd(), "DefaultSkin", isXbox = __isXbox__)
	w.doModal()
	del w
	print 'GrooveShark: Closed'
	sys.modules.clear()

if __isXbox__ == True:
	if __name__ == "__main__":
		from GrooveShark import *
		startGUI()
else: 
	if len(sys.argv) == 3:#Run as a plugin to open datastreams
		from GrooveAPI import *
		import xbmcplugin
		import xbmcgui
		import traceback
		try:
			tools = tools()
			tools.loadParameters(sys.argv[2])
			gs = GrooveAPI()
			get = tools.getCmd
			songId = get('playSong')
			playlist = get('playlist')
			title = get('title')
			album = get('album')
			artist = get('artist')
			cover = 'http://' + get('cover')
			duration = get('duration')
			try:
				duration = int(duration)
			except:
				duration = 0

			if (playlist != None): # To be implemented...
				#listitem=xbmcgui.ListItem('Playlists')#, iconImage=icon, thumbnailImage=thumbnail )
				#listitem.addContextMenuItems( cm, replaceItems=True )
				#listitem.setProperty( "Folder", "true" )
				#xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url='plugin://script.audio.grooveshark/?playSong=409361', listitem=listitem, isFolder=False, totalItems=1)
				#xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True, cacheToDisc=False )
				pass
			
			elif (songId != None):
				print 'GrooveShark: Song ID: ' + str(songId)
				url = gs.getStreamURL(str(songId))
				if url != "":
					#info = gs.songAbout(str(songId))
					listitem=xbmcgui.ListItem(label=title, iconImage=cover, thumbnailImage=cover, path=url);
					listitem.setInfo(type='Music', infoLabels = { 'title': title, 'artist': artist , 'url': url, 'duration': duration})
					listitem.setProperty('mimetype', 'audio/mpeg')
					xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
				else:
					xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=None)
			else:
				xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=None)
				print 'GrooveShark: Unknown command'
		except:
			xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=None)
			traceback.print_exc()
	else:
		if __name__ == "__main__":
			from GrooveShark import *
			startGUI()

