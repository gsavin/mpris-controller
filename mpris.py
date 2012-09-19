# -*- coding: utf-8 -*-

"""
Documentation about MPRIS specifications can be found here :
	http://specifications.freedesktop.org/mpris-spec/latest
	
MPRIS Version 2.2

:Author:
	Guilhelm SAVIN <gsavin@lewub.org>
"""

__all__ = ('MPRIS', 'Root', 'Player', 'Tracklist', 'Playlists')
__docformat__ = 'reStructuredText'

import gobject
gobject.threads_init()

from dbus import glib
glib.init_threads()

import dbus, sys, notify2

def find_mpris_connection():
	"""
	"""
	available = {}
	bus = dbus.SessionBus()
	
	for player in MPRIS.PLAYERS:
		try:
			mpris      = bus.get_object(MPRIS.CONNECTION_PREFIX + player, MPRIS.OBJECT_PATH)
			properties = dbus.Interface(mpris, MPRIS.INTERFACE_PROPERTIES)
			identity   = properties.Get(MPRIS.INTERFACE_ROOT, "Identity")
			
			available[player] = identity.encode('utf-8')
		except:
			pass
		
	return available

def list_available_connection():
	"""
	"""
	available = find_mpris_connection()
	
	if len(available) == 0:
		print "no player is available"
	else:
		print "Available player(s):"
		for player in available:
			print "-", player, ":", available[player]

class MPRIS:
	"""
	Global MPRIS object connected to `Root`, `Player`, `Tracklist` and
	`Playlists` dbus objects.
	"""
	
	PLAYERS				 = ('audacious', 'vlc', 'bmp', 'xmms2')
	CONNECTION_PREFIX    = "org.mpris.MediaPlayer2."
	OBJECT_PATH          = "/org/mpris/MediaPlayer2"
	INTERFACE_ROOT       = "org.mpris.MediaPlayer2"
	INTERFACE_PLAYER     = "org.mpris.MediaPlayer2.Player"
	INTERFACE_TRACKLIST  = "org.mpris.MediaPlayer2.TrackList"
	INTERFACE_PLAYLISTS  = "org.mpris.MediaPlayer2.PlayLists"
	INTERFACE_PROPERTIES = "org.freedesktop.DBus.Properties"

	def __init__(self, conn):
		"""
		:Parameters:
			`conn` : string
				one of `MPRIS.PLAYERS` or the unique name of the player
		"""
		bus = dbus.SessionBus()
		
		self.conn		= MPRIS.CONNECTION_PREFIX + conn
		self.icon		= conn
		self.mpris      = bus.get_object(self.conn, MPRIS.OBJECT_PATH)
		self.properties = dbus.Interface(self.mpris, MPRIS.INTERFACE_PROPERTIES)
		self.root       = Root(self)
		self.player     = Player(self)
		self.metadata	= Metadata(self)
		
		if self.root.HasTrackList():
			self.tracklist = TrackList(self)
			
		self.playlists = Playlists(self)
		
		self.identity   = self.root.Identity()
		
		notify2.init(self.identity)
	
	def notify(self, message):
		n = notify2.Notification(self.identity, "<b>" + message + "</b>", self.icon)
		n.show()
	

class Remote:
	"""
	Base for dbus remote objects.
	"""
	def __init__(self, mpris, interface):
		self.mpris  = mpris
		self.object = dbus.Interface(mpris.mpris, interface)
		self.interface = interface

	def get(self, property, convert=True):
		"""
		Get a property.
		
		:Parameters:
			`property` : string
				name of the property
			`convert` : bool
				convert value from dbus type to standard python type
		"""
		got = self.mpris.properties.Get(self.interface, property)
		
		if convert:
			if type(got) is dbus.String:
				return got.encode('utf-8')
		
		return got

	def set(self, prop, value):
		"""
		
		"""
		self.mpris.properties.Set(self.interface, prop, value)
	
	def connect(self, signal, handler):
		"""
		"""
		self.object.connect_to_signal(signal, handler)


