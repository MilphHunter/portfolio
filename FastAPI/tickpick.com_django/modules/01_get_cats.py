from modules.load_django import *
from parser_app.models import *

from pprint import pprint

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "uk,en-US;q=0.9,en;q=0.8,ru;q=0.7",
    "priority": "u=0, i",
    "sec-ch-device-memory": "8",
    "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
    "sec-ch-ua-arch": "\"x86\"",
    "sec-ch-ua-full-version-list": "\"Chromium\";v=\"140.0.7339.208\", \"Not=A?Brand\";v=\"24.0.0.0\", \"Google Chrome\";v=\"140.0.7339.208\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "\"\"",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

COOKIES = {
    "appHomepageDL": "\"y\"",
    "_gcl_au": "1.1.976643933.1756643063",
    "rtbhouse_uid": "uid-h4jwunn22g5meznxabw",
    "__pdst": "faf96a3017634a8b935e69a1f5ea8667",
    "sm_uuid": "1756643919852",
    "_tt_enable_cookie": "1",
    "_ttp": "01K401BY0AAPFTXZR8MM97J2V9_.tt.1",
    "rskxRunCookie": "0",
    "rCookie": "q059ul7eszibvm9v7ptm26meznxawi",
    "_fbp": "fb.1.1756643063982.924405585798098451",
    "_swb": "2e082fdd-5f18-4239-b01f-ee8dc0b72196",
    "_uetmsdns": "0",
    "tp_abt_buy_v2_variant": "buy_v2",
    "_hjSessionUser_2080162": "eyJpZCI6ImE0OTZiNjYwLWE5ZmEtNTJiMS1iNGMyLTY4Y2IxNDMyOGE1YSIsImNyZWF0ZWQiOjE3NTY2NDMwNjM5MDcsImV4aXN0aW5nIjp0cnVlfQ==",
    "_ga": "GA1.1.1100262710.1756643068",
    "temporary_analytics_id": "ZVUZWZW2WMOQ",
    "utm_source": "impact",
    "utm_medium": "Smart Influence GmbH",
    "utm_campaign": "3476091",
    "utm_content": "Online Tracking Link_656088",
    "_ketch_consent_v1_": "eyJhbmFseXRpY3MiOnsic3RhdHVzIjoiZ3JhbnRlZCIsImNhbm9uaWNhbFB1cnBvc2VzIjpbImFuYWx5dGljcyJdfSwiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyI6eyJzdGF0dXMiOiJncmFudGVkIiwiY2Fub25pY2FsUHVycG9zZXMiOlsiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyJdfSwiZW1haWxfbWFya2V0aW5nIjp7InN0YXR1cyI6ImdyYW50ZWQifSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7InN0YXR1cyI6ImdyYW50ZWQiLCJjYW5vbmljYWxQdXJwb3NlcyI6WyJlc3NlbnRpYWxfc2VydmljZXMiXX19",
    "_reb2buid": "34d58ffc-94ef-4e25-a842-f480d9825e88",
    "_reb2bgeo": "%7B%22city%22%3A%22Boston%22%2C%22country%22%3A%22United%20States%22%2C%22countryCode%22%3A%22US%22%2C%22hosting%22%3Atrue%2C%22isp%22%3A%22Datacamp%20Limited%22%2C%22lat%22%3A42.3601%2C%22proxy%22%3Atrue%2C%22region%22%3A%22MA%22%2C%22regionName%22%3A%22Massachusetts%22%2C%22status%22%3A%22success%22%2C%22timezone%22%3A%22America%2FNew_York%22%2C%22zip%22%3A%2202112%22%7D",
    "_swb_consent_": "eyJjb2xsZWN0ZWRBdCI6MTc1ODA5MjQ5MSwiZW52aXJvbm1lbnRDb2RlIjoicHJvZHVjdGlvbiIsImlkZW50aXRpZXMiOnsic3diX3dlYnNpdGVfc21hcnRfdGFnIjoiMmUwODJmZGQtNWYxOC00MjM5LWIwMWYtZWU4ZGMwYjcyMTk2In0sImp1cmlzZGljdGlvbkNvZGUiOiJkZWZhdWx0IiwicHJvcGVydHlDb2RlIjoid2Vic2l0ZV9zbWFydF90YWciLCJwdXJwb3NlcyI6eyJhbmFseXRpY3MiOnsiYWxsb3dlZCI6InRydWUiLCJsZWdhbEJhc2lzQ29kZSI6ImRpc2Nsb3N1cmUifSwiYmVoYXZpb3JhbF9hZHZlcnRpc2luZyI6eyJhbGxvd2VkIjoidHJ1ZSIsImxlZ2FsQmFzaXNDb2RlIjoiZGlzY2xvc3VyZSJ9LCJlbWFpbF9tYXJrZXRpbmciOnsiYWxsb3dlZCI6InRydWUiLCJsZWdhbEJhc2lzQ29kZSI6ImRpc2Nsb3N1cmUifSwiZXNzZW50aWFsX3NlcnZpY2VzIjp7ImFsbG93ZWQiOiJ0cnVlIiwibGVnYWxCYXNpc0NvZGUiOiJkaXNjbG9zdXJlIn19fQ%3D%3D",
    "lastRskxRun": "1758890711570",
    "_uetvid": "6da5b820866511f08a8d5b991655f17f",
    "ABTasty": "uid=2brxkxz25vwb69yt&fst=1756643063120&pst=1758885755278&cst=1758890709820&ns=12&pvt=36&pvis=3&th=1501366.0.1.1.1.1.1758092493586.1758092493586.0.8",
    "ttcsid": "1758890710489::D2uPB7kyW8uKxksCLVhM.11.1758890716829.0",
    "ttcsid_CPF2G63C77UAJK8BBEQ0": "1758890710488::023uYXTZ1tYY7FS4O9pf.11.1758890716830.0",
    "__cf_bm": "oX3y9wH.qziz.qwAeXghd225LMpxO6UW7nq4NCiuKR4-1759131228-1.0.1.1-fBAdPVfDyFwIgq37tDhfudP5vd_ST.FEotsUeEjm4zmXd08OcOipKjly9FdXyzadeyBI94gIJ9vsCubHfGjSGFF.Yjwz4dzeQkmoL8gwc9D35sdoEZe4AqLL6QtlCbDh",
    "_hjSession_2080162": "eyJpZCI6IjVmM2EzNTBjLTY3MjEtNGQ3MS1iNDg5LTQyMTZlNjNkZjg3OCIsImMiOjE3NTkxMzEyNDMzODIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=",
    "oneTapDismissed": "\"true\"",
    "country": "US",
    "IP": "43.225.189.121",
    "user_cn": "us",
    "GEO": "{\"lat\":42.3574,\"long\":-71.0618,\"city\":\"Boston\",\"state\":\"MA\",\"dma\":\"new-bedford-ma\"}",
    "cf_clearance": "zMJO69YyMP0GfZ8xGv4vaBzQgkdGSRRDA_MtoiKkP3Q-1759132126-1.2.1.1-_Auq6R0sIBYGYg7JmWmwRPzMGVKgOw.STj0K092DfA9w2ig8o4QUXYxpFWkqhcWwfLVEot.D7ETGmzwd7VK_Syuqb7_RqZj_sVWFFWRmOqpLgnUhL2veh4Ox8uzbnFh1eooiB6F6RvVUu1wtTjkDYh8Xv4lzf7iEn6gKzZjd9RiL_vY7unP9UhUg6XfjEujvHWltGARpOKHIEIQ8pIWLRDMXlN6zQdXaMLy8Jbo.760",
    "_ga_XNWJCEXY17": "GS2.1.s1759131241$o21$g1$t1759132409$j60$l0$h923325586",
    "sharedSessionId": "o3kMwqwvNPOwxBQ8nNoKnGVuzpNElURz",
    "connect.sid": "s%3Ao3kMwqwvNPOwxBQ8nNoKnGVuzpNElURz.%2FZ%2Bg6OPUYWLltG1FT0yJfq8%2FdtG%2Bz%2BFIv%2Fn%2Bjd%2F8kKk",
    "_rdt_uuid": "1756643063717.4275def8-650b-4631-bf6f-600d39899dac",
    "__rtbh.uid": "%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22uid-h4jwunn22g5meznxabw%22%2C%22expiryDate%22%3A%222026-09-29T07%3A53%3A58.950Z%22%7D",
    "__rtbh.lid": "%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22MfNx7XG29zeciM593z6P%22%2C%22expiryDate%22%3A%222026-09-29T07%3A53%3A58.950Z%22%7D",
    "tatari-cookie-test": "44603183",
    "t-ip": "1",
    "tatari-session-cookie": "87282496-e9e3-2fbe-f802-3e1156aa0a8d",
    "impactClickId": "\"WYSUcz0uRzB8ROx1NzXynw8WUkp3xUxgLX39yo0\"",
    "datadome": "OiqkpBsN72alNcdj8BcYeyLs1jz0AO9DOIMiPdD4HHTAj~Q1d4mqNIcNuErxkH2t6azOdanUNYLB~MQ_jVx3IudGia25rbDOGKAvK06vn7KYrOI15ePaLRM8FCKqLYUS",
    "forterToken": "ee4452942d304d4fbe24c4ecc9397b74_1759132439080__UDF43-mnf-a4_24ck_/C0wStdZTDs%3D-6012-v2"
}

def save(data):
    obj, created = Categories.objects.get_or_create(
        url=data[0],
        defaults={
            'name' : data[1]
        }
    )

    if created:
        print(f'[LOG] Event {data[1]} created.')
    else:
        print(f'[LOG] Event {data[1]} already exists.')


def get_cats():
    url = 'https://www.tickpick.com/'

    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    if response.status_code != 200:
        print(f'[LOG] Main page. Response status code: {response.status_code}')

    html = response.text

    soup = BeautifulSoup(html, 'html.parser')
    data = soup.find_all('a', class_='contentItem')
    hrefs = [('https://www.tickpick.com' + a.get('href'), a.text) for a in data if a.get('href')]

    for href in hrefs:
        save(href)



if __name__ == '__main__':
    get_cats()