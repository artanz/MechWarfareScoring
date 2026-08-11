#!/usr/bin/python

import MWScore
import wx
import pickle
import json
import traceback
import threading
import functools
import http.server
import serial.tools.list_ports


class OverlayServer:
        """Serves the OBS overlay and score data over HTTP in a background thread."""

        def __init__( self, port=8080 ):
                self.port = port
                self.server = None
                self.thread = None

        def Start( self ):
                if self.server is not None:
                        return True
                try:
                        handler = functools.partial( http.server.SimpleHTTPRequestHandler, directory="." )
                        self.server = http.server.HTTPServer( ( "", self.port ), handler )
                        self.thread = threading.Thread( target=self.server.serve_forever, daemon=True )
                        self.thread.start()
                        return True
                except Exception:
                        self.server = None
                        self.thread = None
                        return False

        def Stop( self ):
                if self.server is not None:
                        self.server.shutdown()
                        self.server.server_close()
                self.server = None
                self.thread = None

"""

	MWScoreFrame

"""

class MWScoreFrame( wx.Frame ):
        ID_QUIT = wx.NewIdRef()
        ID_MATCHSETUP = wx.NewIdRef()
        ID_MATCHSTART = wx.NewIdRef()
        ID_MATCHPAUSE = wx.NewIdRef()
        ID_MATCHRESET = wx.NewIdRef()
        ID_MATCHRESETHP = wx.NewIdRef()
        ID_TRANSPONDERSETUP = wx.NewIdRef()
        ID_TRANSPONDERCONFIG = wx.NewIdRef()
        ID_SOCKETSETUP = wx.NewIdRef()
        ID_TRANSPONDERHPUPDATE = wx.NewIdRef()
        ID_OVERLAYTOGGLE = wx.NewIdRef()
        ID_OVERLAYSTOP = wx.NewIdRef()

        # Class constructor
        def __init__( self ):
                wx.Frame.__init__( self, None, wx.ID_ANY, style=wx.DEFAULT_FRAME_STYLE, name="MWScore Server" )
                self.ScoreServer = MWScore.ScoreServer()
                
                # Menu Bar
                self.MenuBar = wx.MenuBar()
                self.FileMenu = wx.Menu()
                self.TransponderMenu = wx.Menu()
                self.SocketMenu = wx.Menu()
                self.MatchMenu = wx.Menu()

                self.FileMenu.Append( self.ID_QUIT, "Quit" )
                self.Bind( wx.EVT_MENU, self.Quit, id=self.ID_QUIT )

                self.TransponderMenu.Append( self.ID_TRANSPONDERSETUP, "Connect" )
                self.TransponderMenu.Append( self.ID_TRANSPONDERCONFIG, "Configure Transponder" )
                self.TransponderMenu.Append( self.ID_TRANSPONDERHPUPDATE, "Refresh Transponder HP" )
                self.Bind( wx.EVT_MENU, self.TransponderConnect, id=self.ID_TRANSPONDERSETUP )
                self.Bind( wx.EVT_MENU, self.TransponderConfig, id=self.ID_TRANSPONDERCONFIG )
                self.Bind( wx.EVT_MENU, self.TransponderHpUpdate, id=self.ID_TRANSPONDERHPUPDATE )

                self.SocketMenu.Append( self.ID_SOCKETSETUP, "Setup" )
                self.Bind( wx.EVT_MENU, self.SocketSetup, id=self.ID_SOCKETSETUP )

                self.OverlayMenu = wx.Menu()
                self.OverlayMenu.AppendCheckItem( self.ID_OVERLAYTOGGLE, "Enable Overlay" )
                self.OverlayMenu.Append( self.ID_OVERLAYSTOP, "Stop Overlay" )
                self.Bind( wx.EVT_MENU, self.ToggleOverlay, id=self.ID_OVERLAYTOGGLE )
                self.Bind( wx.EVT_MENU, self.StopOverlay, id=self.ID_OVERLAYSTOP )
                self.Overlay = OverlayServer()

                self.MatchMenu.Append( self.ID_MATCHSETUP, "Setup" )
                self.MatchMenu.Append( self.ID_MATCHSTART, "Start/Resume" )
                self.MatchMenu.Append( self.ID_MATCHPAUSE, "Pause" )
                self.MatchMenu.Append( self.ID_MATCHRESET, "Reset" )
                self.MatchMenu.Append( self.ID_MATCHRESETHP, "Reset HP" )
                
                self.Bind( wx.EVT_MENU, self.MatchSetup, id=self.ID_MATCHSETUP )
                self.Bind( wx.EVT_MENU, self.MatchStart, id=self.ID_MATCHSTART )
                self.Bind( wx.EVT_MENU, self.MatchPause, id=self.ID_MATCHPAUSE )
                self.Bind( wx.EVT_MENU, self.MatchReset, id=self.ID_MATCHRESET )
                self.Bind( wx.EVT_MENU, self.MatchResetHP, id=self.ID_MATCHRESETHP )

                self.MenuBar.Append( self.FileMenu, "&File" )
                self.MenuBar.Append( self.MatchMenu, "&Match" )
                self.MenuBar.Append( self.TransponderMenu, "&Transponder" )
                self.MenuBar.Append( self.SocketMenu, "&Socket" )
                self.MenuBar.Append( self.OverlayMenu, "&Overlay" )
                self.SetMenuBar( self.MenuBar )

                # Panel
                self.Panel = MatchPanel( self, -1 )

                # Fix for flicker
                self.SetDoubleBuffered(True)

                # Frame Update Timer
                self.timer = wx.Timer(self)
                self.timer.Start(20)
                self.Bind(wx.EVT_TIMER, self.OnTimer)
                self.Bind( wx.EVT_CLOSE, self.OnClose )

                self.Show( True )
                self.SetTitle( "Mech Warfare Match Score" )

        # Updates the frames panel and Broadcasts match data to clients
        def OnTimer( self, event ):
                self.Panel.Refresh()
                self.ScoreServer.SocketServer.Broadcast( self.ScoreServer.Match.MatchData() )

        # Opens dialog to configure a new match.
        def MatchSetup( self, event ):
                MatchLength = None
                MatchType = None
                NumTeams = None
                MatchRuleSet = None
                MechList = []
                try:
                        f = open("last-match.pkl", "rb")
                        data = pickle.load(f)
                        f.close()
                        MatchLength = data.get("MatchLength", MatchLength)
                        MatchType = data.get("MatchType", MatchType)
                        NumTeams = data.get("NumTeams", NumTeams)
                        MatchRuleSet = data.get("MatchRuleSet", MatchRuleSet)
                        MechList = data.get("MechList", MechList)
                except:
                        print("Pickle Failed")
                        pass

                data = { "MatchLength":MatchLength, "MatchType":MatchType, "NumTeams":NumTeams, "MatchRuleSet":MatchRuleSet, "MechList":MechList }
                dlg = MatchSetupDialog(self, -1, data)

                if dlg.ShowModal() != wx.ID_OK:
                        dlg.Destroy()
                        return

                MatchLength = int(dlg.MatchLengthChoice.GetValue()) * 600
                MatchType = MWScore.MATCH_TEAM if dlg.MatchTypeChoice.GetValue() == "Team" else MWScore.MATCH_FFA
                MatchRuleSet = self._ruleset_from_choice( dlg.MatchRulesChoice.GetValue() )
                NumTeams = int( dlg.NumTeamsChoice.GetValue() )

                MechList = []
                self.ScoreServer.MechList.ResetMechs()

                if MatchType == MWScore.MATCH_TEAM:
                        for t in range( len( dlg.MechListBoxes ) ):
                                for s in dlg.MechListBoxes[t].GetSelections():
                                        m = self.ScoreServer.MechList.MechByID( int( dlg.MechListBoxes[t].GetString(s).split(":")[0] ) )
                                        m.Team = t + 1
                                        MechList.append( m )
                else:
                        t = 1
                        for s in dlg.MechListBoxes[0].GetSelections():
                                m = self.ScoreServer.MechList.MechByID( int( dlg.MechListBoxes[0].GetString(s).split(":")[0] ) )
                                m.Team = t
                                MechList.append( m )
                                t += 1

                dlg.Destroy()

                data = { "MatchLength":MatchLength, "MatchType":MatchType, "NumTeams":NumTeams, "MatchRuleSet":MatchRuleSet, "MechList":MechList }
                f = open("last-match.pkl", "wb")
                pickle.dump(data, f)
                f.close()

                # Stop the frame update timer and current match thread.
                self.timer.Stop()
                self.ScoreServer.Match.KillThread()

                # Create the new match.
                self.ScoreServer.Match = MWScore.Match( self.ScoreServer, MatchType, MatchLength, MatchRuleSet, MechList )

                # Destroy and recreate a new match panel.
                self.Panel.Destroy()
                self.Panel = MatchPanel( self, -1 )

                # Resume the frame update timer.
                self.timer.Start()

        # start or resume a match
        def MatchStart( self, event ):
                self.ScoreServer.Match.Start()
        
        # Pause a match
        def MatchPause( self, event ):
                self.ScoreServer.Match.Pause()

        # Reset the match        
        def MatchReset( self, event ):
                try:
                        self.ScoreServer.Match.Reset()
                except Exception as x :
                        traceback.print_exc()
                        wx.MessageBox("Exception in Reset:\r\n" + str(x), "Error", wx.OK | wx.ICON_ERROR);

        # Reset the match and HP
        def MatchResetHP( self, event ):
                try:
                        self.ScoreServer.Match.ResetHP()
                except Exception as x :
                        traceback.print_exc()
                        wx.MessageBox("Exception in Reset:\r\n" + str(x), "Error", wx.OK | wx.ICON_ERROR);

        # Opens dialog to configure to ScoreServer's SocketServer
        def SocketSetup( self, event ):
                dlg = SocketServerDialog( self, -1 )
                if dlg.ShowModal() == wx.ID_OK:
                        self.ScoreServer.SocketServer.KillThread()
                        self.ScoreServer.SocketServer = MWScore.SocketServer( self.ScoreServer, dlg.HostChoice.GetValue(), int(dlg.PortChoice.GetValue()) )
                dlg.Destroy()

        # Connect to the transponder serial port.
        def TransponderConnect( self, event ):
                dlg = TransponderConnectionDialog( self, -1 )
                if dlg.ShowModal() != wx.ID_OK:
                        dlg.Destroy()
                        return

                self.ScoreServer.TransponderListener.KillThread()
                self.ScoreServer.TransponderListener = MWScore.TransponderListener( self.ScoreServer, dlg.PortChoice.GetValue(), int( dlg.BaudChoice.GetValue() ) )
                if not self.ScoreServer.TransponderListener.Xbee:
                        wx.MessageBox( "Could not open Transponder port " + self.ScoreServer.TransponderListener.Port, "Error", wx.OK | wx.ICON_ERROR )
                dlg.Destroy()

        # Configure a transponder (ID, HP, ruleset). Requires an active connection.
        def TransponderConfig( self, event ):
                if not self.ScoreServer.TransponderListener.Xbee:
                        wx.MessageBox( "Not connected to a transponder. Use Transponder > Connect first.", "Error", wx.OK | wx.ICON_ERROR )
                        return
                dlg = TransponderConfigDialog( self, -1 )
                if dlg.ShowModal() != wx.ID_OK:
                        dlg.Destroy()
                        return
                rules = self._ruleset_from_choice( dlg.MatchRulesChoice.GetValue() )
                self.ScoreServer.TransponderListener.WriteTransponderNewID( int( dlg.CurrentIDChoice.GetValue() ), int( dlg.NewIDChoice.GetValue() ) )
                self.ScoreServer.TransponderListener.WriteTransponder( int( dlg.NewIDChoice.GetValue() ), int( dlg.SetHpChoice.GetValue() ), rules )
                dlg.Destroy()

        # Converts a ruleset display name into its numeric code.
        def _ruleset_from_choice( self, value ):
                if value == "Max HP Per Panel":
                        return 1
                if value == "Healing":
                        return 2
                if value == "Cooldown Increase":
                        return 3
                return 0
        # Reset the match
        def TransponderHpUpdate( self, event ):
                try:
                        self.ScoreServer.Match.UpdateTransponderHP()
                except Exception as x:
                        traceback.print_exc()
                        wx.MessageBox("Exception in Transmit HP:\r\n" + str(x), "Error", wx.OK | wx.ICON_ERROR);
                

        # Kills all threads and closes the program.
        def Quit( self, event ):
                self.Close()

        # Handles the window close button (and Quit) with a clean shutdown.
        def OnClose( self, event ):
                self._Shutdown()
                self.Destroy()

        # Stops the UI timer and shuts down all background threads.
        def _Shutdown( self ):
                self.timer.Stop()
                self.Overlay.Stop()
                self.ScoreServer.KillAll()

        # Toggles the OBS overlay HTTP server on/off.
        def ToggleOverlay( self, event ):
                if event.IsChecked():
                        if self.Overlay.Start():
                                wx.MessageBox( "Overlay server started.\n\nIn OBS, add a Browser Source pointing to:\nhttp://localhost:%d/obs_overlay.html" % self.Overlay.port, "Overlay", wx.OK | wx.ICON_INFORMATION )
                        else:
                                wx.MessageBox( "Could not start the overlay server on port %d. Is it already in use?" % self.Overlay.port, "Overlay", wx.OK | wx.ICON_ERROR )
                                self.OverlayMenu.Check( self.ID_OVERLAYTOGGLE, False )
                else:
                        self.Overlay.Stop()

        # Stops the overlay server and unchecks the Enable Overlay item.
        def StopOverlay( self, event ):
                self.Overlay.Stop()
                self.OverlayMenu.Check( self.ID_OVERLAYTOGGLE, False )
