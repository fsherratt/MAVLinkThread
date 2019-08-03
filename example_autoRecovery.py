# ------------------------------------------------------------------------------
# helloWorld.py
# System attempts to automatically restart serial connection after an exception
#
# Author: Freddie Sherratt
# ------------------------------------------------------------------------------

import threading
import time

from mavlinkThread import mavSerial, mavThread
import pymavlink.dialects.v10.ardupilotmega as pymavlink

# Print out all incoming message
class mavClass( mavThread.mavThread ):
    def _processReadMsg( self, msgList ):
        for msg in msgList:
            print( msg )

    def loop( self ):
        while not self._intentionallyExit:
            try:
                super( mavClass, self).loop()
            except:
                self._ser.closePort()

                time.sleep(1)
                self.startRWLoop()


if __name__ == "__main__":
    # Open serial port connection
    serialObj = mavSerial.mavSerial( '/dev/ttyu1' )
    serialObj.openPort()

    # Create mavlink thread object
    mavObj = mavClass( serialObj, pymavlink )
    mavObj.startRWLoop() # How should the startup behaviour act? Connect immediatly/wait until start?

    # Create mavlink thread
    mavThread = threading.Thread( target = mavObj.loop, daemon = True )
    mavThread.start()

    # Send heartbeat message at 2Hz
    try:
        while True:
            heartbeatMsg = pymavlink.MAVLink_heartbeat_message( 0, 0, 0, 0, 0, 0 )
            mavObj.queueOutputMsg( heartbeatMsg )

            time.sleep(0.5)

    # Close on keyboard interrupt
    except KeyboardInterrupt:
        pass

    mavObj.stopRWLoop()

    print('Bye')

# ------------------------------------ EOF -------------------------------------
