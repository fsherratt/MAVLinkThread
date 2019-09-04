# ------------------------------------------------------------------------------
# mavThreadAbstract.py
# A lightweight python abstraction layer for threading autogenerated MAVLink
# libraries. Provides a non-blocking queue system for outgoing messages and
# fully user defined incoming message behaviour. Build in supports for serial
# and socket connections with easy extensibility fo addition mechanisms.
#
# Author: Freddie Sherratt
# ------------------------------------------------------------------------------

import time
import threading
import traceback
import abc
import sys

if sys.version_info.major == 3:
    import queue
else:
    import Queue as queue

from .commAbstract import commAbstract

# ------------------------------------------------------------------------------
# MAVAbstract
# Abstraction class for MAVLink serial communications, implements loop for
# threaded activity, write queue to allow multiple threads to push out
# mavlink data. The communication channel setup must be overloaded to set up
# a channel that inherits from commAbstract
# ------------------------------------------------------------------------------
class mavThread:
    __metaclass__ = abc.ABCMeta
    # --------------------------------------------------------------------------
    # Public function definitions
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # __init__
    # MAVAbstract initializer, sets up all components required for MAVLink
    # communication except the communication channel. Once set up the serial
    # communication will only occur once the R/W loop is started using
    # startRWLoop
    # shortHand - Name to store port under in the portDict
    # param readQueue - queue object to write read messages to
    # param sysid - MAVLink system ID default 78
    # param cmpid - MAVLink component ID
    # return void
    # --------------------------------------------------------------------------
    def __init__( self, conn, mavLib):
        
        if isinstance( conn, commAbstract ):
            self._ser = conn
        else:
            raise Exception( 'Conn must be of type `commAbstract`' )

        self._mavLib = mavLib

        self.loopPauseSleepTime = 0.5
        self.noRWSleepTime = 0.1
        self._seq = 0

        self._writeQueue = queue.PriorityQueue()

        self._intentionallyExit = False
        
        try:
            self._mavObj = self._mavLib.MAVLink( file = self._ser, srcSystem = 20, srcComponent = 1 )
        except:
            raise Exception( 'Unable to create mavlink interface' )

    # --------------------------------------------------------------------------
    # srcSystem (getter)
    # Retrieve MAVLink system ID
    # param null
    # returns mavlink system id
    # --------------------------------------------------------------------------
    @property
    def srcSystem( self ):
        return self._mavObj.srcSystem

    @srcSystem.setter
    def srcSystem(self, sysid ):
        self._mavObj.srcSystem = sysid

    # --------------------------------------------------------------------------
    # srcComponent (getter)
    # Retrieve MAVLink component ID
    # param null
    # returns mavlink component id
    # --------------------------------------------------------------------------
    @property
    def srcComponent( self ):
        return self._mavObj.srcComponent

    @srcComponent.setter
    def srcComponent(self, cmpid):
        self._mavObj.srcComponent = cmpid

    # --------------------------------------------------------------------------
    # stopRWLoop
    # Stops the serial R/W loop by setting _intentionallyExit to True. Stopping 
    # the serial loop does not close the serial port
    # param null
    # return void
    # --------------------------------------------------------------------------
    def stopLoop( self ):
        self._intentionallyExit = True

    # --------------------------------------------------------------------------
    # queueOutputMsg
    # Add mavlink messages to writing queue, does not accept messages when
    # RW loop is paused.
    # param: msg - mavlink message to add to the queue
    # param: priority - message priority, specify priority of message. A higher
    # number gives a higher priority. (default 5)
    # return: boolean True if successful, false otherwise, exception if an error
    # --------------------------------------------------------------------------
    def queueOutputMsg( self, msg, priority = 5 ):
        if not isinstance( msg, self._mavLib.MAVLink_message ):
           return False

        self._writeQueue.put( (priority, self._seq, msg) )
        self._seq += 1

        return True

    # --------------------------------------------------------------------------
    # loop
    # Mavlink serial reading and writing loop. The loop is controlled through
    # calls to startRWLoop, pauseRWLoop and stopRWLoop. by default the
    # loop starts in a paused state.
    # param null
    # return void
    # --------------------------------------------------------------------------
    def loop(self):
        self._intentionallyExit = False

        if not self._ser.isOpen():
            self._ser.openPort()

        self._ser.flush()

        while not self._intentionallyExit:
            try:
                
                self._loopInternals()

            except KeyboardInterrupt:
                break

            except Exception:
                traceback.print_exc(file=sys.stdout)
                raise Exception('MAVLink thread exited unexpectedly')

        print('MAVLink thread closed')

    # --------------------------------------------------------------------------
    # Private function definitions
    # --------------------------------------------------------------------------

    def _loopInternals( self ):
        rMsg = self._readMsg()
        wMsg = self._getWriteMsg()

        if rMsg is None and wMsg is None:
            time.sleep( self.noRWSleepTime)
            return

        if rMsg is not None:
            self._processReadMsg(rMsg)

        if wMsg is not None:
            self._writeMsg(wMsg)

    # --------------------------------------------------------------------------
    # _processReadMsg
    # This function receives incoming mavlink messages once they are parsed
    # self and a timestamp
    # param msg - mavlink message object
    # return - void
    # --------------------------------------------------------------------------
    @abc.abstractmethod
    def _processReadMsg( self, msgList ):
        raise NotImplementedError('_processReadMsg is not implemented')

    # --------------------------------------------------------------------------
    # _getWriteMsg
    # Returns the next item in the writing message queue
    # param null
    # return - MAVLink_message object from queue, None if queue empty,
    # Exception if an error occurs
    # --------------------------------------------------------------------------
    def _getWriteMsg(self):
        try:
            msg = self._writeQueue.get_nowait()
            return msg[2]
        except queue.Empty:
            return None

    # --------------------------------------------------------------------------
    # _writeMsg
    # Writes mavlink messages out as a bit stream on port associated with class
    # param msg - message to write out
    # return - True if msg written, Exception if an error occurs,
    # False otherwise
    # --------------------------------------------------------------------------
    def _writeMsg( self, msg ):
        if msg is None:
            return False

        try:
            msg.pack( self._mavObj )
            b = msg.get_msgbuf()

            self._ser.write( b )

            self._writeQueue.task_done()

            return True

        except queue.Empty:
            pass

        except self._mavLib.MAVError as e:
            print(e)

        return False

    # --------------------------------------------------------------------------
    # _readMsg
    # read the next available mavlink message in the serial buffer
    # param null
    # return - List of MAVLink_message objects parsed from serial, None if
    # buffer empty, Exception if an error occurs
    # --------------------------------------------------------------------------
    def _readMsg( self ):
        mList = []

        while True:
            try:
                x = self._ser.read()
                if x == b'':
                    break

                msg = self._mavObj.parse_buffer(x)

                if len(msg) > 0:
                    mList.extend( msg )
                
            except self._mavLib.MAVError as e:
                print(e)

        return mList

# ------------------------------------ EOF -------------------------------------
