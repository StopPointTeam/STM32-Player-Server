# STM32Player 服务端

import asyncio

from loguru import logger


async def handler(reader, writer):
    data = await reader.read(100)
    message = data.decode('gbk')
    addr = writer.get_extra_info('peername')

    logger.info(f"从 {addr!r} 接收：{message!r}")

    logger.info(f"发送：{message!r}")
    writer.write(data)
    await writer.drain()

    logger.info("关闭连接")
    writer.close()


async def main():
    server = await asyncio.start_server(
        handler, '0.0.0.0', 2333)

    addr = server.sockets[0].getsockname()
    logger.info(f"STM32-Player-Server 开始运行：{addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())
