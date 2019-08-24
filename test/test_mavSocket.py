import unittest
import socket
import time
import os
import sys

sys.path.append(os.path.abspath(''))

from mavlinkThread.mavSocket import mavSocket as commObj

class Test_SocketObjectCreation(unittest.TestCase):
    def setUp(self):
        # Setup reflective port - written data appears on read port
        self.testAddressA = ('localhost', 10000)

        return super().setUp()

    def test_unitTestConfigured(self):
        self.assertEqual(1,1)

    def test_objectedExsists(self):
        comm = commObj( self.testAddressA )
        self.assertIsInstance(comm, commObj)
        
    def test_notConnected(self):
        # Connected should not occur before port is opened
        comm = commObj( self.testAddressA )
        
        self.assertEqual( comm.isOpen(), False )


class Test_ReflectiveSocketObject(unittest.TestCase):
    def setUp(self):
        # Setup reflective port - written data appears on read port
        self.testAddressA = ('localhost', 10000)

        self.testAddressB = self.testAddressA

        self.comm = commObj( self.testAddressA, self.testAddressB )

        self.testBytes = b'Hello, World!'

        return super().setUp()

    def tearDown(self):
        self.comm.closePort()
        
        return super().tearDown()

    def test_Connected(self):
        # Connected state occurs if both read and write addresses are given
        self.comm.openPort()

        self.assertEqual( self.comm.isOpen(), True )

    def test_disconnected(self):
        # Connected state occurs if both read and write addresses are given
        self.comm.openPort()
        self.comm.closePort()

        self.assertEqual( self.comm.isOpen(), False )

    def test_readIn(self):
        # Test data is read in correctly
        self.comm.openPort()

        self.comm.write( self.testBytes )
        time.sleep(0.01)
        bytesIn = self.comm.read()

        self.assertEqual(self.testBytes, bytesIn)

    def test_flush(self):
        # Test flush operation clears read in buffer
        self.comm.openPort()
        self.comm.write( self.testBytes )
        
        time.sleep(0.01)

        self.comm.flush()
        bytesIn = self.comm.read()
        
        self.assertEqual(b'', bytesIn)

class Test_DualSocketConnection(unittest.TestCase):
    def setUp(self):
        # Setup dual port - pointing at each other
        self.testAddressA = ('127.0.0.1', 10000)

        self.testBytes = b'Hello, World!'

        # A should discover listen address from itself
        self.commA = commObj( broadcastAddress=self.testAddressA )
        self.commA.openPort()

        # B should discover boradcast address from A
        self.commB = commObj( listenAddress=self.testAddressA )
        self.commB.openPort()

        return super().setUp()

    def tearDown(self):
        self.commA.closePort()
        self.commB.closePort()

        return super().tearDown()

    def test_notConnected2(self):
        # CommB should not connect until is recieves a message from A and tries to respond
        self.assertFalse(self.commB.isOpen())

    def test_readIn2(self):
        # Test data is read in correctly
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        bytesIn = self.commB.read()

        self.assertEqual(self.testBytes, bytesIn)

    def test_notconnected3(self):
        # CommB should not connect until is recieves a message from A and tries to write back
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        self.commB.read()

        self.assertFalse(self.commB.isOpen())

    def test_connected2(self):
        # CommB should not connect until is recieves a message from A and tries to write back
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        self.commB.read()
        self.commB.write(self.testBytes)

        self.assertTrue(self.commB.isOpen())

    def test_addressDiscovery(self):
        # Test that commB can respond to commA after learning address
        self.commA.write(self.testBytes)
        # To bind to a discovered read port a read command must be sent
        self.commA.read()
        time.sleep(0.01)

        # Discover connection and respond
        self.commB.read()
        self.commB.write(self.testBytes)
        time.sleep(0.01)

        # Read in data
        bytesIn = self.commA.read()

        self.assertEqual(self.testBytes, bytesIn)


class Test_AF_UNIX(unittest.TestCase):
    def setUp(self):
        # Setup dual port - pointing at each other
        self.testAddressA = os.path.abspath('') + '/.testA'
        self.testAddressB = os.path.abspath('') + '/.testB'

        self.testBytes = b'Hello, World!'

        # B should discover boradcast address from A
        self.commB = commObj( listenAddress=self.testAddressA, broadcastAddress=self.testAddressB )
        self.commB.set_AF_type( socket.AF_UNIX )
        self.commB.openPort()

        # A should discover listen address from itself
        self.commA = commObj( broadcastAddress=self.testAddressA, listenAddress=self.testAddressB )
        self.commA.set_AF_type( socket.AF_UNIX )
        self.commA.openPort()

        return super().setUp()

    def tearDown(self):
        self.commA.closePort()
        self.commB.closePort()

        return super().tearDown()

    def test_notConnected2(self):
        # CommB should not connect until is recieves a message from A and tries to respond
        self.assertFalse(self.commB.isOpen())

    def test_readIn2(self):
        # Test data is read in correctly
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        bytesIn = self.commB.read()

        self.assertEqual(self.testBytes, bytesIn)

    def test_notconnected3(self):
        # CommB should not connect until is recieves a message from A and tries to write back
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        self.commB.read()

        self.assertFalse(self.commB.isOpen())
        
if __name__ == '__main__':
    unittest.main()