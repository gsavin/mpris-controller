#!/usr/bin/python
# -*- coding: utf-8 -*-

__docformat__ = 'reStructuredText'

import sys
from mpris import MPRIS, list_available_connection, \
	find_mpris_connection

from gettext import gettext as _

class Action_Play:
	def do(self, mpris):
		status = mpris.player.PlaybackStatus()
		
		if status != "Playing":
			mpris.player.Play()
			return "Play"
	
	def __str__(self):
		return _("if the player is paused, playbacks resumes, if stopped,\
playbacks starts, else nothing happens")

class Action_PlayPause:
	def do(self, mpris):
		mpris.player.PlayPause()
		return mpris.player.PlaybackStatus()
	
	def __str__(self):
		return ""

class Action_Pause:
	def do(self, mpris):
		status = mpris.player.PlaybackStatus()
		
		if status == "Playing":
			mpris.player.Pause()
			return "Pause"
	
	def __str__(self):
		return ""

class Action_Stop:
	def do(self, mpris):
		status = mpris.player.PlaybackStatus()
		
		if status != "Stopped":
			mpris.player.Stop()
			return "Stop"
	
	def __str__(self):
		return ""

class Action_Next:
	def do(self, mpris):
		mpris.player.Next()
		return "Next song"
	
	def __str__(self):
		return ""

class Action_Previous:
	def do(self, mpris):
		mpris.player.Previous()
		return "Previous song"
	
	def __str__(self):
		return ""

class Action_IsPlaying:
	def do(self, mpris):
		status = mpris.player.PlaybackStatus()
		
		if status == 'Playing':
			exit(0)
		else:
			exit(1)
	
	def __str__(self):
		return ""

class Action_GetCurrentTrack:
	def do(self, mpris):
		print "\"%s\" on \"%s\" by %s" % (mpris.metadata.title(), \
			mpris.metadata.album(), mpris.metadata.artist())
	
	def __str__(self):
		return ""

ACTIONS = { \
	"play"				: Action_Play(), 			\
	"pause" 			: Action_Pause(), 			\
	"play_pause"		: Action_PlayPause(), 		\
	"stop"				: Action_Stop(), 			\
	"next"				: Action_Next(), 			\
	"previous"			: Action_Previous(), 		\
	"is_playing"		: Action_IsPlaying(), 		\
	"get_current_track"	: Action_GetCurrentTrack() 	\
}

def usage():
	print "Usage:", sys.argv[0], "action", "[args]"
	print ""
	print "where action is :"
	for k in ACTIONS:
		print "  -", k, ":", str(ACTIONS[k])

if len(sys.argv) < 2:
	usage()
	print ""
	list_available_connection()
	exit(1)
else:
	conn = None
	
	if conn is None:
	#
	# No connection specified in parameters.
	# Try to found one.
	#
		connections = find_mpris_connection()
	
		if len(connections) == 0:
			print "No MPRIS connection found."
			exit(1)
		elif len(connections) > 1:
			print "Multiple MPRIS connections found."
			list_available_connection()
			exit(1)
		
		conn = connections.keys()[0]
	
	action = sys.argv[1]
	args = sys.argv[2:]
	
	mpris = MPRIS(conn)
	
	action = action.lower()
	msg = None
	
	if action in ACTIONS:
		msg = ACTIONS[action].do(mpris)
	else:
		print "unknown command"
	
	if msg is not None:
		mpris.notify(msg)

