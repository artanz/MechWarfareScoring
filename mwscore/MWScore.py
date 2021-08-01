#!/usr/bin/python

"""
"""

import time
import threading
import serial
import socket
import select
import sys
import operator
import os
import traceback

MATCH_TEAM = 1
MATCH_FFA = 2

"""
        
        ScoreServer

"""

class ScoreServer():

        def __init__( self ):
                
                self.Log( "Mech Warfare MWScore Scoring System v2.0 \n" )
                self.Log( "R-TEAM Version \r\n" )
                
                self.MechList = MechList().CreateFromConfig( "mechs.conf" )             
                defaultPort = "COM3"
                if os.name == 'posix':
                    defaultPort = "/dev/ttyUSB0"
                self.TransponderListener = TransponderListener( self, defaultPort, 38400 )
                self.SocketServer = SocketServer( self, "", 2525)
                self.Match = Match( self, mechs=[self.MechList.List[0], self.MechList.List[1]] )
                
                self.StartAll()
                
        def Log( self, string ):
                print( time.strftime("%I.%M.%S") + ": " + string )
                
        def StartAll( self ):
                self.TransponderListener.StartThread()
                self.SocketServer.StartThread()
                self.Match.StartThread()
                
        def KillAll( self ):
                self.TransponderListener.KillThread()
                self.SocketServer.KillThread()
                self.Match.KillThread()

"""

        ScoreModules

"""

class ScoreModule():

        def __init__( self, server=None ):
                self.ScoreServer = server
                self.Thread = threading.Thread( target=self.Run )
                self.ThreadKill = False
        
        def Setup( self ):
                pass
                
        def Run( self ):
                pass
                
        def StartThread( self ):
                # ( < Python 3.9) if not self.Thread.isAlive():
                if not self.Thread.is_alive():
                        self.Thread.start()
                
        def KillThread( self ):
                self.ThreadKill = True
        
class SocketServer( ScoreModule ):

        def __init__( self, server, host="", port=2525 ):
                ScoreModule.__init__( self, server )
                
                # Log the creation of a new ScoreModule.
                self.ScoreServer.Log( "New SocketServer module attached." )
                
                # module variables
                self.Host = host
                self.Port = port
                self.Socket = None
                self.Clients = []
                
                self.Setup()
        
        # Attempt to setup the socket   
        def Setup( self ):
                self.ScoreServer.Log( "Atempting to setup SocketServer module..." )
                try:
                        self.Socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
                        self.Socket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
                        self.Socket.bind( ( self.Host, self.Port ) )
                        self.Socket.listen( 5 )
                        self.ScoreServer.Log( "SocketServer setup succesful! \r\n" )
                        self.StartThread()
                except Exception as x:
                        traceback.print_exc()
                        self.ScoreServer.Log( "Setup exception! SocketServer not set up. \r\n" )
                        self.Socket = None
        
        # Module's thread.
        def Run( self ):
                while not self.ThreadKill:
                
                        if self.Socket == None:
                                self.ScoreServer.Log("No socket found in socket thread; exiting thread.")
                                time.sleep( 1 )
                                return
                                
                        (sread, swrite, sexc) = select.select( [self.Socket], [], [], 1 )
                        
                        # for each socket with readable data
                        for sock in sread:
                                if sock == self.Socket:
                                        client, address = sock.accept()
                                        self.ScoreServer.Log( "New client connected from " + repr(address) )
                                        client.send( self.ScoreServer.Match.MatchData() + "\n" )
                                        self.Clients.append( client )
        
        # Bradcast a message to all of the servers clients. Removes any clients that produce a socket error.
        def Broadcast( self, msg ):
                for client in self.Clients:
                        try:
                                client.send( msg + "\n" )
                        except:
                                self.ScoreServer.Log( "Disconnecting client " + repr(client.getpeername()) )
                                self.Clients.remove( client )
                                
