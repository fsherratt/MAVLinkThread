# ------------------------------------------------------------------------------
# serial.py
# Abstraction of socket port communication for use with a mavThreadAbstract 
# object
#
# Author: Freddie Sherratt
# ------------------------------------------------------------------------------

import threading
import socket
import traceback
from .commAbstract import commAbstract
import select
import time
import sys
import warnings

class mavSocket( commAbstract ):
    # --------------------------------------------------------------------------
    # __init__
    # initialise serialClass object, does not start the serial port. Call
    # openPort once object is initialised to start serial communication.
    # param listenPort - UDP socket listen port
    # param listenAddress - UDP socket listen address
    # param broadcastPort - UDP socket broadcast port - if None incoming address is used
    # param broadcastAddress - UDP socket broadcast address
    # param readTimeout - UDP socket read timeout
    # param buffSize - listen UDP socket buffer size

    # return void
    # --------------------------------------------------------------------------
    def __init__( self, listenAddress = None, broadcastAddress = None ):
        self._sRead = None
        self._sWrite = None

        self.buffSize = 65535
        self.AF_type = socket.AF_INET
        self.SOCK_type = socket.SOCK_DGRAM

        if listenAddress is None and broadcastAddress is None:
            raise Exception('A address for either listen, broadcast or both is required')

        self._readAddress = listenAddress
        self._writeAddress = broadcastAddress

        self._writeLock = threading.Lock()
        self._readLock = threading.Lock()

        self._rConnected = False
        self._wConnected = False

    # --------------------------------------------------------------------------
    # set_INET_type
    # Change from default AF type
    # param afType - afType either AF_INET, AF_INET6, AF_UNIX
    # return raises an exception if there is an error
    # --------------------------------------------------------------------------
    def set_AF_type(self, afType):
        self.AF_type = afType

    # --------------------------------------------------------------------------
    # set_INET_type
    # Change from default AF type
    # param afType - afType either SOCK_STREAM or SOCK_DGRAM
    # return raises an exception if there is an error
    # --------------------------------------------------------------------------
    def set_SOCK_type(self, sockType):
        self.SOCK_type = sockType

    # --------------------------------------------------------------------------
    # openPort
    # Open the socket connections specified during __init__
    # param null
    # return raises an exception if there is an error
    # --------------------------------------------------------------------------
    def openPort( self ):
        self._sRead = socket.socket( self.AF_type, self.SOCK_type, )
        self._sRead.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self._sRead.setblocking(0)

        self._sWrite = socket.socket( self.AF_type, self.SOCK_type )
        self._sWrite.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self._sWrite.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
        self._sWrite.setblocking(0)

        self.set_close_on_exec(self._sRead.fileno())
        self.set_close_on_exec(self._sWrite.fileno())

        if self._writeAddress is not None:
            self._openWritePort()

        if self._readAddress is not None:
            self._openReadPort() 

    # --------------------------------------------------------------------------
    # _openReadPort
    # Open read port
    # param addr - read address to bind to
    # return void
    # --------------------------------------------------------------------------
    def _openReadPort(self):
        self._sRead.bind( self._readAddress )
        self._rConnected = True

    # --------------------------------------------------------------------------
    # _openWritePort
    # Open write port
    # param addr - write address to connect to
    # return void
    # --------------------------------------------------------------------------
    def _openWritePort(self):
        self._sWrite.connect( self._writeAddress )

        # Read port can be deterimened after write connection
        if self._readAddress is None:
            self._readAddress = self._sWrite.getsockname()

        self._wConnected = True

    # --------------------------------------------------------------------------
    # closePort
    # Close the socket connection port if it is open
    # param null
    # return void
    # --------------------------------------------------------------------------
    def closePort( self ):
        try:
            self._sRead.close()
            self._sRead.shutdown()
        except:
            pass
        
        try:
            self._sWrite.close()
            self._sWrite.shutdown()
        except:
            pass

        self._rConnected = False
        self._wConnected = False

    # --------------------------------------------------------------------------
    # read
    # Thread safe operation, it reads data in from the socket connection
    # param none
    # return tuple of (data, (recieved address)) for each message in buffer
    # --------------------------------------------------------------------------
    def read( self, b = 0 ):
        if self._readAddress is None:
            warnings.warn('Read port not open - message discarded', UserWarning, stacklevel=3)
            return
        elif not self._rConnected:
            self._openReadPort()

        self._readLock.acquire()

        try:
            m, addr = self._sRead.recvfrom( self.buffSize )

            if self._writeAddress is None:
                self._writeAddress = addr

        except(socket.timeout, BlockingIOError):
            m =  b''

        finally:
            self._readLock.release()

        return m

    # --------------------------------------------------------------------------
    # write
    # Thread safe operation, it writes byte string data out the socket
    # connection
    # param b - byte string to write
    # return raises an Exception if there is an error
    # --------------------------------------------------------------------------
    def write( self, b ):
        if self._writeAddress is None:
            warnings.warn('Write port not open - message discarded', UserWarning, stacklevel=3)
            return
        elif not self._wConnected:
            self._openWritePort()

        self._writeLock.acquire()

        try:
            self._sWrite.send(b)
            
        except Exception:
            traceback.print_exc(file=sys.stdout)

        finally:
            self._writeLock.release()

    # --------------------------------------------------------------------------
    # isOpen
    # Check is socket port has been intentionally closed
    # param null
    # return void
    # --------------------------------------------------------------------------
    def isOpen( self ):
        return self._rConnected and self._wConnected

    # --------------------------------------------------------------------------
    # dataAvailable
    # Check is socket data is available
    # param null
    # return True if data available to read, False otherwise
    # --------------------------------------------------------------------------
    def dataAvailable( self ):
        return False

    # --------------------------------------------------------------------------
    # flush
    # Not possible to flush a socket connection so this is left blank
    # param null
    # return void
    # --------------------------------------------------------------------------
    def flush( self ):
        # Probably need a limit to prevent an infinite loop
        while self.read() != b'':
            pass

    def set_close_on_exec(self, fd):
        try:
            import fcntl
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(fd, fcntl.F_SETFD, flags)
        except:
            pass
# ------------------------------------ EOF -------------------------------------
