# fetcher from chalaoshi
# TODO:!! Using BeautifulSoup instead of native Regex matching
# TODO: student comments fetching
import asyncio
from functools import wraps
import json
import aiohttp
import re
import random
from dataclasses import dataclass
CHALAOSHI_URL = "https://chalaoshi.2799web.com"
CHALAOSHI_API_URL = "https://api.chalaoshi.2799web.com"
HEADER_POOL = ["Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
               "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
               "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0",
               "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; InfoPath.3; rv:11.0) like Gecko",
               "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
               "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
               "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
               "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
               "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
               "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
               "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
               "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
               "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
               "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
               "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
               "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
               "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
               "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
               "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+",
               "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
               "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
               "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
               "Mozilla/4.0 (compatible; MSIE 6.0; ) Opera/UCWEB7.0.2.37/28/999", ]
global_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
    "sec-ch-ua": "\"Not_A Brand\";v=\"99\", \"Google Chrome\";v=\"109\", \"Chromium\";v=\"109\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "None",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": "areyouhuman=XI30TcQMKjedjhqVmq1IuPxntoT9qwjS9vRn62NbhKZ7Rile1orKK75HV7e8YRYaq_iHQ-R3QllpizjGUkR8_hlrzyM=.Y9TjeQ.KWFpUAKETI-nlcacsM8Wzmvkhxw"

}
global_headers["User-Agent"] = HEADER_POOL[random.randrange(len(HEADER_POOL))]
global_cookies = {
    "areyouhuman": "XI30TcQMKjedjhqVmq1IuPxntoT9qwjS9vRn62NbhKZ7Rile1orKK75HV7e8YRYaq_iHQ-R3QllpizjGUkR8_hlrzyM=.Y9TjeQ.KWFpUAKETI-nlcacsM8Wzmvkhxw", }
# FIXME: Redundant storage for teacher need to be reduced


def persist_cookie(cookie_file=None):  # TODO: make it works for both coroutine&func
    if cookie_file is None:
        raise ValueError("Cookie filename must be specified")

    def wrapper(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            global global_cookies
            if not global_cookies:
                try:
                    with open(cookie_file, "r") as f:
                        global_cookies = json.loads(f.read())
                except:
                    pass
            res = await func(*args, **kwargs)
            if global_cookies:
                with open(cookie_file, "w") as f:
                    f.write(json.dumps(global_cookies))
            return res
        return wrapped
    return wrapper


@dataclass
class InCourseTeacherStats:
    teacher_name: str | None = None
    avg_grade_points: str | float | None = None
    sigma: str | float | None = None
    rating_count: str | int | None = None


@dataclass
class Teacher(object):
    name: str | None = None
    id: str | int | None = None
    college: str | None = None
    rating: str | float | None = None
    rating_count: str | int | None = None
    taking_rolls_likelihood: str | float | None = None
    grades_per_course: dict[str, InCourseTeacherStats] | None = None


@persist_cookie("./chalaoshi.cookie")
async def get_teacher_info(id: int, detailed=False) -> Teacher:
    if not isinstance(id, int):
        raise ValueError("Not a valid teacher id")
    url = f"{CHALAOSHI_URL}/t/{id}/"
    async with aiohttp.ClientSession(headers=global_headers, cookies=global_cookies) as session:
        async with session.get(url) as r:
            txt = await r.text()
            # print(txt)
            teacher_name = re.search(
                r"<h3>(?P<teacher>.*?)</h3>", txt).group(1)
            pattern = r"""<p id="cmcinfo">浙江大学</p>
<p>(?P<college>.*?)</p>.*?</div>
<div class="right">
<h2>(?P<rating>.*?)</h2>
<p>(?P<rating_cnt>.*?)</p>
</div>
</div>
<div>"""
            match_result = re.search(pattern, txt, flags=re.DOTALL)
            # FIXME: using segment name instead of int index
            college = match_result.group(1)
            taking_rolls_likelihood = "N/A"
            tecaher_rating = match_result.group(2)
            teacher_rating_count: str | int = match_result.group(3)
            teacher_rating_count = teacher_rating_count.rstrip("人参与评分")
            if "尚未" in teacher_rating_count:
                teacher_rating_count = 0
            else:
                p = r"""<p>(?P<take_roll>.*)%的人认为该老师会点名<br></p>"""
                taking_rolls_likelihood = re.search(p, txt).group(1)
            pattern = r"""<p class="course_name">(?P<course_name>.*)</p>
</div>
<div class="right">
<p>(?P<course_rating>.*)/(?P<course_rating_count>.*)</p>"""
            # print(match_result)
            grades_per_course = {}
            for course in re.finditer(pattern, txt):
                grades_per_course[course['course_name']] = InCourseTeacherStats(
                    teacher_name=teacher_name,
                    avg_grade_points=course['course_rating'],
                    rating_count=course['course_rating_count'],)
            return Teacher(name=teacher_name,
                           college=college,
                           taking_rolls_likelihood=taking_rolls_likelihood,
                           rating=tecaher_rating,
                           rating_count=teacher_rating_count,
                           grades_per_course=grades_per_course)


@persist_cookie("./chalaoshi.cookie")
async def search_teachers(query: str):
    url = f"{CHALAOSHI_URL}/search"
    async with aiohttp.ClientSession(headers=global_headers, cookies=global_cookies) as session:
        params = {"q": query}
        async with session.get(url, params=params) as r:
            txt = await r.text()
            pattern = r"""ocation='/t/(?P<id>.*)/'">
<div class="left">
<h3>(?P<name>.*)</h3>
<p>(?P<college>.*)</p>
</div>
<div class="right">
<h2>(?P<rating>.*)</h2>"""
            return (Teacher(
                id=teacher['id'],
                name=teacher['name'],
                college=teacher['college'],
                rating=teacher['rating']) for teacher in re.finditer(pattern, txt))


@persist_cookie("./chalaoshi.cookie")
async def get_course_info(name: str):
    global global_cookies
    url = f"{CHALAOSHI_API_URL}/gpa"
    global_headers["User-Agent"] = HEADER_POOL[random.randrange(
        len(HEADER_POOL))]
    async with aiohttp.ClientSession(headers=global_headers, cookies=global_cookies) as session:
        params = {"course": name}
        async with session.get(url, params=params) as r:
            txt = await r.text()
            for _, cookie in r.cookies.items():
                print(cookie.key, cookie.value)
                global_cookies[cookie.key] = cookie.value
            if r.status != 200:
                return r.status
            pattern = r"""<td class="course_name">(?P<teacher_name>.*)</td>
<td>(?P<avg_grade_points>.*)<span style="font-size:smaller">±(?P<sigma>.*)</span></td>
<td>(?P<rating_count>.*)</td>"""
            return (InCourseTeacherStats(**teacher_grade.groupdict()) for teacher_grade in re.finditer(pattern, txt))

if __name__ == '__main__':
    async def main():
        teacher = input("teacher ID >>>")
        print(await get_teacher_info(int(teacher)))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
