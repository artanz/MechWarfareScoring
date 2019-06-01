#!/usr/bin/python

"""
"""

import MWScore
import wx
import cPickle as pickle
import traceback

"""

	MWScoreFrame

"""

class MWScoreFrame( wx.Frame ):

	FRAME_UPDATE_TIMER_ID = wx.NewId()
	ID_QUIT = wx.NewId()
	ID_MATCHSETUP = wx.NewId()
	ID_MATCHSTART = wx.NewId()
	ID_MATCHPAUSE = wx.NewId()
	ID_MATCHRESET = wx.NewId()
	ID_MATCHRESETHP = wx.NewId()
	ID_TRANSPONDERSETUP = wx.NewId()
	ID_SOCKETSETUP = wx.NewId()
	ID_TRANSPONDERVAR = wx.NewId()
	ID_TRANSPONDERHPUPDATE = wx.NewId()

	def __init__( self ):
		wx.Frame.__init__( self, None, wx.ID_ANY, style=wx.DEFAULT_FRAME_STYLE, name="MWScore Server" )
		
		# MWScore ScoreServer.
		self.ScoreServer = MWScore.ScoreServer()
		
		# Menu Bar
		self.MenuBar = wx.MenuBar()
		self.FileMenu = wx.Menu()
		self.TransponderMenu = wx.Menu()
		self.SocketMenu = wx.Menu()
		self.MatchMenu = wx.Menu()
		
		self.FileMenu.Append( self.ID_QUIT, "Quit" )
		self.Bind( wx.EVT_MENU, self.Quit, id=self.ID_QUIT )
		
		self.TransponderMenu.Append( self.ID_TRANSPONDERSETUP, "Setup" )
		self.TransponderMenu.Append( self.ID_TRANSPONDERVAR, "Transponder Variable Setup" )
		self.TransponderMenu.Append( self.ID_TRANSPONDERHPUPDATE, "Refresh Transponder HP" )
		self.Bind( wx.EVT_MENU, self.TransponderSetup, id=self.ID_TRANSPONDERSETUP )
		self.Bind( wx.EVT_MENU, self.TransponderVar, id=self.ID_TRANSPONDERVAR )
		self.Bind( wx.EVT_MENU, self.TransponderHpUpdate, id=self.ID_TRANSPONDERHPUPDATE )
		
		self.SocketMenu.Append( self.ID_SOCKETSETUP, "Setup" )
		self.Bind( wx.EVT_MENU, self.SocketSetup, id=self.ID_SOCKETSETUP )
		
		self.MatchMenu.Append( self.ID_MATCHSETUP, "Setup" )
		self.MatchMenu.Append( self.ID_MATCHSTART, "Start/Resume" )
		self.MatchMenu.Append( self.ID_MATCHPAUSE, "Pause" )
		self.MatchMenu.Append( self.ID_MATCHRESET, "Reset" )
		self.MatchMenu.Append( self.ID_MATCHRESETHP, "Reset HP" )
		self.Bind( wx.EVT_MENU, self.MatchSetup, id=self.ID_MATCHSETUP )
		self.Bind( wx.EVT_MENU, self.MatchStart, id=self.ID_MATCHSTART )
		self.Bind( wx.EVT_MENU, self.MatchPause, id=self.ID_MATCHPAUSE )
		self.Bind( wx.EVT_MENU, self.MatchReset, id=self.ID_MATCHRESET )
		
		self.MenuBar.Append( self.FileMenu, "&File" )
		self.MenuBar.Append( self.MatchMenu, "&Match" )
		self.MenuBar.Append( self.TransponderMenu, "&Transponder" )
		self.MenuBar.Append( self.SocketMenu, "&Socket" )
		
		self.SetMenuBar( self.MenuBar )

	
		# Panel
		self.Panel = MatchPanel( self, -1 )
		
		# Fix for flicker
		self.SetDoubleBuffered(True)
		
		# Frame Update Timer
		self.Timer = wx.Timer( self, self.FRAME_UPDATE_TIMER_ID )
		self.Timer.Start(1000)
		wx.EVT_TIMER( self, self.FRAME_UPDATE_TIMER_ID, self.OnTimer )
		
		self.Show( True )
                self.SetTitle("Mech Warfare Match Score")
			
	# Updates the frames panel and Broadcasts match data to clients
	def OnTimer( self, event ):
		self.Panel.Refresh()
		self.ScoreServer.SocketServer.Broadcast( self.ScoreServer.Match.MatchData() )
		
	# Opens dialog ot configure a new match.
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
                    pass
                data = { "MatchLength":MatchLength, "MatchType":MatchType, "NumTeams":NumTeams, "MatchRuleSet":MatchRuleSet, "MechList":MechList }

		
		dlg = MatchDialog(self, -1, data)
		if dlg.ShowModal() == wx.ID_OK:
			MatchLength = int(dlg.MatchLengthChoice.GetValue()) * 600
			if dlg.MatchTypeChoice.GetValue() == "Team":
				MatchType = MWScore.MATCH_TEAM
			else:
				MatchType = MWScore.MATCH_FFA
                        if dlg.MatchRulesChoice.GetValue() == "Default":
                                MatchRuleSet = 0
                        if dlg.MatchRulesChoice.GetValue() == "Max HP Per Panel":
                                MatchRuleSet = 1
                        if dlg.MatchRulesChoice.GetValue() == "Healing":
                                MatchRuleSet = 2
                        if dlg.MatchRulesChoice.GetValue() == "Cooldown Increase":
                                MatchRuleSet = 3
			NumTeams = int(dlg.NumTeamsChoice.GetValue())
			dlg.Destroy()
		else:
			dlg.Destroy()
			return
                MechList = []
			
		# Reset the Mech List
		self.ScoreServer.MechList.ResetMechs()
		
		if MatchType == MWScore.MATCH_TEAM:
			
			for t in xrange(NumTeams):
				dlg = TeamDialog(self, -1, "Team #" + str(t+1) + " Setup")
			
				if dlg.ShowModal() == wx.ID_OK:
				
					for s in dlg.MechChoice.GetSelections():
						m = self.ScoreServer.MechList.MechByID( int(dlg.MechChoice.GetString(s).split(":")[0]) )
						m.Team = t+1
						MechList.append( m )				
					dlg.Destroy()
				else:
					dlg.Destroy()
					return
					
		else:
		
			dlg = TeamDialog(self, -1, "FFA Mech Selection")
			
			if dlg.ShowModal() == wx.ID_OK:
			
				t=1
			
				for s in dlg.MechChoice.GetSelections():
					m = self.ScoreServer.MechList.MechByID( int(dlg.MechChoice.GetString(s).split(":")[0]) )
					m.Team = t
					MechList.append( m )
					t += 1
				
				dlg.Destroy()
			
			else:
				dlg.Destroy()
				return

                data = { "MatchLength":MatchLength, "MatchType":MatchType, "NumTeams":NumTeams, "MatchRuleSet":MatchRuleSet, "MechList":MechList }
                f = open("last-match.pkl", "wb")
                pickle.dump(data, f)
                f.close()

		# Stop the frame update timer and current match thread.
		self.Timer.Stop()
		self.ScoreServer.Match.KillThread()
		
		# Create the new match.
		self.ScoreServer.Match = MWScore.Match( self.ScoreServer, MatchType, MatchLength, MatchRuleSet, MechList )
		
		# Destroy and recreate a new match panel.
		self.Panel.Destroy()
		self.Panel = MatchPanel( self, -1 )
		
		# Resume the frame update timer.
		self.Timer.Start()
		
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
            except Exception as x:
                traceback.print_exc()
                wx.MessageBox("Exception in Reset:\r\n" + str(x), "Error", wx.OK | wx.ICON_ERROR);

        # Reset the match
	def MatchResetHP( self, event ):
            try:
		self.ScoreServer.Match.ResetHP()
            except Exception as x:
                traceback.print_exc()
                wx.MessageBox("Exception in Reset:\r\n" + str(x), "Error", wx.OK | wx.ICON_ERROR);
		
	# Opens dialog to configure to ScoreServer's SocketServer
	def SocketSetup( self, event ):
		dlg = SocketServerDialog( self, -1 )
		if dlg.ShowModal() == wx.ID_OK:
			self.ScoreServer.SocketServer.KillThread()
			self.ScoreServer.SocketServer = MWScore.SocketServer( self.ScoreServer, dlg.HostChoice.GetValue(), int(dlg.PortChoice.GetValue()) )
		dlg.Destroy()		
	
	# Opens dialog to configure to ScoreServer's TransponderListener
	def TransponderSetup( self, event ):
		dlg = TransponderDialog( self, -1 )
		if dlg.ShowModal() == wx.ID_OK:
			self.ScoreServer.TransponderListener.KillThread()
			self.ScoreServer.TransponderListener = MWScore.TransponderListener( self.ScoreServer, dlg.PortChoice.GetValue(), int(dlg.BaudChoice.GetValue()) )
                        if not self.ScoreServer.TransponderListener.Xbee:
                            wx.MessageBox("Could not open Transponder port " + ScoreServer.TransponderListener.Port,
                                    "Error", wx.OK | wx.ICON_ERROR)
		dlg.Destroy()

        # Opens dialog to configure Transponder variables
        # Only works with 2018 Transponders
	def TransponderVar( self, event ):
		dlg = TransponderVarDialog( self, -1 )
		if dlg.ShowModal() == wx.ID_OK:
                        if dlg.MatchRulesChoice.GetValue() == "Default":
                                MatchRuleSet = 0
                        if dlg.MatchRulesChoice.GetValue() == "Max HP Per Panel":
                                MatchRuleSet = 1
                        if dlg.MatchRulesChoice.GetValue() == "Healing":
                                MatchRuleSet = 2
                        if dlg.MatchRulesChoice.GetValue() == "Cooldown Increase":
                                MatchRuleSet = 3
                        self.ScoreServer.TransponderListener.WriteTransponderNewID( int(dlg.CurrentIDChoice.GetValue()), int(dlg.NewIDChoice.GetValue()) )
                        self.ScoreServer.TransponderListener.WriteTransponder( int(dlg.NewIDChoice.GetValue()), int(dlg.SetHpChoice.GetValue()), MatchRuleSet )
                        if not self.ScoreServer.TransponderListener.Xbee:
                            wx.MessageBox("Could not open Transponder port " + dlg.PortChoice.GetValue(),
                                    "Error", wx.OK | wx.ICON_ERROR)
                dlg.Destroy()

        # Reset the match
	def TransponderHpUpdate( self, event ):
            try:
		self.ScoreServer.Match.UpdateTransponderHP()
            except Exception as x:
                traceback.print_exc()
                wx.MessageBox("Exception in Transmit HP:\r\n" + str(x), "Error", wx.OK | wx.ICON_ERROR);
		
	# Kills all threads and closes the program
	def Quit( self, event ):
		self.ScoreServer.KillAll()
		self.Close()

