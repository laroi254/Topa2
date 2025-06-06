import json
import time
import threading
import asyncio
import httpx
from pyrogram import Client, filters
from datetime import timedelta
from FUNC.usersdb_func import *
from FUNC.defs import *
from .gate import *
from .response import *
from TOOLS.check_all_func import *
from TOOLS.getcc_for_mass import *


async def mchkfunc(fullcc, user_id):
    retries = 3
    for attempt in range(retries):
        try:
            proxies = await get_proxy_format()
            session = httpx.AsyncClient(
                timeout=30, proxies=proxies, follow_redirects=True)
            result = await create_shopify_charge(fullcc, session)
            getresp = await get_charge_resp(result, user_id, fullcc)
            response = getresp["response"]
            status = getresp["status"]

            await session.aclose()
            return f"Card↯ <code>{fullcc}</code>\n<b>Status - {status}</b>\n<b>Result -⤿ {response} ⤾</b>\n\n"

        except Exception as e:
            import traceback
            await error_log(traceback.format_exc())
            if attempt < retries - 1:
                await asyncio.sleep(0.5)
                continue
            else:
                return f"<code>{fullcc}</code>\n<b>Result - DECLINED ❌</b>\n"


@Client.on_message(filters.command("mso", [".", "/"]))
def multi(Client, message):
    t1 = threading.Thread(target=bcall, args=(Client, message))
    t1.start()


def bcall(Client, message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(stripe_mass_auth_cmd(Client, message))
    loop.close()


async def stripe_mass_auth_cmd(Client, message):
    try:
        user_id = str(message.from_user.id)
        first_name = str(message.from_user.first_name)
        checkall = await check_all_thing(Client, message)

        if checkall[0] == False:
            return

        role = checkall[1]
        getcc = await getcc_for_mass(message, role)
        if getcc[0] == False:
            await message.reply_text(getcc[1], message.id)
            return

        ccs = getcc[1]
        resp = f"""
- 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 -  SHOPIFY [9.53$]

- 𝐂𝐂 𝐀𝐦𝐨𝐮𝐧𝐭 -{len(ccs)}
- 𝐂𝐡𝐞𝐜𝐤𝐞𝐝 - Checking CC For {first_name}

- 𝐒𝐭𝐚𝐭𝐮𝐬 - Processing...⌛️
        """
        nov = await message.reply_text(resp, message.id)

        text = f"""
<b>↯ MASS SHOPIFY [9.53$] [/mso]

Number Of CC Check : [{len(ccs)} / 25]
</b> \n"""
        amt = 0
        start = time.perf_counter()
        # proxies    = await get_proxy_format()
        # session    = httpx.AsyncClient(timeout= 60 , proxies = proxies , follow_redirects=True )
        works = [mchkfunc(i, user_id) for i in ccs]
        worker_num = int(json.loads(
            open("FILES/config.json", "r", encoding="utf-8").read())["THREADS"])

        while works:
            a = works[:worker_num]
            a = await asyncio.gather(*a)
            for i in a:
                amt += 1
                text += i
                if amt % 5 == 0:
                    try:
                        await Client.edit_message_text(message.chat.id, nov.id, text)
                    except:
                        pass
            await asyncio.sleep(1)
            works = works[worker_num:]

        # await session.aclose()
        taken = str(timedelta(seconds=time.perf_counter() - start))
        hours, minutes, seconds = map(float, taken.split(":"))
        hour = int(hours)
        min = int(minutes)
        sec = int(seconds)
        results = await getuserinfo(user_id)
        credit = results["credit"]




        text += f"""
- 𝗧𝗶𝗺𝗲 -  {hour}.h {min}.m {sec}.s 
"""
        await Client.edit_message_text(message.chat.id, nov.id, text)
        await massdeductcredit(user_id, len(ccs))
        await setantispamtime(user_id)

    except:
        import traceback
        await error_log(traceback.format_exc())