"""

	MatchSetupDialog

"""
		
class MatchSetupDialog( wx.Dialog ):

        def __init__( self, parent, id, data ):
                wx.Dialog.__init__( self, parent, id, title="Match Setup" )
                self.MechChoices = [ str( m.ID ) + ": " + str( m.Name ) for m in parent.ScoreServer.MechList.List ]
                self.MechListBoxes = []

                # Match settings
                self.MatchLengthText = wx.StaticText( self, -1, "Match Length (minutes):" )
                self.MatchLengthChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=[ str( i ) for i in range( 1, 21 ) ] )
                if data.get( "MatchLength", None ) is not None:
                        self.MatchLengthChoice.SetValue( str( int( data.get( "MatchLength", 0 ) / 600 ) ) )

                self.MatchTypeText = wx.StaticText( self, -1, "Match Type:" )
                typeChoices = [ "Team", "Free For All" ]
                self.MatchTypeChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=typeChoices )
                if data.get( "MatchType", None ) is not None:
                        self.MatchTypeChoice.SetValue( typeChoices[ data.get( "MatchType", 1 ) - 1 ] )

                self.NumTeamsText = wx.StaticText( self, -1, "Number Of Teams:" )
                self.NumTeamsChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=[ str( i ) for i in range( 2, 11 ) ] )
                if data.get( "NumTeams", None ) is not None:
                        self.NumTeamsChoice.SetValue( str( data.get( "NumTeams", 2 ) ) )

                self.MatchRulesText = wx.StaticText( self, -1, "Ruleset:" )
                rulesChoices = [ "Default", "Max HP Per Panel", "Healing", "Cooldown Increase" ]
                self.MatchRulesChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=rulesChoices )
                if data.get( "MatchRuleSet", None ) is not None:
                        self.MatchRulesChoice.SetValue( rulesChoices[ data.get( "MatchRuleSet", 0 ) ] )

                # Mech selection notebook (one tab per team, or a single tab for FFA)
                self.Notebook = wx.Notebook( self, -1 )

                self.Bind( wx.EVT_COMBOBOX, self.OnSettingsChange, self.MatchTypeChoice )
                self.Bind( wx.EVT_COMBOBOX, self.OnSettingsChange, self.NumTeamsChoice )
                self._build_notebook()

                # Buttons
                self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
                self.OKButton = wx.Button( self, wx.ID_OK, "OK" )

                # Layout
                settingsSizer = wx.BoxSizer( wx.VERTICAL )
                settingsSizer.Add( self._row( self.MatchLengthText, self.MatchLengthChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                settingsSizer.Add( self._row( self.MatchTypeText, self.MatchTypeChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                settingsSizer.Add( self._row( self.NumTeamsText, self.NumTeamsChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                settingsSizer.Add( self._row( self.MatchRulesText, self.MatchRulesChoice ), 0, wx.ALL|wx.EXPAND, 2 )

                btnSizer = wx.BoxSizer( wx.HORIZONTAL )
                btnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
                btnSizer.Add( self.OKButton, 0, wx.ALL, 5 )

                topSizer = wx.BoxSizer( wx.VERTICAL )
                topSizer.Add( settingsSizer, 0, wx.ALL|wx.EXPAND, 5 )
                topSizer.Add( self.Notebook, 1, wx.ALL|wx.EXPAND, 5 )
                topSizer.Add( btnSizer, 0, wx.ALL|wx.CENTER, 5 )

                self.SetSizer( topSizer )
                topSizer.Fit( self )
                self.SetMinSize( ( 520, 560 ) )

        def _row( self, label, ctrl ):
                s = wx.BoxSizer( wx.HORIZONTAL )
                s.Add( label, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
                s.Add( ctrl, 2, wx.ALL, 5 )
                return s

        def _build_notebook( self ):
                self.MechListBoxes = []
                self.Notebook.DeleteAllPages()
                if self.MatchTypeChoice.GetValue() == "Team":
                        for t in range( int( self.NumTeamsChoice.GetValue() ) ):
                                page = self._make_mech_page( "Team %d" % ( t + 1 ) )
                                self.Notebook.AddPage( page, "Team %d" % ( t + 1 ) )
                else:
                        page = self._make_mech_page( "Free For All" )
                        self.Notebook.AddPage( page, "Mechs" )

        def _make_mech_page( self, title ):
                panel = wx.Panel( self.Notebook )
                sizer = wx.BoxSizer( wx.VERTICAL )
                label = wx.StaticText( panel, -1, "Select mechs for " + title + ":" )
                lb = wx.ListBox( panel, -1, style=wx.LB_EXTENDED, choices=self.MechChoices )
                sizer.Add( label, 0, wx.ALL, 5 )
                sizer.Add( lb, 1, wx.ALL|wx.EXPAND, 5 )
                panel.SetSizer( sizer )
                self.MechListBoxes.append( lb )
                return panel

        def OnSettingsChange( self, event ):
                self._build_notebook()


"""

	SocketServerDialog

"""

class SocketServerDialog( wx.Dialog ):

        def __init__( self, parent, id ):
                wx.Dialog.__init__( self, parent, id, title="SocketServer Setup" )

                self.HostText = wx.StaticText( self, -1, "Host:" )
                self.HostChoice = wx.TextCtrl( self, -1, str( parent.ScoreServer.SocketServer.Host ) )

                self.PortText = wx.StaticText( self, -1, "Port:" )
                self.PortChoice = wx.TextCtrl( self, -1, str( parent.ScoreServer.SocketServer.Port ) )

                self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
                self.OKButton = wx.Button( self, wx.ID_OK, "OK" )

                TopSizer = wx.BoxSizer( wx.VERTICAL )
                HostSizer = wx.BoxSizer( wx.HORIZONTAL )
                PortSizer = wx.BoxSizer( wx.HORIZONTAL )
                BtnSizer = wx.BoxSizer( wx.HORIZONTAL )

                HostSizer.Add( self.HostText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
                HostSizer.Add( self.HostChoice, 2, wx.ALL, 5 )

                PortSizer.Add( self.PortText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
                PortSizer.Add( self.PortChoice, 2, wx.ALL, 5 )

                BtnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
                BtnSizer.Add( self.OKButton, 0, wx.ALL, 5 )

                TopSizer.Add( HostSizer, 0, wx.ALL|wx.CENTER, 5 )
                TopSizer.Add( PortSizer, 0, wx.ALL|wx.CENTER, 5 )
                TopSizer.Add( BtnSizer, 0, wx.ALL|wx.CENTER, 5 )

                self.SetSizer( TopSizer )
                TopSizer.Fit( self )


"""

	TransponderConnectionDialog

"""

class TransponderConnectionDialog( wx.Dialog ):

        def __init__( self, parent, id ):
                wx.Dialog.__init__( self, parent, id, title="Transponder Connection" )
                tl = parent.ScoreServer.TransponderListener

                self.PortText = wx.StaticText( self, -1, "Serial Port:" )
                self.PortChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=self._available_ports() )
                self.PortChoice.SetValue( self._select_port( str( tl.Port ) ) )
                self.BaudText = wx.StaticText( self, -1, "Baud Rate:" )
                self.BaudChoice = wx.TextCtrl( self, -1, str( tl.Baudrate ) )

                self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
                self.OKButton = wx.Button( self, wx.ID_OK, "OK" )

                sizer = wx.BoxSizer( wx.VERTICAL )
                sizer.Add( self._row( self.PortText, self.PortChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                sizer.Add( self._row( self.BaudText, self.BaudChoice ), 0, wx.ALL|wx.EXPAND, 2 )

                btnSizer = wx.BoxSizer( wx.HORIZONTAL )
                btnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
                btnSizer.Add( self.OKButton, 0, wx.ALL, 5 )
                sizer.Add( btnSizer, 0, wx.ALL|wx.CENTER, 5 )

                self.SetSizer( sizer )
                sizer.Fit( self )

        # Returns a list of detected serial port names.
        def _available_ports( self ):
                try:
                        return [ p.device for p in serial.tools.list_ports.comports() ]
                except Exception:
                        return []

        # Picks the port to show in the dropdown: prefer the currently configured
        # port, otherwise the first detected port, otherwise leave it blank.
        def _select_port( self, current ):
                ports = self._available_ports()
                if current in ports:
                        return current
                if ports:
                        return ports[ 0 ]
                return current

        def _row( self, label, ctrl ):
                s = wx.BoxSizer( wx.HORIZONTAL )
                s.Add( label, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
                s.Add( ctrl, 2, wx.ALL, 5 )
                return s


"""

	TransponderConfigDialog

"""

class TransponderConfigDialog( wx.Dialog ):

        def __init__( self, parent, id ):
                wx.Dialog.__init__( self, parent, id, title="Configure Transponder" )

                self.CurrentIDText = wx.StaticText( self, -1, "Current ID:" )
                self.CurrentIDChoice = wx.TextCtrl( self, -1, "1" )
                self.NewIDText = wx.StaticText( self, -1, "New ID:" )
                self.NewIDChoice = wx.TextCtrl( self, -1, "2" )
                self.SetHpText = wx.StaticText( self, -1, "Hit Points:" )
                self.SetHpChoice = wx.TextCtrl( self, -1, "20" )
                self.MatchRulesText = wx.StaticText( self, -1, "Ruleset:" )
                rulesChoices = [ "Default", "Max HP Per Panel", "Healing", "Cooldown Increase" ]
                self.MatchRulesChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=rulesChoices )

                self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
                self.OKButton = wx.Button( self, wx.ID_OK, "OK" )

                sizer = wx.BoxSizer( wx.VERTICAL )
                sizer.Add( self._row( self.CurrentIDText, self.CurrentIDChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                sizer.Add( self._row( self.NewIDText, self.NewIDChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                sizer.Add( self._row( self.SetHpText, self.SetHpChoice ), 0, wx.ALL|wx.EXPAND, 2 )
                sizer.Add( self._row( self.MatchRulesText, self.MatchRulesChoice ), 0, wx.ALL|wx.EXPAND, 2 )

                btnSizer = wx.BoxSizer( wx.HORIZONTAL )
                btnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
                btnSizer.Add( self.OKButton, 0, wx.ALL, 5 )
                sizer.Add( btnSizer, 0, wx.ALL|wx.CENTER, 5 )

                self.SetSizer( sizer )
                sizer.Fit( self )

        def _row( self, label, ctrl ):
                s = wx.BoxSizer( wx.HORIZONTAL )
                s.Add( label, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
                s.Add( ctrl, 2, wx.ALL, 5 )
                return s


TEAM_COLORS = [
        wx.Colour( 210, 60, 60 ),    # red
        wx.Colour( 60, 110, 220 ),   # blue
        wx.Colour( 70, 170, 80 ),    # green
        wx.Colour( 220, 170, 40 ),   # amber
        wx.Colour( 170, 80, 180 ),   # purple
        wx.Colour( 60, 180, 180 ),   # teal
        wx.Colour( 230, 120, 40 ),   # orange
        wx.Colour( 150, 150, 150 ),  # grey
]

class MatchPanel( wx.Panel ):

        def __init__( self, parent, id ):
                wx.Panel.__init__( self, parent )

                self.ScoreServer = parent.ScoreServer
                self.Match = self.ScoreServer.Match
                self.MechList = self.ScoreServer.Match.MechList

                self.Sizer = wx.BoxSizer( wx.VERTICAL )

                # Match timer
                self.MatchTimerText = MatchTimerText( self, -1, self.Match )
                self.MatchTimerText.SetFont( wx.Font( 96, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                self.Sizer.Add( self.MatchTimerText, 0, wx.ALL|wx.ALIGN_CENTER, 6 )

                # Match status
                self.StatusText = wx.StaticText( self, -1, "" )
                self.StatusText.SetFont( wx.Font( 26, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                self.Sizer.Add( self.StatusText, 0, wx.ALL|wx.ALIGN_CENTER, 2 )

                self.Sizer.Add( wx.StaticLine( self ), 0, wx.ALL|wx.EXPAND, 8 )

                # Group mechs by team, preserving match order.
                teams = {}
                order = []
                for m in self.MechList:
                        if m.Team not in teams:
                                teams[m.Team] = []
                                order.append( m.Team )
                        teams[m.Team].append( m )

                self.HPBars = []
                self.MechHPTexts = []

                for idx, t in enumerate( order ):
                        self.Sizer.Add( self._build_team_section( t, teams[t] ), 0, wx.ALL|wx.EXPAND, 6 )
                        if idx < len(order) - 1 and self.Match.MatchType != MWScore.MATCH_FFA:
                                vs = wx.StaticText( self, -1, "VS" )
                                vs.SetFont( wx.Font( 42, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                                self.Sizer.Add( vs, 0, wx.ALL|wx.ALIGN_CENTER, 4 )

                self.SetSizer( self.Sizer )
                self.Sizer.Fit( parent )

        def _build_team_section( self, team, members ):
                box = wx.StaticBox( self, -1, "" )
                box.SetFont( wx.Font( 22, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                sizer = wx.StaticBoxSizer( box, wx.VERTICAL )

                team_name = members[0].TeamName if members[0].TeamName else ( "Team " + str( team ) )
                header = wx.StaticText( self, -1, team_name )
                header.SetFont( wx.Font( 30, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                header.SetForegroundColour( TEAM_COLORS[ ( team - 1 ) % len( TEAM_COLORS ) ] )
                sizer.Add( header, 0, wx.ALL|wx.ALIGN_CENTER, 6 )

                for m in members:
                        row = wx.BoxSizer( wx.HORIZONTAL )

                        name = wx.StaticText( self, -1, m.Name )
                        name.SetFont( wx.Font( 28, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                        name.SetMinSize( ( 220, -1 ) )

                        bar = HPBar( self, m )

                        hp = MechHPText( self, -1, self.ScoreServer, m )
                        hp.SetFont( wx.Font( 28, wx.DEFAULT, wx.NORMAL, wx.BOLD ) )
                        hp.SetMinSize( ( 80, -1 ) )

                        row.Add( name, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 6 )
                        row.Add( bar, 1, wx.ALL|wx.EXPAND, 6 )
                        row.Add( hp, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 6 )
                        sizer.Add( row, 0, wx.ALL|wx.EXPAND, 4 )

                        self.HPBars.append( bar )
                        self.MechHPTexts.append( hp )

                return sizer

        # Refresh the timer, status, HP bars, and all mech HP text.
        def Refresh( self ):
                self.MatchTimerText.Refresh()
                self._refresh_status()

                # OBS overlay files (unchanged behaviour).
                if len( self.MechList ) > 0:
                        self._write_obs( "obs_score_red_hp.txt", self.MechList[0].HP )
                        self._write_obs( "obs_score_red_name.txt", str( self.MechList[0].Name ) )
                        self._write_obs( "obs_score_red_team_name.txt", str( self.MechList[0].TeamName ) )
                if len( self.MechList ) > 1:
                        self._write_obs( "obs_score_blue_hp.txt", self.MechList[1].HP )
                        self._write_obs( "obs_score_blue_name.txt", str( self.MechList[1].Name ) )
                        self._write_obs( "obs_score_blue_team_name.txt", str( self.MechList[1].TeamName ) )

                for bar in self.HPBars:
                        bar.Refresh()
                for hp in self.MechHPTexts:
                        hp.Refresh()

                # Full match data for the OBS HTML overlay.
                self._write_obs_json()

        def _write_obs( self, filename, value ):
                try:
                        f = open( filename, "w" )
                        if isinstance( value, int ):
                                if value > 10:
                                        f.write( str( value ) )
                                else:
                                        f.write( '0' + str( value ) )
                        else:
                                f.write( str( value ) )
                        f.close()
                except Exception:
                        pass

        # Writes a single JSON file with the full match state for the OBS overlay.
        def _write_obs_json( self ):
                data = {
                        "time": self.Match.Time,
                        "match_type": self.Match.MatchType,
                        "status": self._status_string(),
                        "teams": [],
                }
                teams = {}
                order = []
                for m in self.MechList:
                        if m.Team not in teams:
                                teams[m.Team] = []
                                order.append( m.Team )
                        teams[m.Team].append( m )
                for t in order:
                        members = teams[t]
                        data["teams"].append( {
                                "team": t,
                                "name": members[0].TeamName if members[0].TeamName else ( "Team " + str( t ) ),
                                "mechs": [ { "name": m.Name, "hp": m.HP, "maxhp": m.MaxHP } for m in members ],
                        } )
                try:
                        f = open( "obs_score.json", "w" )
                        json.dump( data, f )
                        f.close()
                except Exception:
                        pass

        def _status_string( self ):
                m = self.Match
                if m.MatchOver:
                        return "MATCH OVER"
                if m.SuddenDeath:
                        return "SUDDEN DEATH"
                if m.MatchPaused:
                        return "PAUSED"
                return "RUNNING"

        def _refresh_status( self ):
                m = self.Match
                if m.MatchOver:
                        self.StatusText.SetLabel( "MATCH OVER" )
                        self.StatusText.SetForegroundColour( wx.Colour( 205, 55, 55 ) )
                elif m.SuddenDeath:
                        self.StatusText.SetLabel( "SUDDEN DEATH" )
                        self.StatusText.SetForegroundColour( wx.Colour( 225, 175, 45 ) )
                elif m.MatchPaused:
                        self.StatusText.SetLabel( "PAUSED" )
                        self.StatusText.SetForegroundColour( wx.Colour( 150, 150, 150 ) )
                else:
                        self.StatusText.SetLabel( "RUNNING" )
                        self.StatusText.SetForegroundColour( wx.Colour( 60, 180, 75 ) )


class HPBar( wx.Panel ):

        def __init__( self, parent, mech, size=( 340, 30 ) ):
                wx.Panel.__init__( self, parent )
                self.Mech = mech
                self.lastHP = -1
                self.SetMinSize( size )
                self.Bind( wx.EVT_PAINT, self.OnPaint )
                self.Bind( wx.EVT_ERASE_BACKGROUND, lambda e: None )

        # Repaint only when the mech's HP has actually changed.
        def Refresh( self ):
                if self.Mech.HP != self.lastHP:
                        self.lastHP = self.Mech.HP
                        wx.Panel.Refresh( self )

        def OnPaint( self, event ):
                dc = wx.PaintDC( self )
                w, h = self.GetSize()

                # Track background.
                dc.SetBrush( wx.Brush( wx.Colour( 30, 30, 30 ) ) )
                dc.SetPen( wx.Pen( wx.Colour( 90, 90, 90 ), 1 ) )
                dc.DrawRectangle( 0, 0, w, h )

                # Fill proportional to remaining HP.
                maxhp = float( self.Mech.MaxHP ) if self.Mech.MaxHP > 0 else 1.0
                frac = max( 0.0, min( 1.0, self.Mech.HP / maxhp ) )
                fill_w = int( w * frac )

                if frac > 0.5:
                        col = wx.Colour( 60, 180, 75 )
                elif frac > 0.25:
                        col = wx.Colour( 225, 175, 45 )
                else:
                        col = wx.Colour( 205, 55, 55 )

                dc.SetBrush( wx.Brush( col ) )
                dc.SetPen( wx.Pen( col, 1 ) )
                dc.DrawRectangle( 0, 0, fill_w, h )


class MechHPText( wx.StaticText ):

        def __init__( self, parent, id, server, mech ):
                wx.StaticText.__init__( self, parent )
                self.ScoreServer = server
                self.Mech = mech
                self.Bind( wx.EVT_LEFT_DOWN, self.LeftClick )
                self.Bind( wx.EVT_RIGHT_DOWN, self.RightClick )
                self.oldHP = 99
                self.SetLabel( '--' )

        def Refresh( self ):
                if self.Mech.HP != self.oldHP:
                        self.SetLabel( str( self.Mech.HP ) )
                self.oldHP = self.Mech.HP

        def LeftClick( self, event ):
                if not self.ScoreServer.Match.MatchOver:
                        self.Mech.AssignPenality()
                        self.ScoreServer.Match.UpdateTransponderHP()
                        self.ScoreServer.Log( "Assign Hit Point Penality" )

        def RightClick( self, event ):
                if not self.ScoreServer.Match.MatchOver:
                        self.Mech.ResetHP()
                        self.ScoreServer.Match.UpdateTransponderHP()
                        self.ScoreServer.Log( "Reset HP" )


class MatchTimerText( wx.StaticText ):

        lastSecond = 0

        def __init__( self, parent, id, match ):
                wx.StaticText.__init__( self, parent )
                self.Match = match
                self.Bind( wx.EVT_LEFT_DOWN, self.LeftClick )
                self.Bind( wx.EVT_RIGHT_DOWN, self.RightClick )
                MatchTimerText.lastSecond = 0
                self.SetLabel( '--:--' )

        def Refresh( self ):
                t_time = int( self.Match.Time )
                t_min = int( t_time / 600 )
                t_sec = int( ( t_time - ( t_min * 600 ) ) * .1 )

                if t_sec != MatchTimerText.lastSecond:
                        self.SetLabel( str( t_min ).rjust( 2, "0" ) + ":" + str( t_sec ).rjust( 2, "0" ) )
                        try:
                                f = open( "obs_score_time.txt", "w" )
                                f.write( str( t_min ).rjust( 2, "0" ) + ":" + str( t_sec ).rjust( 2, "0" ) )
                                f.close()
                        except Exception:
                                pass

                MatchTimerText.lastSecond = t_sec

        def LeftClick( self, event ):
                if not self.Match.MatchOver:
                        if self.Match.MatchPaused:
                                self.Match.Start()
                        else:
                                self.Match.Pause()

        def RightClick( self, event ):
                if not self.Match.MatchOver:
                        self.Match.Pause()
                        self.Match.SetTime( int( self.Match.MatchLength ) )


if __name__ == "__main__":
	app = wx.App(0)
	frame = MWScoreFrame()
	app.MainLoop()
