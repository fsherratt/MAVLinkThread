# These tests make use of MacOS very simple IPC serial ports
import unittest
import serial
import time

from mavlinkThread.mavSerial import mavSerial as commObj

class Test_SocketObjectCreation(unittest.TestCase):
    def setUp(self):
        # Setup reflective port - written data appears on read port
        self.testAddress = ('/dev/ttys1', 57600)

        return super().setUp()

    def test_unitTestConfigured(self):
        self.assertEqual(1,1)

    def test_objectedExsists(self):
        comm = commObj( serialPortAddress=self.testAddress )
        self.assertIsInstance(comm, commObj)

    def test_not_connected(self):
        # Connection not open before connection
        comm = commObj( serialPortAddress=self.testAddress )
        
        self.assertFalse(comm.isOpen())

class Test_SingledEndedPort(unittest.TestCase):
    def setUp(self):
        self.testAddress = ('/dev/ttys1', 57600)

        self.commA = commObj( serialPortAddress=self.testAddress )
        self.commA.openPort()

        self.testBytes = b'Hello, World!'

        return super().setUp()

    def tearDown(self):
        self.commA.closePort()
        
        return super().tearDown()

    def test_connected(self):
        self.assertTrue(self.commA.isOpen())

    def test_close_port(self):
        self.commA.closePort()
        self.assertFalse(self.commA.isOpen())
    
    def test_write_timeout_handled(self):
        self.commA.write(self.testBytes)

        self.assertTrue(True)

class Test_DualPorts(unittest.TestCase):
    def setUp(self):
        self.testAddressA = ('/dev/ttys1', 57600)
        self.testAddressB = ('/dev/ptys1', 57600)

        self.commA = commObj( serialPortAddress=self.testAddressA )
        self.commA.openPort()

        self.commB = commObj( serialPortAddress=self.testAddressB )
        self.commB.openPort()

        self.testBytes = b'Hello, World!'

        return super().setUp()

    def tearDown(self):
        self.commA.closePort()
        self.commB.closePort()
        
        return super().tearDown()
 
    def test_write_out(self):
        self.commA.write(self.testBytes)
        
        self.assertTrue(True)

    def test_data_not_available(self):
        self.assertFalse( self.commB.dataAvailable() )

    def test_dataAvailable(self):
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        self.assertTrue( self.commB.dataAvailable() )

    def test_flush(self):
        self.commA.write(self.testBytes)
        self.commB.flush()
        time.sleep(0.01)
        self.assertFalse( self.commB.dataAvailable() )

    def test_read_byte_in(self):
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        byteIn = self.commB.read()

        self.assertEqual( ord(byteIn), self.testBytes[0] )

    def test_read_bytes_in(self):
        self.commA.write(self.testBytes)
        time.sleep(0.01)
        bytesIn = bytearray()

        while len(bytesIn) < len(self.testBytes):
            bytesIn.extend( self.commB.read() )

        self.assertEqual( bytesIn, self.testBytes )

if __name__ == '__main__':
    unittest.main()