class SocketClient( ScoreModule ):

        def __init__( self, host="192.168.1.102", port=2525, notify=None ):
                ScoreModule.__init__( self )
                
                self.Host = host
                self.Port = port
                self.Socket = None
                
                self.MatchTime = 7200
                self.MatchType = 1
                self.NumMechs = 2
                self.MechNames = ["Dummy 1", "Dummy 2"]
                self.MechHP = [20, 20]
                self.Notify = notify
                
                self.Setup( host, port )
        
        # Attempt to setup the socket.  
        def Setup( self, host, port ):
                try:
                        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.Socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        self.Socket.connect((host, port))
                        self.StartThread()
                except:
                        print("Could not connect to " + repr(host) + ":" + repr(port) + ": " + repr(sys.exc_info()))
                        self.Socket = None
        
        # Module's Thread
        def Run( self ):
                pack = ""
                while not self.ThreadKill:
                
                        if self.Socket == None:
                                time.sleep( 1 )
                                self.ThreadKill = True
                                print("No Socket in SocketClient()")
                                if self.Notify:
                                        self.Notify(None)
                                return
                                
                        try:
                                data = self.Socket.recv(1024)
                        except:
                                print("Exception in Socket.recv(): " + repr(sys.exc_info()))
                                time.sleep( 1 )
                                self.ThreadKill = True
                                if self.Notify:
                                        self.Notify(None)
                                return
                        pack = pack + data
                        while pack.find('\n') != -1:
                                pieces = pack.split('\n', 1)
                                data = pieces[0]
                                pack = pieces[1]
                                
                                info = data.split( ":" )
                                
                                if (len(info)-3)%3 != 0:
                                        print("Protocol mismatch in SocketClient(): " + data)
                                        self.ThreadKill = True
                                        if self.Notify:
                                                self.Notify(None)
                                        return
                                
                                self.MatchTime = int( info[0] )
                                self.MatchType = int( info[1] )
                                self.NumMechs = int( info[2] )
                        
                                names = []
                                hp = []
                        
                                for m in range( self.NumMechs ):
                                        names.append( info[3+(3*m)] )
                                        hp.append( int(info[4+(3*m)]) )
                                
                                self.MechNames = names
                                self.MechHP = hp
                                if self.Notify:
                                        self.Notify(zip(self.MechNames, self.MechHP))


