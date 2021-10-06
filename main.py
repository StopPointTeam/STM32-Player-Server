import time
import json
import asyncio

import aiohttp
from fuzzywuzzy import fuzz
from loguru import logger


citycode_list = json.load(open('./citycode.json', 'r'))


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    data: bytes = await reader.read(100)
    req_str: str = data.decode('gbk')

    addr: tuple = writer.get_extra_info('peername')
    logger.info(f"从 {addr!r} 接收：{req_str!r}")

    # 处理请求
    if (req_str.find('checknet') != -1):
        resp_str = checknet_handler(req_str)
    elif (req_str.find('time') != -1):
        resp_str = time_handler(req_str)
    elif (req_str.find('weather') != -1):
        resp_str = await weather_handler(req_str)
    elif (req_str.find('ipaddr') != -1):
        resp_str = await ipaddr_handler(req_str, addr)
    else:
        resp_str = 'ERROR'

    logger.info(f"发送：{resp_str!r}")
    writer.write((resp_str + '\n').encode('gbk'))
    await writer.drain()

    logger.info("关闭连接")
    writer.close()


def checknet_handler(req_str: str) -> str:
    return 'OK'


def time_handler(req_str: str) -> str:
    return 'OK\n' + time.strftime("%Y%m%d%H%M%S", time.localtime())


async def weather_handler(req_str: str) -> str:
    city_str = req_str.split('=')[1]
    city_code = city_to_code(city_str)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://t.weather.itboy.net/api/weather/city/{city_code}") as resp:
            res = await resp.json()

    if res['status'] != 200:
        return 'ERROR'
    else:
        return 'OK\n' + str(res['cityInfo']['city']) + '&' + str(res['data']['forecast'][0]['type']) + '&' + str(res['data']['wendu']) + '&' + str(
            res['data']['forecast'][0]['fx']) + '&' + str(res['data']['forecast'][0]['fl']) + '&' + str(res['data']['shidu']) + '&' + str(res['data']['quality'])


def city_to_code(city_str: str) -> str:
    ratio_list = []

    for city in citycode_list:
        ratio_list.append(fuzz.ratio(city_str, city['city_name']))

    max_i = 0
    for i in range(len(ratio_list)):
        if ratio_list[i] > ratio_list[max_i] and citycode_list[i]['city_code'] != '':
            max_i = i

    return citycode_list[max_i]['city_code']


async def ipaddr_handler(req_str: str, addr: tuple) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://opendata.baidu.com/api.php?query={addr[0]}&co=&resource_id=6006&oe=utf8") as resp:
            res = await resp.json()

    if 'data' in res:
        return f"OK\n{addr[0]}&{res['data'][0]['location']}"
    else:
        return 'FAIL'


async def main():
    server = await asyncio.start_server(
        handler, '0.0.0.0', 2333)

    addr = server.sockets[0].getsockname()
    logger.info(f"STM32-Player-Server 开始运行：{addr}")

    async with server:
        await server.serve_forever()

asyncio.run(main())
