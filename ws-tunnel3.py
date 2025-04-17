#!/usr/bin/env python3
import asyncio

LISTEN_ADDR = '127.0.0.1'
LISTEN_PORT = 700
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 109
PASS = ''
RESPONSE = (
    'HTTP/1.1 101 <b><font color="green"> 873ETH x TeamV24 Switching Protocols </font></b>\r\n'
    'Content-Length: 104857600000\r\n\r\n'
)

TIMEOUT = 60

async def handle_client(reader, writer):
    try:
        request = await asyncio.wait_for(reader.read(4096), timeout=5)
        headers = request.decode(errors='ignore').split('\r\n')
        header_dict = {line.split(": ", 1)[0]: line.split(": ", 1)[1] for line in headers if ": " in line}

        real_host = header_dict.get("X-Real-Host", f"{DEFAULT_HOST}:{DEFAULT_PORT}")
        passwd = header_dict.get("X-Pass", "")

        if PASS and passwd != PASS:
            writer.write(b"HTTP/1.1 400 WrongPass!\r\n\r\n")
            await writer.drain()
            writer.close()
            return

        if not real_host.startswith("127.0.0.1") and PASS == "":
            writer.write(b"HTTP/1.1 403 Forbidden!\r\n\r\n")
            await writer.drain()
            writer.close()
            return

        host, port = real_host.split(":")
        port = int(port)

        try:
            target_reader, target_writer = await asyncio.open_connection(host, port)
        except Exception as e:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            await writer.drain()
            writer.close()
            return

        writer.write(RESPONSE.encode())
        await writer.drain()

        async def pipe(reader1, writer1):
            try:
                while not reader1.at_eof():
                    data = await reader1.read(4096)
                    if not data:
                        break
                    writer1.write(data)
                    await writer1.drain()
            except:
                pass
            finally:
                writer1.close()

        await asyncio.gather(
            pipe(reader, target_writer),
            pipe(target_reader, writer)
        )

    except asyncio.TimeoutError:
        writer.close()
    except Exception as e:
        print(f"Error: {e}")
        writer.close()

async def main():
    server = await asyncio.start_server(handle_client, LISTEN_ADDR, LISTEN_PORT)
    print(f"[+] Listening on {LISTEN_ADDR}:{LISTEN_PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")