class TransponderListener( ScoreModule ):

        def __init__( self, server, port="COM2", baud=38400 ):
                ScoreModule.__init__( self, server )
                
                # Log the creation of a new ScoreModule.
                self.ScoreServer.Log( "New TransponderListener module attached." )
                
                # module variables
                self.Port = port
                self.Baudrate = baud
                self.Xbee = None
                
                self.Setup( self.Port, self.Baudrate )
        
        # Attempt to setup Xbee radio.  
        def Setup( self, port, baud ):
                self.ScoreServer.Log( "Atempting to setup TransponderListener module..." )
                try:
                        self.Xbee = serial.Serial( self.Port, self.Baudrate, timeout=1 )
                        self.ScoreServer.Log( " TransponderListener setup succesful on port " + self.Port + " ! \r\n" )
                        self.StartThread()
                        return True
                except Exception as x:
                        self.Xbee = None
                        self.ScoreServer.Log( "Setup exception! TransponderListener not set up. Port " + self.Port + " error " + str(x) + "\r\n" )
                        return False
        
        # Module's thread.
        def Run( self ):
                try:
                    while not self.ThreadKill:
                        
                        # Return if xbee is not setup.
                        if self.Xbee == None:
                                self.ScoreServer.Log(" Xbee not set up -- exiting \r\n");
                                time.sleep( 0.5 )
                                return
                        
                                
                        # Look for the transponder's header byte
                        while True:
                            if self.ThreadKill == True:
                                    return
                            if self.Xbee.inWaiting() == 0:
                                time.sleep(0.01)
                                continue
                            q = self.ReadByte()
                            if (ord(q) != 0x55):
                                self.ScoreServer.Log("Skipping byte %r\r\n" % (ord(q),))
                                continue
                            break
                                
                        # Read packet data.
                        mechidh = ord( self.ReadByte() )
                        mechidl = ord( self.ReadByte() )
                        mechhit = ord( self.ReadByte() )
                        mechhp  = ord( self.ReadByte() )
                        
                        # Check for valid packet and assign hit if valid.
                        if ( mechidh + mechidl ) == 0xff:
                                result = self.ScoreServer.MechList.MechByID(mechidh).AdjustHP(mechhp)
                                self.ScoreServer.Log( result )
                        else:
                                self.ScoreServer.Log( "Failed packet!", mechidl, mechidh )
        
                except Exception as x:
                    traceback.print_exc();
                    print("Exiting Xbee thread")

        # Read a single byte from xbee. Blocks untill byte is read.
        def ReadByte( self ):
                ret = self.Xbee.read()
                return ret

        # Send message to setup transponder on mech
        def WriteTransponder( self, mechid, hp, rules ):
                mechstr1 = mechid
                mechstr2 = 255 - mechid
                hpstr = hp
                rulesstr = rules
                packet = bytearray()
                packet.append( 85 )
                packet.append( mechstr1 )
                packet.append( mechstr2 )
                packet.append( hpstr )
                packet.append( rulesstr )
                self.Xbee.write( packet )
                self.ScoreServer.Log( "Adjust Mech ID " + str(mechid) + " to " + str(hp) + " HP"  )

        # Send message to setup transponder ID on mech
        def WriteTransponderNewID( self, mechid, newmechid ):
                mechstr1 = mechid
                mechstr2 = 255 - mechid
                newmechstr1 = newmechid
                newmechstr2 = 255 - newmechid
                packet = bytearray()
                packet.append( 165 )
                packet.append( mechstr1 )
                packet.append( mechstr2 )
                packet.append( newmechstr1 )
                packet.append( newmechstr2 )
                self.Xbee.write( packet )
                self.ScoreServer.Log( "Adjust Mech ID " + str(mechid) + " to Mech ID" + str(newmechid) )
        
