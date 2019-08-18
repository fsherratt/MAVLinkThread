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

class mavSocket( commAbstract ):
    # --------------------------------------------------------------------------
    # __init__
    # initialise serialClass object, does not start the serial port. Call
    # openPort once object is initialised to start serial communication.
    # param broadcastPort - UDP socket broadcast port
    # param broadcastAddress - UDP socket broadcast address
    # param listenPort - UDP socket listen port
    # param listenAddress - UDP socket listen address
    # param readTimeout - UDP socket read timeout
    # param buffSize - listen UDP socket buffer size

    # return void
    # --------------------------------------------------------------------------
    def __init__( self, port, listenAddress = '', buffSize = 65535, ):
        
        self._sRead = None
        self._sWrite = None

        self.buffSize = buffSize

        self._readAddress = (socket.gethostbyname(listenAddress), int(port))
        self._writeAddress = None

        self._writeLock = threading.Lock()
        self._readLock = threading.Lock()

        self._connected = False

    # --------------------------------------------------------------------------
    # openPort
    # Open the socket connections specified during __init__
    # param null
    # return raises an exception if there is an error
    # --------------------------------------------------------------------------
    def openPort( self ):
        self._sRead = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self._sRead.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self._sRead.setblocking(0)

        self._sWrite = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self._sWrite.setsockopt( socket.SOL_SOCKET, socket.SO_BROADCAST, 1 )
        self._sWrite.setblocking(0)
        
        self._sRead.bind( self._readAddress )
        self.set_close_on_exec(self._sRead.fileno())  

    # --------------------------------------------------------------------------
    # _openWritePort
    # Once we have a write address we can make a connection
    # param addr - 2-tuple of address and port
    # return null
    # --------------------------------------------------------------------------
    def _openWritePort(self, addr):
        self._writeAddress = addr

        self._sWrite.connect( self._writeAddress )
        self.set_close_on_exec(self._sWrite.fileno())

        self._connected = True

    # --------------------------------------------------------------------------
    # closePort
    # Close the socket connection port if it is open
    # param null
    # return void
    # --------------------------------------------------------------------------
    def closePort( self ):
        self._connected = False

        self._sRead.close()
        self._sWrite.close()

    # --------------------------------------------------------------------------
    # read
    # Thread safe operation, it reads data in from the socket connection
    # param none
    # return tuple of (data, (recieved address)) for each message in buffer
    # --------------------------------------------------------------------------
    def read( self, b = 0 ):
        self._readLock.acquire()

        try:
            m, addr = self._sRead.recvfrom( self.buffSize )

            if self._writeAddress is None:
                self._openWritePort(addr)

        except(socket.timeout, BlockingIOError):
            m =  ''

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
            return

        self._writeLock.acquire()

        try:
            self._sWrite.sendto(b, self._writeAddress)
            # self._sWrite.sendall( b )
            
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
        return self._connected

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
        pass
        # while self.dataAvailable():
        #     self.read()
        #     time.sleep(0.01)

    def set_close_on_exec(self, fd):
        try:
            import fcntl
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(fd, fcntl.F_SETFD, flags)
        except:
            pass
# ------------------------------------ EOF -------------------------------------
