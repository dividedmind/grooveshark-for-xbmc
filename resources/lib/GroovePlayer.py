import sys
import os
import xbmc
import xbmcgui

class GroovePlayer(xbmc.Player):
	def __init__(self, *args, **kwargs):
		self.function = self.dummyFunc

	def onPlayBackStopped(self):
		xbmc.sleep(300)
		self.function(0)

	def onPlayBackEnded(self):
		xbmc.sleep(300)
		self.function(1)

	def onPlayBackStarted(self):
		self.function(2)
		
	def playnext(self):
		xbmc.sleep(300)
		self.function(3)
		
	def setCallBackFunc(self, func):
		self.function = func
		
	def dummyFunc(self, event):
		pass
