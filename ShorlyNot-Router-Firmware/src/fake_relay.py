#!/usr/bin/env python3
"""
Fake Relay Server for ShorlyNot Router Guard project testing.
A simple TCP echo server to simulate the WebSocket relay, with a client mode.
"""
import argparse
import logging
import socket
import threading
import sys
import time

def handle_client(conn, addr):
    """Handle individual TCP client connections."""
    logging.info(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # Echo the received data prefixed with 'ECHO: '
            response = b"ECHO: " + data
            conn.sendall(response)
    except Exception as e:
        logging.error(f"Error handling {addr}: {e}")
    finally:
        logging.info(f"Disconnected {addr}")
        conn.close()

def run_server(host, port):
    """Run the TCP echo server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Allow address reuse
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except Exception as e:
            logging.error(f"Failed to bind to {host}:{port}: {e}")
            sys.exit(1)
            
        s.listen()
        logging.info(f"Fake Relay Server listening on {host}:{port}...")
        
        try:
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            logging.info("Shutting down Fake Relay Server...")

def run_client(host, port):
    """Run the test client to connect to the relay and send messages."""
    print(f"Connecting to {host}:{port}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))
            print("Connected! Type messages to send. Press Ctrl+C to exit.")
            while True:
                msg = input("> ")
                if msg:
                    s.sendall(msg.encode("utf-8"))
                    data = s.recv(1024)
                    print(f"Received: {data.decode('utf-8')}")
    except ConnectionRefusedError:
        print("Connection refused. Make sure the server is running and firewall allows it.")
    except socket.timeout:
        print("Connection timed out. Firewall might be dropping packets.")
    except KeyboardInterrupt:
        print("\nExiting client.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fake Relay TCP Server/Client")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen/connect on (default: 8765)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to listen/connect on (default: 127.0.0.1)")
    parser.add_argument("--client", action="store_true", help="Run in client mode to test connection")
    
    args = parser.parse_args()

    # Initialise logging here so it's always set up before any log calls
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if args.client:
        run_client(args.host, args.port)
    else:
        run_server(args.host, args.port)