"""

	MatchDialog

"""
		
class MatchDialog( wx.Dialog ):

	def __init__( self, parent, id, data ):
                print repr(data)
		wx.Dialog.__init__( self, parent, id, title="New Match Setup" )
		
		self.MatchLengthText = wx.StaticText( self, -1, "Match Length:" )
		self.MatchLengthChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20"] )
                if data.get("MatchLength", None) is not None:
                    self.MatchLengthChoice.SetValue(str(data.get("MatchLength", 0)/600))
		  
		self.MatchTypeText = wx.StaticText( self, -1, "Match Type:" )
                typeChoices = ["Team", "Free For All"]
		self.MatchTypeChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=typeChoices )
                if data.get("MatchType", None) is not None:
                    self.MatchTypeChoice.SetValue(typeChoices[data.get("MatchType", 1)-1])
		
		self.NumTeamsText = wx.StaticText( self, -1, "Number Of Teams: " )
		self.NumTeamsChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=["2","3","4","5","6","7","8","9","10"] )
                if data.get("NumTeams", None) is not None:
                    self.NumTeamsChoice.SetValue(str(data.get("NumTeams", 0)))

		self.MatchRulesText = wx.StaticText( self, -1, "Ruleset: " )
                rulesChoices = ["Default","Max HP Per Panel","Healing","Cooldown Increase"]
		self.MatchRulesChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=rulesChoices )
                if data.get("MatchRuleSet", None) is not None:
                    self.MatchRulesChoice.SetValue(str(rulesChoices[data.get("MatchRuleSet", 0)]))
	
		self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
		self.OKButton = wx.Button( self, wx.ID_OK, "OK" )
		
		TopSizer = wx.BoxSizer( wx.VERTICAL )
		MatchLengthSizer = wx.BoxSizer( wx.HORIZONTAL )
		MatchTypeSizer = wx.BoxSizer( wx.HORIZONTAL )
		NumTeamsSizer = wx.BoxSizer( wx.HORIZONTAL )
		MatchRulesSizer = wx.BoxSizer( wx.HORIZONTAL )
		BtnSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		MatchLengthSizer.Add( self.MatchLengthText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		MatchLengthSizer.Add( self.MatchLengthChoice, 2, wx.ALL, 5 )
		
		MatchTypeSizer.Add( self.MatchTypeText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		MatchTypeSizer.Add( self.MatchTypeChoice, 2, wx.ALL, 5 )
		
		NumTeamsSizer.Add( self.NumTeamsText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		NumTeamsSizer.Add( self.NumTeamsChoice, 2, wx.ALL, 5 )

		MatchRulesSizer.Add( self.MatchRulesText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		MatchRulesSizer.Add( self.MatchRulesChoice, 2, wx.ALL, 5 )
		
		BtnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
		BtnSizer.Add( self.OKButton, 0, wx.ALL, 5 )
		
		TopSizer.Add( MatchLengthSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( MatchTypeSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( NumTeamsSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( MatchRulesSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( BtnSizer, 0, wx.ALL|wx.CENTER, 5 )
		
		self.SetSizer( TopSizer )
		TopSizer.Fit( self )
	
"""

	TeamDialog

"""
	
class TeamDialog( wx.Dialog ):
	
	def __init__( self, parent, id, titlemsg ):
		wx.Dialog.__init__( self, parent, id, title=titlemsg )
		
		MechList = []
		for m in parent.ScoreServer.MechList.List:
			MechList.append( str(m.ID) + ": " + str(m.Name) )
			
		self.MechText = wx.StaticText( self, -1, "Mech Selection:" )
		self.MechChoice = wx.ListBox( self, -1, style=wx.LB_EXTENDED, choices=MechList )			
		self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
		self.OKButton = wx.Button( self, wx.ID_OK, "OK" )
		
		TopSizer = wx.BoxSizer( wx.VERTICAL )
		BtnSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		BtnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
		BtnSizer.Add( self.OKButton, 0, wx.ALL, 5 )
		
		TopSizer.Add( self.MechText, 0, wx.ALL, 5 )
		TopSizer.Add( self.MechChoice, 0, wx.ALL, 5 )
		TopSizer.Add( BtnSizer, 0, wx.ALL|wx.CENTER, 5 )
		
		self.SetSizer( TopSizer )
		TopSizer.Fit( self )


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

	TransponderDialog

"""
	
class TransponderDialog( wx.Dialog ):
	
	def __init__( self, parent, id ):
		wx.Dialog.__init__( self, parent, id, title="TransponderListener Setup" )
		  
		self.PortText = wx.StaticText( self, -1, "Port:" )
		self.PortChoice = wx.TextCtrl( self, -1, str( parent.ScoreServer.TransponderListener.Port ) )
	
		self.BaudText = wx.StaticText( self, -1, "Host:" )
		self.BaudChoice = wx.TextCtrl( self, -1, str( parent.ScoreServer.TransponderListener.Baudrate ) )
	
		self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
		self.OKButton = wx.Button( self, wx.ID_OK, "OK" )
		
		TopSizer = wx.BoxSizer( wx.VERTICAL )
		BaudSizer = wx.BoxSizer( wx.HORIZONTAL )
		PortSizer = wx.BoxSizer( wx.HORIZONTAL )
		BtnSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		PortSizer.Add( self.PortText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		PortSizer.Add( self.PortChoice, 2, wx.ALL, 5 )
		
		BaudSizer.Add( self.BaudText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		BaudSizer.Add( self.BaudChoice, 2, wx.ALL, 5 )
		
		BtnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
		BtnSizer.Add( self.OKButton, 0, wx.ALL, 5 )
		
		TopSizer.Add( PortSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( BaudSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( BtnSizer, 0, wx.ALL|wx.CENTER, 5 )
		
		self.SetSizer( TopSizer )
		TopSizer.Fit( self )

"""

	TransponderVarDialog

"""
	
class TransponderVarDialog( wx.Dialog ):
	
	def __init__( self, parent, id ):
		wx.Dialog.__init__( self, parent, id, title="Transponder Variable Setup" )
		  
		self.CurrentIDText = wx.StaticText( self, -1, "Current ID:" )
		self.CurrentIDChoice = wx.TextCtrl( self, -1, "1" )

		self.NewIDText = wx.StaticText( self, -1, "New ID:" )
		self.NewIDChoice = wx.TextCtrl( self, -1, "2" )
	
		self.SetHpText = wx.StaticText( self, -1, "Hit Points:" )
		self.SetHpChoice = wx.TextCtrl( self, -1, "20" )

		self.MatchRulesText = wx.StaticText( self, -1, "Ruleset: " )
                rulesChoices = ["Default","Max HP Per Panel","Healing","Cooldown Increase"]
		self.MatchRulesChoice = wx.ComboBox( self, -1, style=wx.CB_DROPDOWN, choices=rulesChoices )
	
		self.CancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
		self.OKButton = wx.Button( self, wx.ID_OK, "OK" )
		
		TopSizer = wx.BoxSizer( wx.VERTICAL )
		CurrentIDSizer = wx.BoxSizer( wx.HORIZONTAL )
		NewIDSizer = wx.BoxSizer( wx.HORIZONTAL )
		SetHpSizer = wx.BoxSizer( wx.HORIZONTAL )
		RuleSizer = wx.BoxSizer( wx.HORIZONTAL )
		BtnSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		CurrentIDSizer.Add( self.CurrentIDText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		CurrentIDSizer.Add( self.CurrentIDChoice, 2, wx.ALL, 5 )

		NewIDSizer.Add( self.NewIDText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		NewIDSizer.Add( self.NewIDChoice, 2, wx.ALL, 5 )
		
		SetHpSizer.Add( self.SetHpText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		SetHpSizer.Add( self.SetHpChoice, 2, wx.ALL, 5 )

		RuleSizer.Add( self.MatchRulesText, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )
		RuleSizer.Add( self.MatchRulesChoice, 2, wx.ALL, 5 )
		
		BtnSizer.Add( self.CancelButton, 0, wx.ALL, 5 )
		BtnSizer.Add( self.OKButton, 0, wx.ALL, 5 )
		
		TopSizer.Add( CurrentIDSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( NewIDSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( SetHpSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( RuleSizer, 0, wx.ALL|wx.CENTER, 5 )
		TopSizer.Add( BtnSizer, 0, wx.ALL|wx.CENTER, 5 )
		
		self.SetSizer( TopSizer )
		TopSizer.Fit( self )
		
"""

	MatchPanel

"""
		
class MatchPanel( wx.Panel ):

	def __init__( self, parent, id ):
		wx.Panel.__init__( self, parent )
		
		self.ScoreServer = parent.ScoreServer
		self.Match = self.ScoreServer.Match
		self.MechList = self.ScoreServer.Match.MechList
		
		# Create a MatchTimeText
		self.MatchTimerText = MatchTimerText( self, -1, self.Match )
		self.MatchTimerText.SetFont(wx.Font(80, wx.DEFAULT, wx.NORMAL, wx.BOLD))
		
		# Create a Sizer, NameText, and HPText for each Mech in the match.
		self.MechSizer = []
		self.MechNameText = []
		self.MechHPText = []
		
		for m in xrange(len(self.MechList)):
			self.MechSizer.append( wx.BoxSizer( wx.HORIZONTAL ) )
			self.MechNameText.append( wx.StaticText( self, -1, self.MechList[m].Name ) )
			self.MechHPText.append( MechHPText( self, -1, self.ScoreServer, self.MechList[m] ) )
			
			self.MechNameText[m].SetFont(wx.Font(72, wx.DEFAULT, wx.NORMAL, wx.BOLD))
			self.MechHPText[m].SetFont(wx.Font(72, wx.DEFAULT, wx.NORMAL, wx.BOLD))
		
		# Create an overall sizer for the panel.
		self.Sizer = wx.BoxSizer( wx.VERTICAL )
		
		# Add TimerText to the panel's sizer.
		self.Sizer.Add( self.MatchTimerText, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=10 )
		self.Sizer.Add( wx.StaticLine( self ), 0, wx.ALL|wx.EXPAND, 5 )
		
		# Add all Mech Sizers to the panel's sizer
		for m in xrange(len(self.MechList)):
		
			# Insert a "VS" static text between teams if this is not a FFA match.
			if self.Match.MatchType != MWScore.MATCH_FFA:
				if self.MechList[m].Team != self.MechList[m-1].Team and m != 0:
					vstext = wx.StaticText(self, -1, "VS")
					vstext.SetFont(wx.Font(50, wx.DEFAULT, wx.NORMAL, wx.BOLD))
					self.Sizer.Add( vstext, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=10 )
					
			self.MechSizer[m].Add( self.MechNameText[m], proportion=0, flag=wx.RIGHT, border=10 )
			self.MechSizer[m].Add( self.MechHPText[m], proportion=0, flag=wx.LEFT, border=10 )
		
			self.Sizer.Add( self.MechSizer[m], proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=10 )
			
		# Set panel's sizer and fit.
		self.SetSizer( self.Sizer )
		self.Sizer.Fit( parent )
	
	# Refresh the TimeText and all instances of MechHPText
	def Refresh( self ):
	
		self.MatchTimerText.Refresh()
		
		for m in self.MechHPText:
			m.Refresh()
			
"""

	MechHPText
	
"""

class MechHPText( wx.StaticText ):

	oldHP = 999

	def __init__( self, parent, id, server, mech ):
		wx.StaticText.__init__( self, parent )
		
		self.ScoreServer = server
		self.Mech = mech
		self.Bind( wx.EVT_LEFT_DOWN, self.LeftClick )
		self.Bind( wx.EVT_RIGHT_DOWN, self.RightClick )
		self.oldHP = 99;
		self.SetLabel( '--' )
	
	def Refresh( self ):
		if self.Mech.HP != MechHPText.oldHP:
			self.SetLabel( str(self.Mech.HP) )
		else:
			pass
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

"""

	MatchTimerText
	
"""

class MatchTimerText( wx.StaticText ):

	lastSecond = 0

	def __init__( self, parent, id, match ):
			wx.StaticText.__init__( self, parent )
			
			self.Match = match
			self.Bind( wx.EVT_LEFT_DOWN, self.LeftClick )
			self.Bind( wx.EVT_RIGHT_DOWN, self.RightClick )
			MatchTimerText.lastSecond = 0
			self.SetLabel('--:--')
			
	def Refresh( self ):
		time = self.Match.Time
		min = time / 600
		sec = int((time -(min * 600)) * .1)
		#mic = time - (min * 600) - (sec * 10)
		
		# If the match time (seconds) has changed since the last refresh update the string
		if sec != MatchTimerText.lastSecond:
			self.SetLabel( str(min).rjust(2,"0") + ":" + str(sec).rjust(2,"0")) # + ":" + str(mic) )
		else:
			pass
		
		MatchTimerText.lastSecond = sec
		
	def LeftClick( self, event ):
		if not self.Match.MatchOver:
			if self.Match.MatchPaused:
				self.Match.Start()
			else:
				self.Match.Pause()
		
	def RightClick( self, event ):
		if not self.Match.MatchOver:
			self.Match.Pause()
			self.Match.SetTime( self.Match.MatchLength )
			
				
if __name__ == "__main__":
	app = wx.App(0)
	frame = MWScoreFrame()
	app.MainLoop()
