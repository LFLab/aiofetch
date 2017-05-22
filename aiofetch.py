__version__ = "0.2.0"

import os
import asyncio
import argparse

import aiohttp
import async_timeout
from aiofiles import open as aopen
from bs4 import BeautifulSoup as bs


async def save_img(fpath, url, semaphore):
    print("request img from", url)
    async with aiohttp.request("GET", url) as r:
        data = await r.read()
    print("saving file to:", fpath, url)
    async with semaphore, aopen(fpath, 'wb') as f:
        await f.write(data)


async def fetch_imgs(url):
    print('request page 1:', url)
    with async_timeout.timeout(10):
        async with aiohttp.request("GET", url) as r:
            soup = bs(await r.text(), 'lxml')
    ps = soup.select('option')[1:]
    img_url = soup.select('img[src*=".jpg"]')[0]['src']
    img_root = img_url.rsplit('/', 1)[0]
    return ("%s/%03d.jpg" % (img_root, idx) for idx, _ in enumerate(ps, 1))


async def fetch_vols(url):
    r = await aiohttp.request('GET', url)
    soup = bs(await r.text('big5-hkscs'), "lxml")
    vols = soup.select('fieldset:nth-of-type(2) a')
    cur = url.rsplit('/', 2)[0]
    return ((v.text, cur + v['href']) for v in vols)


async def main(args):
    dest = args.dir or "Comic_from_%s" % args.url.split('/', 1)[-1]
    if not os.path.isdir(dest):
        os.makedirs(dest)
    os.chdir(dest)
    fs = []
    for vol, url in await fetch_vols(args.url):
        if not os.path.isdir(vol):
            os.makedirs(vol)
            print("create dir %s" % vol)
            fs.append(fetch_imgs(url))

    img_fs, semaphore = [], asyncio.Semaphore(args.limit)
    for f in asyncio.as_completed(fs):
        try:
            imgs = await f
        except asyncio.TimeoutError:
            print("request for %s timeout." % vol)
            print("skip to next.")
        else:
            for idx, img_url in enumerate(imgs, 1):
                fpath = os.path.join(vol, "%03d.jpg" % idx)
                img_f = asyncio.ensure_future(save_img(fpath, img_url, semaphore))
                img_fs.append(img_f)

    await asyncio.wait(img_fs)


if __name__ == '__main__':
    arg = argparse.ArgumentParser()
    arg.add_argument("url", help="the url.")
    arg.add_argument("-dest", "-d", dest="dir", help="the destnation folder.")
    arg.add_argument("-limit", "-l", type=int, default=50, dest='limit',
                     help="the concurrent saving image limit.")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(arg.parse_args()))
