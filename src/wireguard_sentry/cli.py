import signal
from threading import Event
from time import sleep
from ping3 import ping

hosts = ["google.com", "say.what", "localhost"]

exit_event = Event()

def signal_handler(signal, frame):
    print( f"Interrupted by {signal}, stopping" )
    exit_event.set()

class Peer:
    knownParameters = [
        "PrivateKey",
        "ListenPort",
        "FwMark",
        "PublicKey",
        "PresharedKey",
        "AllowedIPs",
        "Endpoint",
        "PersistentKeepalive"
    ]
    def __init__( self, firstLine ):
        self.enabled = firstLine[0] != "#"
        self.lines = [ { "type": "peer", "line": firstLine if self.enabled else firstLine[1:] } ]
        self.parameters = {}
        # We will only toggle the comments for known parameters, to avoid uncommenting real comments
        # https://deepwiki.com/WireGuard/wireguard-tools/3.1-configuration-file-format

    def __repr__( self ):
        return self.get_host()

    def print( self ):
        prefix = "" if self.enabled else "#"
        for line in self.lines:
            if line["type"] == "string":
                print( line["line"] )
            else:
                print( prefix + line["line"] )
                

    def add_line( self, line ):
        matched = False
        for knownParameter in Peer.knownParameters:
            if knownParameter.lower() in line.lower():
                if line[0] == "#":
                    line = line[1:]
                self.parameters[ knownParameter ] = line.split("=")[1].strip()
                matched = True
                self.lines.append( { "type": knownParameter, "line": line } )
                break

        if not matched:
            self.lines.append( { "type": "string", "line": line } )

    def get_host( self ):
        return self.parameters[ "Endpoint" ].split(":")[0].strip()

class Config:
    def __init__( self, filename ):
        self.filename = filename
        self.read()

    def read( self ):
        self.prefix = []
        self.peers = []
        currentPeer = None
        with open( self.filename, "r" ) as file:
            lines = file.read().splitlines()
            for line in lines:
                if "[Peer]" in line:
                    currentPeer = Peer( line )
                    self.peers.append( currentPeer )
                elif currentPeer != None:
                    currentPeer.add_line( line )
                else:
                    self.prefix.append( line )

    def print( self ):
        for line in self.prefix:
            print( line )
        for peer in self.peers:
            peer.print()

    def get_hosts( self ):
        return list(map( lambda p: p.get_host(), self.peers ))

    def get_active_host( self ):
        for peer in self.peers:
            if peer.enabled:
                return peer.get_host()

    def set_active_host( self, host ):
        for peer in self.peers:
            peer.enabled = peer.get_host() == host

class Sentry:
    def __init__( self, hosts ):
        # constants (make configurable?)
        self.interval=2.5
        self.timeout=0.005
        self.fail_retries=3
        self.okay_retries=10

        # maximum for nicer logging and avoiding overflows
        self.okay_max = 99
        self.fail_max = 99

        print( "Reading Config..." )
        #self.config = Config( "/home/fiz/python/wireguard-sentry/test/demo.conf" )
        self.config = Config( "test/demo.conf" )

        self.hosts = self.config.get_hosts()
        self.active_host = self.config.get_active_host()

        self.config.print()

        # Initialize okays/fails
        self.host_fails = {}
        self.host_okays = {}
        for host in self.hosts:
            self.host_fails[ host ] = 0
            self.host_okays[ host ] = 0

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
        print( f"Switching from {last} to {host}" )
        self.active_host = host
        self.config.set_active_host( host )
        self.config.print()

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