class Match( ScoreModule ):

        def __init__( self, server, matchtype=MATCH_TEAM, matchlength=4800, matchrules=0, mechs=[] ):
                ScoreModule.__init__( self, server )
                
                # Log the creation of a new ScoreModule
                self.ScoreServer.Log( "New Match module attached." )
                
                # module variables
                self.MatchType = matchtype
                self.MatchLength = matchlength
                self.MatchRules = matchrules
                self.MechList = mechs
                self.Time = matchlength
                self.NumTeams = 0
                self.Teams = []
                self.SuddenDeath = False
                self.MatchOver = False
                self.MatchPaused = True
                
                self.Setup( )
        
        # Setup for a new match.
        def Setup( self ):
                self.Teams = []
                self.SuddenDeath = False
                self.MatchOver = False
                self.MatchPaused = True
                
                # Find out how many teams are in the match
                for m in self.MechList:
                        if m.Team > self.NumTeams:
                                self.NumTeams = m.Team
                
                # Create instace of team for each team and append to self.Teams
                for t in range(self.NumTeams):
                        team = []
                        for m in self.ScoreServer.MechList.MechByTeam( t+1 ):
                                team.append( m )
                        self.Teams.append( Team(t, team) )
                        
                self.StartThread()
                
        # Module's thread.
        def Run( self ):
                while not self.ThreadKill:
                
                        # Update time.
                        if not self.MatchPaused:
                                if self.Time <= 0 or self.MatchOver:
                                        pass
                                else:
                                        self.Time -= 1
                        
                        # Check win conditions
                        self.CheckForWin()
                        
                        time.sleep( .1 )
        
        # Resumes match from pause status or starts the module's thread if not already running.
        def Start( self ):

                # Module thread is already alive...
                # ( < Python 3.9) if self.Thread.isAlive():
                if self.Thread.is_alive():
                        
                        # Set mechs in the module's mech list as "InMatch".
                        for m in self.MechList:
                                m.InMatch = True
                        
                        self.MatchPaused = False        
                        self.ScoreServer.Log( "Match resumed." )
                
                # Module thread is not alive...
                else:
                        
                        # Reset all mechs in the server's mechlist as NOT "InMach".
                        for m in range(len(self.ScoreServer.MechList.List)):
                                self.ScoreServer.MechList.List[m].InMatch = False
                        
                        # Set mechs in the module's mech list as "InMatch".
                        for m in self.MechList:
                                m.InMatch = True
                        
                        self.StartThread()
                        self.MatchPaused = False
                        self.ScoreServer.Log( "Match Started." )
        
        # Sets match puase status.              
        def Pause( self ):
                self.MatchPaused = True
                self.ScoreServer.Log( "Match paused." )
                time.sleep( .5 )
                
        # Sets the match time.
        def SetTime( self, time ):
                self.Time = time
                self.ScoreServer.Log( "Match time set. " + str(time) )
                
        # Reset the Match.
        def Reset( self ):
                self.Pause()
                self.SetTime( self.MatchLength )
                for m in self.MechList:
                        m.ResetHP()
                        self.ScoreServer.TransponderListener.WriteTransponder( m.ID, m.HP, self.MatchRules )
                self.ScoreServer.Log( "Match reset." )

        # Reset the HP.
        def ResetHP( self ):
                for m in self.MechList:
                        m.ResetHP()
                        self.ScoreServer.TransponderListener.WriteTransponder( m.ID, m.HP, self.MatchRules )
                self.ScoreServer.Log( "Reset HP." )

        # Reset the HP.
        def UpdateTransponderHP( self ):
                for m in self.MechList:
                        self.ScoreServer.TransponderListener.WriteTransponder( m.ID, m.HP, self.MatchRules )
                self.ScoreServer.Log( "Updated Transponder to Score Server HP." )
                
        # Checks the match for a win condition.
        def CheckForWin( self ):
        
                # Return if match is already over.
                if self.MatchOver == True:
                        return
                
                # Update Teams hp totals
                for t in self.Teams:
                        t.CalcHP()
                
                # If time has expired find the team with the most HP    
                if self.Time <= 0:
                
                        # Sort teams by highest hp to lowest
                        self.Teams = sorted( self.Teams, key=operator.attrgetter("HP") , reverse=True )
                
                        if not self.SuddenDeath:

                                if self.Teams[0].HP == self.Teams[1].HP:
                                        self.SuddenDeath = True
                                        self.ScoreServer.Log( "Match Time up... Tie found... SUDDEN DEATH MODE!" )
                                
                                else:
                                        msg = "Team #" + str(self.Teams[0].Number) + " ( "
                                        for m in self.Teams[0].Roster:
                                                msg += str(m.Name) + " "
                                        msg += ") wins!"
                                        
                                        self.MatchOver == True
                                        self.KillThread()
                                        self.ScoreServer.Log( msg )
                                        return
                
                        else:
                                if self.Teams[0].HP != self.Teams[1].HP:
                                        msg = "Team #" + str(self.Teams[0].Number) + " ( "
                                        for m in self.Teams[0].Roster:
                                                msg += str(m.Name) + " "
                                        msg += ") wins!"
                                        
                                        self.MatchOver == True
                                        self.KillThread()
                                        self.ScoreServer.Log( msg )
                                        return
                
                # Else check if any team has won by KO          
                else:
                        
                        for t1 in self.Teams:
                                othershp = 0
                                for t2 in self.Teams:
                                        if t1.Number != t2.Number:
                                                othershp += t2.HP
                                
                                if othershp == 0:
                                        msg = "Team #" + str(t1.Number) + " ( "
                        
                                        for m in t1.Roster:
                                                msg += str(m.Name) + " "
                                        msg += ") wins!"
                
                                        self.MatchOver == True
                                        self.KillThread()
                                        self.ScoreServer.Log( msg ) 
                                        return
                        
        # Form match data into a semicolon delimted string
        def MatchData( self ):
                
                # MatchTime, MatchType, NumbTeams, NumMechs
                data = str(self.Time) + ":" + str(self.MatchType) + ":" + str(len(self.MechList))
                
                # MechName and MechHP for each mech in the modules MechList
                for m in self.MechList:
                        data += ":" + str(m.Name) + ":" + str(m.HP) + ":" + str(m.Team)
        
                return data

