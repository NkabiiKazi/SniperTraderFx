import os
import sys
import logging
from twisted.internet import reactor
from ctrader_open_api import Client, Protobuf, TcpProtocol
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)

# Load credentials from GitHub Secrets environment variables
CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("CTRADER_ACCOUNT_ID")

HOST = "live.ctraderapi.com"  # Live endpoint for Pepperstone live account
PORT = 5035

if not all([CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, ACCOUNT_ID]):
    logging.error("Missing required environment variables/secrets. Please check GitHub repository secrets.")
    sys.exit(1)

class cTraderBot:
    def __init__(self, reactor, client_id, client_secret, access_token, account_id):
        self.reactor = reactor
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.account_id = int(account_id)
        
        self.client = Client(HOST, PORT, TcpProtocol)
        self.client.setConnectedCallback(self.connected)
        self.client.setConnectionFailedCallback(self.connection_failed)
        self.client.setConnectionLostCallback(self.connection_lost)
        self.client.setMessageReceivedCallback(self.message_received)

    def start(self):
        logging.info("Connecting to cTrader Open API Live Gateway...")
        self.client.startService()

    def connected(self, client):
        logging.info("Connected successfully. Sending Application Authorization...")
        auth_req = ProtoOaApplicationAuthReq()
        auth_req.clientId = self.client_id
        auth_req.clientSecret = self.client_secret
        deferred = self.client.send(auth_req)
        deferred.addCallbacks(self.app_authorized, self.request_failed)

    def app_authorized(self, response):
        logging.info("Application authorized successfully. Sending Account Authorization...")
        account_auth = ProtoOaAccountAuthReq()
        account_auth.ctidTraderAccountId = self.account_id
        account_auth.accessToken = self.access_token
        deferred = self.client.send(account_auth)
        deferred.addCallbacks(self.account_authorized, self.request_failed)

    def account_authorized(self, response):
        logging.info(f"Account {self.account_id} authorized successfully! Bot is ready.")
        
        # --- YOUR TRADING STRATEGY LOGIC GOES HERE ---
        # Example: Check market status or place orders here
        
        logging.info("Execution complete. Shutting down session...")
        self.reactor.callLater(3, self.stop)

    def request_failed(self, failure):
        logging.error(f"API request failed: {failure}")
        self.stop()

    def connection_failed(self, client, reason):
        logging.error(f"Connection failed: {reason}")
        self.stop()

    def connection_lost(self, client, reason):
        logging.info(f"Connection lost: {reason}")
        self.stop()

    def message_received(self, client, message):
        # Handle incoming asynchronous messages/quotes/events here if needed
        pass

    def stop(self):
        if self.client.transport.connected:
            self.client.stopService()
        if self.reactor.running:
            self.reactor.stop()

if __name__ == "__main__":
    bot = cTraderBot(reactor, CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, ACCOUNT_ID)
    reactor.callWhenRunning(bot.start)
    reactor.run()
