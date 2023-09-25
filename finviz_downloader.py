import asyncio
import random
import aiohttp
import pandas as pd

async def download_url(session, url,ticker):
    async with session.get(url) as response:
        if response.status == 200:
            content = await response.read()
            print(f"Downloaded {len(content)} bytes from {url}")
            content_tbl=pd.read_html(content)
            df_news = content_tbl[10]
            df_news['ticker']=ticker
            df_news.columns=['time','news','ticker']
        else:
            print(f"Failed to download from {url}")
    return df_news
async def get_headers():
    return {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.'+ str(random.random())+' Safari/537.36'}

async def main(p_ticker_list, p_csv_filename):

    urls = [f'https://finviz.com/quote.ashx?t={ticker}&p=d' for ticker in p_ticker_list]

    headers = await get_headers()

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [download_url(session, url,ticker) for url,ticker in zip(urls,p_ticker_list)]
        results = await asyncio.gather(*tasks)
        df_all_ticker = pd.concat(results)
        df_all_ticker.to_csv(p_csv_filename, index=None)
        return

if __name__ == '__main__':
    ticker_list = ['MSFT', 'NKE', 'ORCL', 'AAPL', 'META']
    csv_filename = 'testfile.csv'
    asyncio.run(main(p_ticker_list=ticker_list, p_csv_filename=csv_filename))
