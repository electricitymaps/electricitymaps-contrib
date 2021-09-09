
import requests


def test_call():
    session = requests.Session()

    cookies = session.get("http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login").cookies
    payload = {
        "ajaxToken": "",
        "downloadKey": "",
        "fwExtention.actionSubType": "headerInput",
        "fwExtention.actionType": "reference",
        "fwExtention.formId": "CA01S070P",
        "fwExtention.jsonString": "",
        "fwExtention.pagingTargetTable": "",
        "fwExtention.pathInfo": "CA01S070C",
        "fwExtention.prgbrh": "0",
        "msgArea": "・マージンには需給調整市場の連系線確保量が含まれております。",
        "requestToken": "",
        "requestTokenBk": "",
        "searchReqHdn": "",
        "simFlgHdn": "",
        "sntkTgtRklCdHdn": "",
        "spcDay": "2021/09/09",
        "spcDayHdn": "",
        "tgtRkl": "{:02d}".format(4),
        "tgtRklHdn": "01,北海道・本州間電力連系設備,02,相馬双葉幹線,03,周波数変換設備,04,三重東近江線,05,南福光連系所・南福光変電所の連系設備,06,越前嶺南線,07,西播東岡山線・山崎智頭線,08,阿南紀北直流幹線,09,本四連系線,10,関門連系線,11,北陸フェンス",
        "transitionContextKey": "DEFAULT",
        "updDaytime": "",
    }

    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        # cookies=cookies,
        data=payload,
    )
    # print(r.text)
    headers = r.text
    headers = eval(headers.replace("false", "False").replace("null", "None"))

    payload["msgArea"] = headers["root"]["bizRoot"]["header"]["msgArea"]["value"]
    payload["searchReqHdn"] = headers["root"]["bizRoot"]["header"]["searchReqHdn"][
        "value"
    ]
    payload["spcDayHdn"] = headers["root"]["bizRoot"]["header"]["spcDayHdn"][
        "value"
    ]
    payload["updDaytime"] = headers["root"]["bizRoot"]["header"]["updDaytime"][
        "value"
    ]
    # OK till here

    payload["fwExtention.actionSubType"] = "ok"
    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        # "http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C?fwExtention.pathInfo=CA01S070C&fwExtention.prgbrh=0",
        # cookies=cookies,
        data=payload,
    )
    headers = r.text
    headers = eval(headers.replace("false", "False").replace("null", "None"))
    payload["downloadKey"] = headers["root"]["bizRoot"]["header"]["downloadKey"][
        "value"
    ]
    payload["requestToken"] = headers["root"]["bizRoot"]["header"]["requestToken"][
        "value"
    ]

    payload["fwExtention.actionSubType"] = "download"
    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=payload,
    )
    r.encoding = "shift-jis"
    print(r.text)
    exit()

    url = "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C"


    # headers
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Length": "1954",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "JSESSIONID=006B7E3A26362130B648F2800C477C9B9; HSERVERID=4d46852227454b98e9591710522cda9f76f062d8d0ae3da187111c9f7e20e353",
        "Host": "occtonet3.occto.or.jp",
        "Origin": "https://occtonet3.occto.or.jp",
        "Referer": "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C?fwExtention.pathInfo=CA01S070C&fwExtention.prgbrh=0",
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    }
    

    # formdata 
    example_formdata = {
        'ajaxToken': '',
        'downloadKey': '20210909212517_CA01S070C',
        'fwExtention.actionSubType': 'download',
        'fwExtention.formId': 'CA01S070P',
        'fwExtention.jsonString': '',
        'fwExtention.pagingTargetTable': '',
        'fwExtention.pathInfo': 'CA01S070C',
        'fwExtention.prgbrh': '0',
        'msgArea': ' ・マージンには需給調整市場の連系線確保量が含まれております。',
        'requestToken': 'a6b6b90b848abe5de98fd561d2ed9fe4f2b48961c2b2dc74',
        'requestTokenBk': '',
        'searchReqHdn': '[検索条件]対象連系線:周波数変換設備,指定日:2021/09/09',
        'simFlgHdn': '',
        'sntkTgtRklCdHdn': '15',
        'spcDay': '2021/09/09',
        'spcDayHdn': '20210909',
        'tgtRkl': '03',
        'tgtRklHdn': '01,北海道・本州間電力連系設備,02,相馬双葉幹線,03,周波数変換設備,04,三重東近江線,05,南福光連系所・南福光変電所の連系設備,06,越前嶺南線,07,西播東岡山線・山崎智頭線,08,阿南紀北直流幹線,09,本四連系線,10,関門連系線,11,北陸フェンス',
        'transitionContextKey': 'DEFAULT',
        'updDaytime': '2021年09月09日 21時20分更新',
        'wExtention.actionType': 'reference'
    }

    r = session.post(url, data=example_formdata, headers=headers)
    print(r)
    print(r.text)


if __name__ == '__main__':
    test_call()
