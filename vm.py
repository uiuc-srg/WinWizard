import subprocess
import shlex
from twisted.internet import protocol
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor


class GetNetstat(protocol.Protocol):
    def dataReceived(self, data):
        cmd = data
        cm = shlex.split(cmd)
        var = subprocess.check_output(cm, shell=True)
        self.transport.write(var)


class GetNetstatFactory(protocol.ReconnectingClientFactory):
    def __init__(self):
        self.maxDelay = 5
        self.initialDelay = 5

    def startedConnecting(self, connector):
        #print 'Started to connect.'
        pass

    def buildProtocol(self, addr):
        #print 'Connected.'
        #print 'Resetting reconnection delay'
        self.resetDelay()
        return GetNetstat()

    def clientConnectionLost(self, connector, reason):
        #print 'Lost connection.  Reason:', reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        #print 'Connection failed. Reason:', reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


#reactor.listenTCP(8123, GetNetstatFactory()) # server line
reactor.connectTCP('localhost', 8124, GetNetstatFactory())
reactor.run()
