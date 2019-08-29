import unittest
import serial
import time
from threading import Thread
import queue

from mavlinkThread import mavSocket, mavThread
import pymavlink.dialects.v20.ardupilotmega as pymavlink

class testMavlinkThread(mavThread.mavThread):
    def __init__(self, conn, mavLib):
        self.readQueue = queue.Queue()

        super( testMavlinkThread, self).__init__( conn, mavLib )

    def _processReadMsg(self, msgList):
        for msg in msgList:
            self.readQueue.put(msg)

    def getReadMsg(self) -> pymavlink.MAVLink_message:
        return self.readQueue.get(timeout=1)


class Test_ObjectCreation(unittest.TestCase):
    def setUp(self):
        self.testAddress = ('localhost', 10000)

        self.comm = mavSocket.mavSocket( self.testAddress, self.testAddress )
        self.comm.openPort()
        return super().setUp()

    def tearDown(self):
        self.comm.closePort()
        
        return super().tearDown()

    def test_unitTest(self):
        self.assertTrue(True)

    def test_objectCreation(self):
        mav = testMavlinkThread( self.comm, pymavlink )

        self.assertTrue(True)

    def test_mavLoopStart(self):
        mav = testMavlinkThread(self.comm, pymavlink)

        mt = Thread(target = mav.loop)
        mt.daemon = True
        mt.start()

        time.sleep(0.5)

        self.assertTrue(mt.isAlive())

    def test_mavLoopStop(self):
        mav = testMavlinkThread(self.comm, pymavlink)

        mt = Thread(target = mav.loop)
        mt.daemon = True
        mt.start()

        mav.stopLoop()
        time.sleep(1)

        self.assertFalse(mt.isAlive())


class Test_Functionality(unittest.TestCase):
    def setUp(self):
        self.testAddress = ('localhost', 10000)

        self.comm = mavSocket.mavSocket( self.testAddress, self.testAddress )
        self.comm.openPort()

        self.mav = testMavlinkThread(self.comm, pymavlink)

        self.mt = Thread(target = self.mav.loop)
        self.mt.daemon = True

        self.testMessage = pymavlink.MAVLink_debug_message(0,1,2)
        self.testMessage2 = pymavlink.MAVLink_ping_message(0,0,0,0)

        return super().setUp()

    def tearDown(self):
        self.mav.stopLoop()
        self.comm.closePort()
        
        return super().tearDown()

    def test_queueMessage(self):
        self.mt.start()
        self.mav.queueOutputMsg( self.testMessage )

        self.assertTrue(True)

    def test_readMessage(self):
        self.mt.start()
        self.mav.queueOutputMsg( self.testMessage )
        time.sleep(1)
        msg = self.mav.getReadMsg()

        self.assertIsInstance( msg, type(self.testMessage) )

    def test_priorityQueue(self):
        self.mav.queueOutputMsg( self.testMessage, priority = 5 )
        self.mav.queueOutputMsg( self.testMessage2, priority = 1 )

        self.mt.start()

        msg1 = self.mav.getReadMsg()
        msg2 = self.mav.getReadMsg()

        a = isinstance( msg1, type(self.testMessage2))
        b = isinstance( msg2, type(self.testMessage))

        self.assertTrue( a & b )


if __name__ == '__main__':
    unittest.main()