"""

        Mech
        
"""

class Mech():

        def __init__( self, id=0, name="Dummy", hp=20, team=0):
                self.ID = id
                self.Name = name
                self.MaxHP = hp
                self.Team = team
                
                self.HP = self.MaxHP
                self.InMatch = False
                
        def Reset( self ):
                self.Team = 0
                self.InMatch = False
                self.ResetHP()
                
        # Reset the hp of a mech.
        def ResetHP( self ):
                self.HP = self.MaxHP
                return "HP reset on ID# " + str(self.ID) + " " + str(self.Name) + " HP=" + str(self.HP)
                
        # Assigns a penality to a mech.
        def AssignPenality( self, ammount=1 ):
                if self.HP > 0:
                        self.HP -= ammount
                return str(ammount) + " point penalty assigned to # " + str(self.ID) + " " + str(self.Name) + " HP=" + str(self.HP)
        
        # Assigns a hit to a mech.
        def AssignHit( self, ammount=1 ):
                if self.InMatch:
                        if self.HP > 0:
                                self.HP -= ammount
                                return "Hit on #" + str(self.ID) + " " + str(self.Name) + " HP = " + str(self.HP)
                        else:
                                return "Hit (ignored, HP already 0) on #" + str(self.ID) + " " + str(self.Name) + " HP = " + str(self.HP)
                else:
                        return "Hit (ignored, not in match) on # " + str(self.ID) + " " + str(self.Name) + " HP=" + str(self.HP)
        
        # Adjusts a mech's HP.
        def AdjustHP( self, hp ):
                self.HP = hp
                return "HP adjusted on ID# " + str(self.ID) + " " + str(self.Name) + " HP=" + str(self.HP)
                
        def __repr__( self ):
                return repr( (self.ID, self.Name, self.HP) )

"""

        MechList
        
"""

class MechList():
        
        def __init__(self):
                self.List = []
                
        # fill list from a config file.
        def CreateFromConfig( self, configfile ):
                
                # attempt to open the config file.
                try:
                        conf = open( configfile, "r" ).readlines()
                except:
                        return self
                        
                for line in conf:
                
                        # Ignore comments in config file.
                        if line[0] == "#":
                                continue
                        
                        # Attempt to create and instance of mech from the line. 
                        try:
                                info = line.split( ":" )
                                self.List.append( Mech( int(info[0]), info[1], int(info[2]) ) )
                        except:
                                pass
                
                return self
                
        def ResetMechs( self ):
                for m in self.List:
                        m.Reset()
        
        # Fill list from and existing list of mech instances.
        def CreateFromList( self, mechs ):
                self.List = mechs
                return self
        
        # Return insatnce of mech from list with matching id.
        def MechByID( self, id ):
                for m in self.List:
                        if m.ID == id:
                                return m
                return None
                
        # Return instance(s) of mech from list with matching team number.
        def MechByTeam( self, team ):
                tmplist = []
                for m in self.List:
                        if m.Team == team:
                                tmplist.append( m )
                return tmplist
        
        # Return instance of mech from list with matching name.
        def MechByName( self, name ):
                for m in self.List:
                        if m.Name == name:
                                return m
                return None
        
        # Return instance(s) of mech from list that are currently in a match.   
        def MechByInMatch( self ):
                tmplist = []            
                for m in self.InMatch:
                        tmplist.append( m )
                return tmplist
                
"""

        Team
        
"""

class Team:

        def __init__( self, number, roster ):
                self.Number = number
                self.Roster = roster
                self.HP = 0
                
        def CalcHP( self ):
                hp = 0
                for member in self.Roster:
                        hp += member.HP
                self.HP = hp
                return hp
                
        def __repr__( self ):
                return repr( (self.Number, self.Roster, self.HP) )
