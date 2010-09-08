
import os
import sys
import xbmcplugin
import xbmc

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
