import subprocess
import shlex
import threading
from twisted.internet import protocol
from twisted.protocols.stateful import StatefulProtocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
import pprint


def is_int(num_string):
    try:
        int(num_string)
        return True
    except Exception:
        return False


class HandleTaskSel(threading.Thread):
    def __init__(self):
        self.output = ""
        self.tasks = {}
        super(HandleTaskSel, self).__init__()

    def setOutput(self, output):
        self.output = output

    def setHost(self, host):
        self.host = host

    def diff_tasks(self, other_tasks):
        # make a dict for processes not reported by the host
        not_reported = {}
        # processes not found on the host machine
        not_found = {}

        # see which tasks are in other_tasks, but not in the ones reported by tasklist
        for k, v in other_tasks.iteritems():
            if k in self.tasks:
                #compare process name
                if not self.tasks[k] == v:
                    not_reported[k] = v
            else:
                not_reported[k] = v

        # see which keys were reported but not in our host generated task list
        for k, v in self.tasks.iteritems():
            if k not in other_tasks:
                not_found[k] = v
            else:
                pass

        return not_reported, not_found

    def run(self):
        # parse output of task list and turn it into dict of PID:Process Name/ the [3:] skips the first three lines
        for line in self.output.splitlines()[3:]:
            line_data = line.split()
            data_to_remove = []
            if len(line_data) != 6:
                first_elem = ""
                for data in line_data:
                    if is_int(data):
                        break
                    else:
                        first_elem += "%s " % data
                        # if we were to just remove it here, it would mess up the index in the for loop
                        data_to_remove.append(data)

                # remove the duplicate data for the process name here
                for data in data_to_remove:
                    line_data.remove(data)

                # insert the process name as the first element again
                line_data.insert(0, first_elem)
            self.tasks[line_data[1]] = line_data[0]

        # print out the task list we built here
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(self.tasks)

        other_tasks = {'0': 'System Idle Process ',
                      '1000': 'svchost.exe',
                      '200': 'svchost.exe',
                      '240': 'smss.exe',
                      '4': 'System',
                      '400': 'csrss.exe',
                      '500': 'wininit.exe',
                      '512': 'csrss.exe',
                      '564': 'services.ee',
                      '580': 'lsass.exe',
                      '588': 'lsm.exe',
                      '652': 'winlogon.exe',
                      '732': 'svchost.exe',
                      '792': 'nvvsvc.exe',
                      '832': 'svchost.exe',
                      '900': 'svchost.exe',
                      '973': 'svchost.exe',
                      '999': 'tha-Devil.exe'}
        #pp.pprint(self.diff_tasks(other_tasks))


class HandleNetstat(threading.Thread):
    def __init__(self):
        super(HandleNetstat, self).__init__()

    def setOutput(self, output):
        self.output = output

    def setHost(self, host):
        self.host = host

    def run(self):
        # handle data here
        if not self.output:
            # if there is no data to process
            print "No output!"
            pass
        else:
            # process the output from netstat here
            print self.output


class ThreadManager(object):
    def __init__(self):
        self.threads = {}

    def getOrCreateHandler(self, host):
        if host in self.threads:
            thread = self.threads[host]
            # check to see if we've run the thread and it has completed
            if not thread.isAlive():
                # create a new one
                del thread
                thread = self.createThread(host)
            return thread
        else:
            return self.createThread(host)

    def createThread(self, host):
        thread = HandleTaskSel()
        thread.setHost(host)
        self.threads[host] = thread
        return thread

    def startThread(self, host):
        if self.threads[host].isAlive():
            pass
        else:
            self.threads[host].start()


class PrintNetstat(protocol.Protocol):
    def __init__(self, threadManager):
        self.threadManager = threadManager

    def connectionMade(self):
        cmd = 'tasklist'
        self.transport.write(cmd)

    def dataReceived(self, data):
        host = self.transport.getHost()
        thread = self.threadManager.getOrCreateHandler(host)
        thread.setOutput(data)
        self.threadManager.startThread(host)
        self.transport.loseConnection()


class PrintNetstatFactory(protocol.Factory):
    def __init__(self, threadManager, *args, **kwargs):
        self.threadManager = threadManager

    def buildProtocol(self, addr):
        return PrintNetstat(self.threadManager)


if __name__ == "__main__":
    threadManager = ThreadManager()
    endpoint = TCP4ServerEndpoint(reactor, 8124)
    endpoint.listen(PrintNetstatFactory(threadManager))
    reactor.run()
    #thread = HandleTaskSel()
    #f = open('tasklist.txt')
    #thread.setOutput(f.read())
    #thread.run()
