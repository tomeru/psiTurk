"""
Module to provide interaction with the two PsiTurk servers.
"""
import sys, os, subprocess
from threading import Thread, Event
from socket import socket, AF_INET, SOCK_STREAM
from signal import SIGKILL
import urllib2
import webbrowser


def is_port_available(ip, port):
    """
    Determines whether a port is available by attempting to connect to it.
    """
    try:
        port = int(port)
    except ValueError:
        raise(PsiturkControllerException("Port number must be coercable to an integer."))
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.shutdown(2)
        return(0)
    except:
        # TODO this should only run for port-in-use exceptions
        return(1)

class PsiturkControllerException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return(repr(self.value))

class OnState(Thread):
    """
    Polls at a fixed interval defined by `pollinterval` (default 1 second)
    using a state-checking function `state_function` If `state_function`
    returns `True`, runs a given function `function` shuts down.
    
    Example:
        t = OnState(lambda: server.check_port_state(), lambda: print "Server has started!")
        t.start()
        t.cancel() # Cancels thread
    """
    def __init__(self, state_function, function, poll_interval=1):
        Thread.__init__(self)
        self.function = function
        self.state_function = state_function
        self.poll_interval = poll_interval
        self.finished = Event()
        self.final = lambda: ()

    def cancel(self):
        self.finished.set()
    
    def run(self):
        while not self.finished.is_set():
            if self.state_function():
                self.function()
                self.finished.set()
            else:
                self.finished.wait(self.poll_interval)

class BaseServerController:
    """
    Base API for comunicating and interacting with servers launched by PsiTurk.
    """
    def __init__(self, host, port, default_route="", script_file=None):
        try:
            self.port = int(port)
        except ValueError:
            raise(PsiturkControllerException("Port number must be coercable to an integer."))
        self.host = host
        self.default_route = default_route
        self.script_file = script_file
        self.wait_until_online_thread = None
    
    def get_url(self, route=None):
        if not route:
            route = self.default_route
        template = "http://{hostname}:{port}/{route}"
        return(template.format(hostname=self.host, port=self.port,
                               route=route))
    
    def is_running(self):
        """
        Checks whether the server's port is in use. If so, it is assumed the
        server is running.
        """
        return(not is_port_available(self.host, self.port))
        
    def launch_browser(self, route=None):
        """
        Launch a browser pointed at the specified route on the server (or
        `default_route` if none is passed in).
        """
        if not route:
            route = self.default_route
        launchurl = "http://{host}:{port}/{route}".format(host=self.host,
                                                          port=self.port,
                                                          route=route)
        webbrowser.open(launchurl, new=1, autoraise=True)
    
    def wait_until_online(self, function, poll_interval=1):
        """
        Uses OnState to wait for the server to come online, then runs
        the given function.
        """
        awaiting_service = OnState(self.is_running, function,
                                          poll_interval=poll_interval)
        awaiting_service.start()
        return(awaiting_service)
    
    def launch_browser_when_online(self):
        """
        Wait for the port to be taken, then launch the browser pointed at it.
        """
        self.wait_until_online_thread = self.wait_until_online(self.launch_browser)
    
    def startup(self):
        if not self.script_file:
            raise(PsiturkControllerException("No script file provided"))
        server_command = "{python_exec} '{server_script}'".format(
            python_exec = sys.executable,
            server_script = os.path.join(os.path.dirname(__file__),
                                         self.script_file)
        )
        if not self.is_running():
            print("Running experiment server with command:", server_command)
            subprocess.Popen(server_command, shell=True, close_fds=True)
            return("Experiment server launching...")
        else:
            return("Experiment server is already running...")

class ExperimentServerController(BaseServerController):
    """
    Class definition for the experiment server.
    """
    def __init__(self, host, port, default_route="", script_file=None, **kwargs):
        self.parent = BaseServerController
        self.parent.__init__(self, host, port, default_route=default_route,
                             script_file=script_file, **kwargs)
    
    def get_ppid(self):
        """
        Retrieve the server's pid by accessing its /ppid route.
        """
        if self.is_running():
            url = self.get_url(route="ppid")
            ppid_request = urllib2.Request(url)
            ppid =  urllib2.urlopen(ppid_request).read()
            return(ppid)
        else:
            raise(PsiturkControllerException("Cannot retrieve experiment server\
                                         pid, experiment server does not appear\
                                         to be running (at least not on port\
                                         {})".format(self.port)))
    
    def shutdown(self, ppid=None):
        if not ppid:
            ppid = self.get_ppid()
        print("Shutting down experiment server at pid %s..." % ppid)
        try:
            os.kill(int(ppid), SIGKILL)
        except PsiturkControllerException:
            print(PsiturkControllerException)

class DashboardServerController(BaseServerController):
    """
    Class definition for the dashboard server.
    """
    def __init__(self, host, port, default_route="dashboard", script_file="dashboard.py", **kwargs):
        self.parent = BaseServerController
        self.parent.__init__(self, host, port, default_route=default_route,
                             script_file=script_file, **kwargs)

