
import os
import sys
import xbmcplugin
import xbmc

try:
	# new XBMC 10.05 addons:
	import xbmcaddon
except ImportError:
	# old XBMC - create fake xbmcaddon module with same interface as new XBMC 10.05
	class xbmcaddon:
		""" fake xbmcaddon module """
		__version__ = "(old XBMC)"
		class Addon:
			""" fake xbmcaddon.Addon class """
			def __init__(self, id):
				self.id = id

			def getSetting(self, key):
				return xbmcplugin.getSetting(key)

			def setSetting(self, key, value):
				xbmcplugin.setSetting(key, value)

			def openSettings(self, key, value):
				xbmc.openSettings()

			def getLocalizedString(self, id):
				return xbmc.getLocalizedString(id)

__scriptname__ = "GrooveShark"
__scriptid__ = "script.audio.grooveshark"
__author__ = "Solver"
__url__ = "http://code.google.com/p/grooveshark-for-xbmc/"
__svn_url__ = ""
__credits__ = ""
__version__ = "0.2.5"
__XBMC_Revision__ = "22240"


BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )

sys.path.append (BASE_RESOURCE_PATH)

__settings__ = xbmc.Settings(path=os.getcwd())

__language__ = xbmc.Language(os.getcwd().replace( ";", "" )).getLocalizedString

__debugging__ = __settings__.getSetting("debug")

__isXbox__ = True

if __name__ == "__main__":
	from GrooveShark import *
	w = GrooveClass("grooveshark.xml", os.getcwd(), "DefaultSkin", isXbox = True)
	w.doModal()
	del w
	sys.modules.clear()            
