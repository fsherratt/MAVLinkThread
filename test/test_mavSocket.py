import unittest
import socket
import time

from mavlinkThread.mavSocket import mavSocket as commObj

class Test_SocketObjectCreation(unittest.TestCase):
    def setUp(self):
        # Setup reflective port - written data appears on read port
        self.testPortA = 10000
        self.testHostA = ''

        return super().setUp()

    def test_unitTestConfigured(self):
        self.assertEqual(1,1)

    def test_objectedExsists(self):
        comm = commObj( listenPort=self.testPortA )
        self.assertIsInstance(comm, commObj)

    def test_portStored(self):
        # Check that read address is stored
        comm = commObj( listenPort=self.testPortA, listenAddress=self.testHostA )

        testAddress = (socket.gethostbyname(self.testHostA), int(self.testPortA))
        self.assertEqual( testAddress, comm._readAddress )
        
    def test_notConnected(self):
        # Connected should not occur before port is opened
        comm = commObj( listenPort=self.testPortA )
        
        self.assertEqual( comm.isOpen(), False )


class Test_ReflectiveSocketObject(unittest.TestCase):
    def setUp(self):
        # Setup reflective port - written data appears on read port
        self.testPortA = 10000
        self.testHostA = 'localhost'

        self.testPortB = self.testPortA
        self.testHostB = self.testHostA

        self.comm = commObj( listenPort=self.testPortA, listenAddress=self.testHostA, 
                        broadcastPort=self.testPortB, broadcastAddress=self.testHostB )

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
        self.testPort = 10000
        self.testHost = 'localhost'

        self.testBytes = b'Hello, World!'

        # A should discover listen address from itself
        self.commA = commObj(  broadcastPort=self.testPort, broadcastAddress=self.testHost,
                               listenAddress=self.testHost )
        self.commA.openPort()

        # B should discover boradcast address from A
        self.commB = commObj( listenPort=self.testPort, listenAddress=self.testHost )
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
        time.sleep(0.01)

        # Discover connection and respond
        self.commB.read()
        self.commB.write(self.testBytes)
        time.sleep(0.01)

        # Read in data
        bytesIn = self.commA.read()

        self.assertEqual(self.testBytes, bytesIn)


if __name__ == '__main__':
    unittest.main()