import signal
from threading import Event
from time import sleep
from ping3 import ping

hosts = ["google.com", "say.what", "localhost"]

exit_event = Event()

def signal_handler(signal, frame):
    print( f"Interrupted by {signal}, stopping" )
    exit_event.set()

class Sentry:
    def __init__( self, hosts ):
        self.hosts = hosts

        # constants (make configurable?)
        self.interval=2.5
        self.timeout=0.005
        self.fail_retries=3
        self.okay_retries=10

        # maximum for nicer logging and avoiding overflows
        self.okay_max = 99
        self.fail_max = 99

        print( "Reading Config..." )
        # TODO: read WG-config

        # Initialize okays/fails
        self.host_fails = {}
        self.host_okays = {}
        for host in self.hosts:
            self.host_fails[ host ] = 0
            self.host_okays[ host ] = 0

        self.active_host = self.hosts[0]

        # graceful exit sleep

    def host_add_okay( self, host ):
        self.host_fails[ host ] = 0
        if self.host_okays[ host ] < self.okay_max:
            self.host_okays[ host ] = self.host_okays[ host ] + 1

    def host_add_fail( self, host ):
        self.host_okays[ host ] = 0
        if self.host_fails[ host ] < self.fail_max:
            self.host_fails[ host ] = self.host_fails[ host ] + 1

    def ping_host( self, host ):
        result = not not ping( host, timeout=self.timeout )
        if result:
            self.host_add_okay( host )
        else:
            self.host_add_fail( host )
        return result

    def ping_all( self ):
        print( "Active:", self.active_host, end="  " )
        print( "Pinging ", end="" )
        for host in self.hosts:
            result = self.ping_host( host )
            print( " ", host, end="-" )
            print( "_OK_" if result else "FAIL", end="#" )
            print( self.host_okays[host] if result else self.host_fails[host], end=" " )
        print("")

    def switch_active( self, host ):
        last = self.active_host
        self.active_host = host
        print( f"Switching from {last} to {host}" )

    def select_active( self ):
        for i, host in enumerate( self.hosts ):
            # first host okay, stay as is
            if host == self.active_host and i == 0 and self.host_fails[ host ] < self.fail_retries:
                return 

            # take next host, but only if okay enough
            if host != self.active_host and self.host_okays[host] >= self.okay_retries:
                self.switch_active( host )
                return
        pass

    def run( self ):
        global exit_event

        while not exit_event.is_set():
            self.ping_all()
            self.select_active()
            exit_event.wait( self.interval )
            self.timeout = self.timeout + 0.0001

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sentry = Sentry( hosts )
    sentry.run()

if __name__ == "__main__":
    main()

