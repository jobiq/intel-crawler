import asyncio
import time
from typing import Union

from prisma import Prisma

connecting = False
prisma: Union[Prisma, None] = None

async def connect_prisma(prisma: Prisma):
    global connected
    await prisma.connect()

    if prisma.is_connected():
        connected = True


def threaded_function(prisma: Prisma):
    asyncio.run(connect_prisma(prisma))


async def connect(reconnect: bool = False):
    global prisma
    global connecting

    # if reconnect and prisma is not None and prisma.is_connected():
    #     await prisma.disconnect()

    if reconnect or prisma is None:
        prisma = Prisma()
        await prisma.connect()

    if prisma.is_connected():
        return prisma

    retry = 0

    while not prisma.is_connected():
        if not connecting and not prisma.is_connected():
            connecting = True
            await connect_prisma(prisma)
            connecting = False

        if prisma.is_connected():
            return prisma

        if retry < 1:
            retry += 1
            time.sleep(0.25)
        else:
            break

    return prisma

