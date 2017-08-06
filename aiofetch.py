import os
import sys
import asyncio
import argparse
from datetime import datetime

import aiohttp
from aiofiles import open as aopen
from bs4 import BeautifulSoup as bs

__version__ = "0.3.3"
__doc__ = "comic image fetcher for http://www.cartoonmad.com/"


async def save_img(fpath, url, session):
    try:
        async with session.get(url, timeout=45) as r:
            print("request img from", url)
            data = await r.read()
        async with aopen(fpath, 'wb') as f:
            print("saving file to:", fpath, url)
            await f.write(data)
    except Exception as e:
        print("fail to save img from", url, "due to", repr(e))
        return fpath, url
    else:
        return None


async def fetch_imgs(url, vol, session):
    print('request vol %s page 1 in url: %s' % (vol, url))
    async with session.get(url, timeout=20) as r:
        soup = bs(await r.text('big5-hkscs'), 'html.parser')
    ps = soup.select('option')[1:]
    img_url = soup.select('img[onload]')[0]['src']
    img_root = img_url.rsplit('/', 1)[0]
    return vol, ("%s/%03d.jpg" % (img_root, idx) for idx, _ in enumerate(ps, 1))


async def fetch_vols(url, session):
    async with session.get(url, timeout=10) as r:
        soup = bs(await r.text('big5-hkscs'), "html.parser")
    vols = soup.select('fieldset:nth-of-type(2) a')
    cur = url.rsplit('/', 2)[0]
    return ((v.text, cur + v['href']) for v in vols)


async def main(args):
    print("=== program start at %s ===" % datetime.now(), file=sys.stderr)
    dest = args.dir or "Comic_from_%s" % args.url.split('/', 2)[-1]
    if not os.path.isdir(dest):
        os.makedirs(dest)
    os.chdir(dest)
    conn = aiohttp.TCPConnector(limit=args.limit)
    session = aiohttp.ClientSession(connector=conn)

    fs = []
    for vol, url in await fetch_vols(args.url, session):
        if not os.path.isdir(vol):
            os.makedirs(vol)
            print("create dir %s" % vol)
        fs.append(asyncio.ensure_future(fetch_imgs(url, vol, session)))

    img_fs = []
    for f in asyncio.as_completed(fs):
        try:
            vol, imgs = await f
        except asyncio.TimeoutError:
            print("request for %s timeout. skip to next." % vol, file=sys.stderr)
        else:
            for idx, img_url in enumerate(imgs, 1):
                fpath = os.path.join(vol, "%03d.jpg" % idx)
                if not os.path.exists(fpath):
                    img_f = asyncio.ensure_future(save_img(fpath, img_url, session))
                    img_fs.append(img_f)
    done, _ = await asyncio.wait(img_fs)

    print("=== tasks done at %s ===" % datetime.now(), file=sys.stderr)
    pending = [f.result() for f in done if f.result()]
    while any(pending):
        print(" * retry for %s page(s) at %s" % (len(pending), datetime.now()), file=sys.stderr)
        done, _ = await asyncio.wait([save_img(fp, url, session) for fp, url in pending])
        pending = [f.result() for f in done if f.result()]

    print("=== program end at %s ===" % datetime.now(), file=sys.stderr)
    session.close()

if __name__ == '__main__':
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("url", help="the url.")
    arg.add_argument("-dest", "-d", dest="dir", help="the destnation folder.")
    arg.add_argument("-limit", "-l", type=int, default=256, dest='limit',
                     help="the concurrent saving image limit.")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(arg.parse_args()))