class Root(Remote):
	"""
	Bindings to MPRIS methods for the root interface.
	Documentation from <http://specifications.freedesktop.org/mpris-spec/>
	
	Methods :
	- Raise	() 	: nothing
	- Quit	() 	: nothing
	
	Properties :
	- CanQuit	 			b	Read only		
	- Fullscreen	 		b	Read/Write		
	- CanSetFullscreen	 	b	Read only		
	- CanRaise	 			b	Read only		
	- HasTrackList	 		b	Read only		
	- Identity	 			s	Read only		
	- DesktopEntry	 		s	Read only		
	- SupportedUriSchemes	as	Read only		
	- SupportedMimeTypes	as	Read only
	"""
	def __init__(self, mpris):
		Remote.__init__(self, mpris, MPRIS.INTERFACE_ROOT)
		
	def Raise(self):
		"""
		Brings the media player's user interface to the front using any
		appropriate mechanism available. The media player may be unable to
		control how its user interface is displayed, or it may not have a
		graphical user interface at all. In this case, the CanRaise
		property is false and this method does nothing.
		"""
		self.object.Raise()
	
	def Quit(self):
		"""
		Causes the media player to stop running.
		The media player may refuse to allow clients to shut it down. In
		this case, the CanQuit property is false and this method does
		nothing.

		Note: Media players which can be D-Bus activated, or for which
		there is no sensibly easy way to terminate a running instance (via
		the main interface or a notification area icon for example) should
		allow clients to use this method. Otherwise, it should not be
		needed. If the media player does not have a UI, this should be
		implemented.
		"""
		self.object.Quit()
	
	def CanQuit(self):
		"""
		If false, calling Quit will have no effect, and may raise a
		NotSupported error. If true, calling Quit will cause the media
		application to attempt to quit (although it may still be prevented
		from quitting by the user, for example).

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanQuit")
		
	def Fullscreen(self, on=None):
		"""
		Whether the media player is occupying the fullscreen. This is
		typically used for videos. A value of true indicates that the media
		player is taking up the full screen. Media centre software may well
		have this value fixed to true If CanSetFullscreen is true, clients
		may set this property to true to tell the media player to enter
		fullscreen mode, or to false to return to windowed mode. If
		CanSetFullscreen is false, then attempting to set this property
		should have no effect, and may raise an error. However, even if it
		is true, the media player may still be unable to fulfil the
		request, in which case attempting to set this property will have no
		effect (but should not raise an error).
	
		This property is optional. Clients should handle its absence
		gracefully.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read/Write
		"""
		if on is not None:
			self.set("Fullscreen", on)
		else:
			return self.get("Fullscreen")
		
	def CanSetFullscreen(self):
		"""
		If false, attempting to set Fullscreen will have no effect, and may
		raise an error. If true, attempting to set Fullscreen will not
		raise an error, and (if it is different from the current value)
		will cause the media player to attempt to enter or exit fullscreen
		mode.
	
		Note that the media player may be unable to fulfil the request. In
		this case, the value will not change. If the media player knows in
		advance that it will not be able to fulfil the request, however,
		this property should be false.
	
		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.
	
		Read only
		"""
		return self.get("CanSetFullscreen")
		
	def HasTrackList(self):
		"""
		Indicates whether the /org/mpris/MediaPlayer2 object implements the
		org.mpris.MediaPlayer2.TrackList interface.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("HasTrackList")
		
	def CanRaise(self):
		"""
		If false, calling Raise will have no effect, and may raise a
		NotSupported error. If true, calling Raise will cause the media
		application to attempt to bring its user interface to the front,
		although it may be prevented from doing so (by the window manager,
		for example).

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanRaise")
		
	def Identity(self):
		"""
		A friendly name to identify the media player to users. This should
		usually match the name found in .desktop files (eg: "VLC media
		player").

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("Identity")
		
	def DesktopEntry(self):
		"""
		The basename of an installed .desktop file which complies with the
		Desktop entry specification, with the ".desktop" extension
		stripped.
	
		Example: The desktop entry file is
		"/usr/share/applications/vlc.desktop", and this property contains
		"vlc"

		This property is optional. Clients should handle its absence gracefully.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("DesktopEntry")
		
	def SupportedUriSchemes(self):
		"""
		The URI schemes supported by the media player.
	
		This can be viewed as protocols supported by the player in almost
		all cases. Almost every media player will include support for the
		"file" scheme. Other common schemes are "http" and "rtsp".

		Note that URI schemes should be lower-case.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("SupportedUriSchemes")
		
	def SupportedMimeTypes(self):
		"""
		The mime-types supported by the media player.
	
		Mime-types should be in the standard format (eg: audio/mpeg or
		application/ogg).

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("SupportedMimeTypes")

class Player(Remote):
	"""
	Bindings to MPRIS methods for the player interface.
	Documentation from <http://specifications.freedesktop.org/mpris-spec/>
	
	Methods :
	- Next			()							:	nothing	
	- Previous		()							:	nothing	
	- Pause			()							:	nothing	
	- PlayPause		()							:	nothing	
	- Stop			()							:	nothing	
	- Play			()							:	nothing	
	- Seek			(x: Offset)					:	nothing	
	- SetPosition	(o: TrackId, x: Position)	:	nothing	
	- OpenUri		(s: Uri)					:	nothing	

	Properties :
	- PlaybackStatus	s (Playback_Status)		Read only		
	- LoopStatus	 	s (Loop_Status)			Read/Write		
	- Rate	 			d (Playback_Rate)		Read/Write		
	- Shuffle	 		b						Read/Write		
	- Metadata	 		a{sv} (Metadata_Map)	Read only		
	- Volume	 		d (Volume)				Read/Write		
	- Position	 		x (Time_In_Us)			Read only		
	- MinimumRate	 	d (Playback_Rate)		Read only		
	- MaximumRate	 	d (Playback_Rate)		Read only		
	- CanGoNext	 		b						Read only		
	- CanGoPrevious	 	b						Read only		
	- CanPlay	 		b						Read only		
	- CanPause	 		b						Read only		
	- CanSeek	 		b						Read only		
	- CanControl	 	b						Read only
	"""
	
	def __init__(self, mpris):
		Remote.__init__(self, mpris, MPRIS.INTERFACE_PLAYER)
	
	def Next(self):
		"""
		Skips to the next track in the tracklist.

		If there is no next track (and endless playback and track repeat
		are both off), stop playback. If playback is paused or stopped, it
		remains that way. If CanGoNext is false, attempting to call this
		method should have no effect.
		"""
		self.object.Next()
		
	def Previous(self):
		"""
		Skips to the previous track in the tracklist.
	
		If there is no previous track (and endless playback and track
		repeat are both off), stop playback. If playback is paused or
		stopped, it remains that way. If CanGoPrevious is false, attempting
		to call this method should have no effect.
		"""
		self.object.Previous()
	
	def Pause(self):
		"""
		Pauses playback.
	
		If playback is already paused, this has no effect. Calling Play
		after this should cause playback to start again from the same
		position. If CanPause is false, attempting to call this method
		should have no effect.
		"""
		self.object.Pause()
	
	def PlayPause(self):
		"""
		Pauses playback.
	
		If playback is already paused, resumes playback. If playback is
		stopped, starts playback. If CanPause is false, attempting to call
		this method should have no effect and raise an error.
		"""
		self.object.PlayPause()
	
	def Stop(self):
		"""
		Stops playback.
	
		If playback is already stopped, this has no effect. Calling Play
		after this should cause playback to start again from the beginning
		of the track. If CanControl is false, attempting to call this
		method should have no effect and raise an error.
		"""
		self.object.Stop()
	
	def Play(self):
		"""
		Starts or resumes playback.
	
		If already playing, this has no effect. If paused, playback resumes
		from the current position. If there is no track to play, this has
		no effect. If CanPlay is false, attempting to call this method
		should have no effect.
		"""
		self.object.Play()
	
	def Seek(self, offset):
		"""
		Seeks forward in the current track by the specified number of
		microseconds.
	
		A negative value seeks back. If this would mean seeking back
		further than the start of the track, the position is set to 0. If
		the value passed in would mean seeking beyond the end of the track,
		acts like a call to Next. If the CanSeek property is false, this
		has no effect.

		Parameters :
		- Offset — x (Time_In_Us) : The number of microseconds to seek
		  forward.
		"""
		self.object.Seek(offset)
	
	def SetPosition(self, track_id, position):
		"""
		Sets the current track position in microseconds.
	
		If the Position argument is less than 0, do nothing. If the
		Position argument is greater than the track length, do nothing. If
		the CanSeek property is false, this has no effect.

		Parameters :
		- TrackId — o (Track_Id) : The currently playing track's
		  identifier. If this does not match the id of the currently-playing
		  track, the call is ignored as "stale".
		  /org/mpris/MediaPlayer2/TrackList/NoTrack is not a valid value for
		  this argument.
		- Position — x (Time_In_Us) : Track position in microseconds. This
		  must be between 0 and <track_length>.
		"""
		self.object.SetPosition(track_id, position)
	
	def OpenUri(self, uri):
		"""
		Opens the Uri given as an argument

		If the playback is stopped, starts playing. If the uri scheme or
		the mime-type of the uri to open is not supported, this method does
		nothing and may raise an error. In particular, if the list of
		available uri schemes is empty, this method may not be implemented.
	
		Clients should not assume that the Uri has been opened as soon as
		this method returns. They should wait until the mpris:trackid field
		in the Metadata property changes. If the media player implements
		the TrackList interface, then the opened track should be made part
		of the tracklist, the org.mpris.MediaPlayer2.TrackList.TrackAdded
		or org.mpris.MediaPlayer2.TrackList.TrackListReplaced signal should
		be fired, as well as the
		org.freedesktop.DBus.Properties.PropertiesChanged signal on the
		tracklist interface.

		Parameters :
		- Uri — s (Uri) : Uri of the track to load. Its uri scheme should
		  be an element of the org.mpris.MediaPlayer2.SupportedUriSchemes
		  property and the mime-type should match one of the elements of
		  the org.mpris.MediaPlayer2.SupportedMimeTypes.
		"""
		self.object.OpenUri(uri)
	
	def PlaybackStatus(self):
		"""
		The current playback status.

		May be "Playing", "Paused" or "Stopped".

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("PlaybackStatus")
	
	def LoopStatus(self, value=None):
		"""
		The current loop / repeat status.
	
		May be:
		- "None" if the playback will stop when there are no more tracks to
		  play
		- "Track" if the current track will start again from the begining
		  once it has finished playing
		- "Playlist" if the playback loops through a list of tracks
	
		This property is optional, and clients should deal with
		NotSupported errors gracefully. If CanControl is false, attempting
		to set this property should have no effect and raise an error.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read/Write
		"""
		if value is None:
			return self.get("LoopStatus")
		else:
			self.set("LoopStatus", value)
	
	def Rate(self, rate=None):
		"""
		The current playback rate.
	
		The value must fall in the range described by MinimumRate and
		MaximumRate, and must not be 0.0. If playback is paused, the
		PlaybackStatus property should be used to indicate this. A value of
		0.0 should not be set by the client. If it is, the media player
		should act as though Pause was called.
	
		If the media player has no ability to play at speeds other than the
		normal playback rate, this must still be implemented, and must
		return 1.0. The MinimumRate and MaximumRate properties must also be
		set to 1.0.
	
		Not all values may be accepted by the media player. It is left to
		media player implementations to decide how to deal with values they
		cannot use; they may either ignore them or pick a "best fit" value.
		Clients are recommended to only use sensible fractions or multiples
		of 1 (eg: 0.5, 0.25, 1.5, 2.0, etc).

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read/Write
		"""
		if rate is None:
			return self.get("Rate")
		else:
			self.set("Rate", rate)
	
	def Shuffle(self, shuffle=None):
		"""
		A value of false indicates that playback is progressing linearly
		through a playlist, while true means playback is progressing
		through a playlist in some other order.
	
		This property is optional, and clients should deal with
		NotSupported errors gracefully. If CanControl is false, attempting
		to set this property should have no effect and raise an error.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read/Write
		"""
		if shuffle is None:
			return self.get("Shuffle")
		else:
			self.set("Shuffle", shuffle)
	
	def Metadata(self):
		"""
		The metadata of the current element.
	
		If there is a current track, this must have a "mpris:trackid" entry
		(of D-Bus type "o") at the very least, which contains a D-Bus path
		that uniquely identifies this track.

		See the type documentation for more details.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("Metadata")
	
	def Volume(self, volume=None):
		"""
		The volume level.
	
		When setting, if a negative value is passed, the volume should be
		set to 0.0. If CanControl is false, attempting to set this property
		should have no effect and raise an error.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read/Write
		"""
		if volume is None:
			return self.get("Volume")
		else:
			self.set("Volume", volume)
	
	def Position(self):
		"""
		The current track position in microseconds, between 0 and the
		'mpris:length' metadata entry (see Metadata).
	
		Note: If the media player allows it, the current playback position
		can be changed either the SetPosition method or the Seek method on
		this interface. If this is not the case, the CanSeek property is
		false, and setting this property has no effect and can raise an
		error.
	
		If the playback progresses in a way that is inconstistant with the
		Rate property, the Seeked signal is emited.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("Position")
	
	def MinimumRate(self):
		"""
		The minimum value which the Rate property can take. Clients should
		not attempt to set the Rate property below this value.
	
		Note that even if this value is 0.0 or negative, clients should not
		attempt to set the Rate property to 0.0.

		This value should always be 1.0 or less.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("MinimumRate")
	
	def MaximumRate(self):
		"""
		The maximum value which the Rate property can take. Clients should
		not attempt to set the Rate property above this value.
	
		This value should always be 1.0 or greater.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("MaximumRate")
	
	def CanGoNext(self):
		"""
		Whether the client can call the Next method on this interface and
		expect the current track to change.
	
		If it is unknown whether a call to Next will be successful (for
		example, when streaming tracks), this property should be set to
		true. If CanControl is false, this property should also be false.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanGoNext")
	
	def CanGoPrevious(self):
		"""
		Whether the client can call the Previous method on this interface
		and expect the current track to change.
	
		If it is unknown whether a call to Previous will be successful (for
		example, when streaming tracks), this property should be set to
		true. If CanControl is false, this property should also be false.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanGoPrevious")
	
	def CanPlay(self):
		"""
		Whether playback can be started using Play or PlayPause.
	
		Note that this is related to whether there is a "current track":
		the value should not depend on whether the track is currently
		paused or playing. In fact, if a track is currently playing (and
		CanControl is true), this should be true.

		If CanControl is false, this property should also be false.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanPlay")
	
	def CanPause(self):
		"""
		Whether playback can be paused using Pause or PlayPause.
	
		Note that this is an intrinsic property of the current track: its
		value should not depend on whether the track is currently paused or
		playing. In fact, if playback is currently paused (and CanControl
		is true), this should be true.

		If CanControl is false, this property should also be false.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanPause")
	
	def CanSeek(self):
		"""
		Whether the client can control the playback position using Seek and
		SetPosition. This may be different for different tracks.
	
		If CanControl is false, this property should also be false.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanSeek")
	
	def CanControl(self):
		"""
		Whether the media player may be controlled over this interface.
	
		This property is not expected to change, as it describes an
		intrinsic capability of the implementation.

		If this is false, clients should assume that all properties on this
		interface are read-only (and will raise errors if writing to them
		is attempted), no methods are implemented and all other properties
		starting with "Can" are also false.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanControl")
	
	def on_Seeked(self, handler):
		"""
		Indicates that the track position has changed in a way that is
		inconsistant with the current playing state.
		
		When this signal is not received, clients should assume that:
			- When playing, the position progresses according to the rate
			property.
			- When paused, it remains constant.
			
		This signal does not need to be emitted when playback starts or when
		the track changes, unless the track is starting at an unexpected
		position. An expected position would be the last known one when going
		from Paused to Playing, and 0 when going from Stopped to Playing.

		:Parameters:
			`Position` — x (Time_In_Us)
				The new position, in microseconds.
		"""
		self.connect('Seeked', handler)

class TrackList(Remote):
	"""
	Bindings to MPRIS methods for the tracklist interface.
	Documentation from <http://specifications.freedesktop.org/mpris-spec/>
	
	Methods :
	- GetTracksMetadata	(ao: TrackIds)								:	aa{sv}: Metadata	
	- AddTrack			(s: Uri, o: AfterTrack, b: SetAsCurrent)	:	nothing	
	- RemoveTrack		(o: TrackId)								:	nothing	
	- GoTo				(o: TrackId)								:	nothing	

	Signals :
	- TrackListReplaced		(ao: Tracks, o: CurrentTrack)	
	- TrackAdded			(a{sv}: Metadata, o: AfterTrack)	
	- TrackRemoved			(o: TrackId)	
	- TrackMetadataChanged	(o: TrackId, a{sv}: Metadata)	

	Properties :
	- Tracks	 		ao (Track_Id_List)	Read only		
	- CanEditTracks		b					Read only
		
	Types :
	- Uri			Simple Type	s	
	- Metadata_Map	Mapping	a{sv}	
	"""
	
	def __init__(self, mpris):
		Remote.__init__(self, mpris, MPRIS.INTERFACE_TRACKLIST)

	def GetTracksMetadata(self, track_ids):
		"""
		Gets all the metadata available for a set of tracks.

		Each set of metadata must have a "mpris:trackid" entry at the very
		least, which contains a string that uniquely identifies this track
		within the scope of the tracklist.

		Parameters :
		- TrackIds — ao (Track_Id_List) : The list of track ids for which
		  metadata is requested.

		Returns :
		- Metadata — aa{sv} (Metadata_Map_List) : Metadata of the set of
		  tracks given as input. See the type documentation for more
		  details.
		"""
		return self.object.GetTracksMetadata(track_ids)
	
	def AddTrack(self, uri, after_track, set_as_current):
		"""
		Adds a URI in the TrackList.
	
		If the CanEditTracks property is false, this has no effect.

		Note: Clients should not assume that the track has been added at
		the time when this method returns. They should wait for a
		TrackAdded (or TrackListReplaced) signal.

		Parameters :
		- Uri — s (Uri) : The uri of the item to add. Its uri scheme should
		  be an element of the org.mpris.MediaPlayer2.SupportedUriSchemes
		  property and the mime-type should match one of the elements of
		  the org.mpris.MediaPlayer2.SupportedMimeTypes
		- AfterTrack — o (Track_Id) : The identifier of the track after
		  which the new item should be inserted. The path
		  /org/mpris/MediaPlayer2/TrackList/NoTrack indicates that the
		  track should be inserted at the start of the track list.
		- SetAsCurrent — b : Whether the newly inserted track should be
		  considered as the current track. Setting this to true has the
		  same effect as calling GoTo afterwards.
		"""
		self.object.AddTrack(uri, after_track, set_as_current)
	
	def RemoveTrack(self, track_id):
		"""
		Removes an item from the TrackList.
	
		If the track is not part of this tracklist, this has no effect. If
		the CanEditTracks property is false, this has no effect.

		Note: Clients should not assume that the track has been removed at
		the time when this method returns. They should wait for a
		TrackRemoved (or TrackListReplaced) signal.

		Parameters :
		- TrackId — o (Track_Id) : Identifier of the track to be removed. 
		  /org/mpris/MediaPlayer2/TrackList/NoTrack is not a valid value
		  for this argument.
		"""
		self.object.RemoveTrack(track_id)
	
	def GoTo(self, track_id):
		"""
		Skip to the specified TrackId.
	
		If the track is not part of this tracklist, this has no effect. If
		this object is not /org/mpris/MediaPlayer2, the current TrackList's
		tracks should be replaced with the contents of this TrackList, and
		the TrackListReplaced signal should be fired from
		/org/mpris/MediaPlayer2.

		Parameters :
		- TrackId — o (Track_Id) : Identifier of the track to skip to.
		  /org/mpris/MediaPlayer2/TrackList/NoTrack is not a valid value
		  for this argument.
		"""
		self.object.GoTo(track_id)
	
	def Tracks(self):
		"""
		An array which contains the identifier of each track in the
		tracklist, in order.
	
		The org.freedesktop.DBus.Properties.PropertiesChanged signal is
		emited every time this property changes, but the signal message
		does not contain the new value. Client implementations should
		rather rely on the TrackAdded, TrackRemoved and TrackListReplaced
		signals to keep their representation of the tracklist up to date.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("Tracks")
	
	def CanEditTracks(self):
		"""
		If false, calling AddTrack or RemoveTrack will have no effect, and
		may raise a NotSupported error.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("CanEditTracks")
	
	def on_TrackListReplaced(self, handler):
		"""
		Indicates that the entire tracklist has been replaced.
		
		It is left up to the implementation to decide when a change to the track
		list is invasive enough that this signal should be emitted instead of a
		series of TrackAdded and TrackRemoved signals.

		:Parameters:
			`Tracks` — ao (Track_Id_List)
				The new content of the tracklist.
			`CurrentTrack` — o (Track_Id)
				The identifier of the track to be considered as current.
				/org/mpris/MediaPlayer2/TrackList/NoTrack indicates that there
				is no current track. This should correspond to the
				mpris:trackid field of the Metadata property of the
				org.mpris.MediaPlayer2.Player interface.
		"""
		self.connect('TrackListReplaced', handler)
	
	def on_TrackAdded(self, handler):
		"""
		Indicates that a track has been added to the track list.
	
		:Parameters:
			`Metadata` — a{sv} (Metadata_Map)
				The metadata of the newly added item.
				This must include a mpris:trackid entry.
				See the type documentation for more details.
			`AfterTrack` — o (Track_Id)
				The identifier of the track after which the new track was
				inserted. The path /org/mpris/MediaPlayer2/TrackList/NoTrack
				indicates that the track was inserted at the start of the track
				list.
		"""
		self.connect('TrackAdded', handler)
	
	def on_TrackRemoved(self, handler):
		"""
		Indicates that a track has been removed from the track list.

		:Parameters:
			`TrackId` — o (Track_Id)
				The identifier of the track being removed.
				/org/mpris/MediaPlayer2/TrackList/NoTrack is not a valid value
				for this argument.
		"""
		self.connect('TrackRemoved', handler)
	
	def on_TrackMetadataChanged(self, handler):
		"""
		Indicates that the metadata of a track in the tracklist has changed.
		
		This may indicate that a track has been replaced, in which case the
		mpris:trackid metadata entry is different from the TrackId argument.

		:Parameters:
			`TrackId` — o (Track_Id)
				The id of the track which metadata has changed.
				If the track id has changed, this will be the old value.
				/org/mpris/MediaPlayer2/TrackList/NoTrack is not a valid value
				for this argument.
			`Metadata` — a{sv} (Metadata_Map)
				The new track metadata.
				This must include a mpris:trackid entry. If the track id has
				changed, this will be the new value.
				See the type documentation for more details.
		"""
		self.connect('TrackMetadataChanged', handler)
	

class Playlists(Remote):
	"""
	Bindings to MPRIS methods for the playlists interface.
	Documentation from <http://specifications.freedesktop.org/mpris-spec/>
	
	Methods :
	- ActivatePlaylist	(o: PlaylistId)										:	nothing	
	- GetPlaylists		(u: Index, u: MaxCount, s: Order, b: ReverseOrder)	:	a(oss): Playlists	
	
	Signals :
	- PlaylistChanged	((oss): Playlist)	

	Properties :
	- PlaylistCount	 	u								Read only		
	- Orderings	 		as (Playlist_Ordering_List)		Read only		
	- ActivePlaylist	(b(oss)) (Maybe_Playlist)		Read only		

	Types :
	- Playlist_Id			Simple Type	o	
	- Uri					Simple Type	s	
	- Playlist_Ordering		Enum	s	
	- Playlist				Struct	(oss)	
	- Maybe_Playlist		Struct	(b(oss))	
	"""
	
	def __init__(self, mpris):
		Remote.__init__(self, mpris, MPRIS.INTERFACE_PLAYLISTS)
	
	def ActivatePlaylist(self, playlist_id):
		"""
		Starts playing the given playlist.
	
		Note that this must be implemented. If the media player does not
		allow clients to change the playlist, it should not implement this
		interface at all.

		It is up to the media player whether this completely replaces the
		current tracklist, or whether it is merely inserted into the
		tracklist and the first track starts. For example, if the media
		player is operating in a "jukebox" mode, it may just append the
		playlist to the list of upcoming tracks, and skip to the first
		track in the playlist.

		Parameters :
		- PlaylistId — o : The id of the playlist to activate.
		"""
		self.object.ActivatePlaylist(playlist_id)
	
	def GetPlaylists(self, index, max_count, order, reverse_order):
		"""
		Gets a set of playlists.
	
		Parameters :
		- Index — u : The index of the first playlist to be fetched
		  (according to the ordering).
		- MaxCount — u : The maximum number of playlists to fetch.
		- Order — s (Playlist_Ordering) : The ordering that should be used.
		- ReverseOrder — b : Whether the order should be reversed.
	
		Returns :
		- Playlists — a(oss) (Playlist_List) : A list of (at most MaxCount)
		  playlists.
		"""
		self.object.GetPlaylists(index, max_count, order, reverse_order)
	
	def PlaylistCount(self):
		"""
		The number of playlists available.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("PlaylistCount")
	
	def Orderings(self):
		"""
		The available orderings. At least one must be offered.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("Orderings")
	
	def ActivePlaylist(self):
		"""
		The currently-active playlist.
	
		If there is no currently-active playlist, the structure's Valid
		field will be false, and the Playlist details are undefined.
	
		Note that this may not have a value even after ActivatePlaylist is
		called with a valid playlist id as ActivatePlaylist implementations
		have the option of simply inserting the contents of the playlist
		into the current tracklist.

		When this property changes, the
		org.freedesktop.DBus.Properties.PropertiesChanged signal is emitted
		with the new value.

		Read only
		"""
		return self.get("ActivePlaylist")
	
	def on_PlaylistChanged(self, handler):
		"""
		Indicates that either the Name or Icon attribute of a playlist has
		changed. Client implementations should be aware that this signal may
		not be implemented.
		
		:Parameters:
			`Playlist` — (oss) (Playlist)
				The playlist which details have changed.
		"""
		self.connect('PlayListChanged', handler)

class Metadata:
	"""
	Specifications taken from :
	_`http://www.freedesktop.org/wiki/Specifications/mpris-spec/metadata`
	
	:MPRIS-specific:
		- mpris:trackid
		- mpris:length
		- mpris:artUrl

	:Common Xesam properties:
		- xesam:album
		- xesam:albumArtist
		- xesam:artist
		- xesam:asText
		- xesam:audioBPM
		- xesam:autoRating
		- xesam:comment
		- xesam:composer
		- xesam:contentCreated
		- xesam:discNumber
		- xesam:firstUsed
		- xesam:genre
		- xesam:lastUsed
		- xesam:lyricist
		- xesam:title
		- xesam:trackNumber
		- xesam:url
		- xesam:useCount
		- xesam:userRating
	"""
	def __init__(self, mpris):
		"""
		"""
		self.mpris = mpris
		self.data  = mpris.player.Metadata()
		
		mpris.properties.connect_to_signal('PropertiesChanged', self.update)
	
	def update(self, *args):
		if len(args) > 1 and args[0] == MPRIS.INTERFACE_PLAYER and 'Metadata' in args [1]:
			self.data = args[1]['Metadata']
			print "Current track:", self.title()
	
	def trackid(self):
		"""
		D-Bus path: A unique identity for this track within the context of an
		MPRIS object (eg: tracklist).
		"""
		return self.data['mpris:trackid']
	
	def length(self):
		"""
		64-bit integer: The duration of the track in microseconds.
		"""
		return self.data['mpris:length']
	
	def artUrl(self):
		"""
		URI: The location of an image representing the track or album. Clients
		should not assume this will continue to exist when the media player
		stops giving out the URL.
		"""
		return self.data['mpris:artUrl']
	
	def album(self):
		"""
		String: The album name.
		"""
		return self.data['xesam:album']
	
	def albumArtist(self):
		"""
		List of Strings: The album artist(s).
		"""
		return self.data['xesam:albumArtist']
	
	def artist(self):
		"""
		List of Strings: The track artist(s).
		"""
		return self.data['xesam:artist']
	
	def asText(self):
		"""
		String: The track lyrics.
		"""
		return self.data['xesam:asText']
	
	def audioBPM(self):
		"""
		Integer: The speed of the music, in beats per minute.
		"""
		return self.data['xesam:audioBPM']
	
	def autoRating(self):
		"""
		Float: An automatically-generated rating, based on things such as how
		often it has been played. This should be in the range 0.0 to 1.0.
		"""
		return self.data['xesam:autoRating']
	
	def comment(self):
		"""
		List of Strings: A (list of) freeform comment(s).
		"""
		return self.data['xesam:comment']
	
	def composer(self):
		"""
		List of Strings: The composer(s) of the track.
		"""
		return self.data['xesam:composer']
	
	def contentCreated(self):
		"""
		Date/Time: When the track was created. Usually only the year component
		will be useful.
		"""
		return self.data['xesam:contentCreated']
	
	def discNumber(self):
		"""
		Integer: The disc number on the album that this track is from.
		"""
		return self.data['xesam:discNumber']
	
	def firstUsed(self):
		"""
		Date/Time: When the track was first played.
		"""
		return self.data['xesam:firstUsed']
	
	def genre(self):
		"""
		List of Strings: The genre(s) of the track.
		"""
		return self.data['xesam:genre']
	
	def lastUsed(self):
		"""
		Date/Time: When the track was last played.
		"""
		return self.data['xesam:lastUsed']
	
	def lyricist(self):
		"""
		List of Strings: The lyricist(s) of the track.
		"""
		return self.data['xesam:lyricist']
	
	def title(self):
		"""
		String: The track title.
		"""
		return self.data['xesam:title']
	
	def trackNumber(self):
		"""
		Integer: The track number on the album disc.
		"""
		return self.data['xesam:trackNumber']
	
	def url(self):
		"""
		URI: The URL of the file. Local files use the file:// schema.
		"""
		return self.data['xesam:url']
	
	def useCount(self):
		"""
		Integer: The number of times the track has been played.
		"""
		return self.data['xesam:useCount']
	
	def userRating(self):
		"""
		Float: A user-specified rating. This should be in the range 0.0 to 1.0.
		"""
		return self.data['xesam:userRating']

