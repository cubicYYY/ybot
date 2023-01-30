# A simple library for fetching data from zju school website
# TODO:!! Using BeautifulSoup instead of native Regex matching
# TODO: school official site monitoring
# TODO: exams related stuffs
# TODO: teacher ranking site
# TODO: deadlines query
# TODO: school activities announcement/subscription
# Non-firstplace requirements
# TODO: McDonald tracking
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from collections import namedtuple
from functools import wraps
from dataclasses import dataclass
from itertools import chain
import aiohttp
import execjs
import pickle
import json
import os
import re
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
}
# WEBDRIVER_PATH = "./chromedriver"
# Deprecated, may enable it when using legacy selenium webdriver
ECRYPTION_FILE = os.path.join(PACKAGE_DIR, 'security.js')
CACHE_FILE = os.path.join(PACKAGE_DIR, "{username}.cache")

ZJUAM_URL = "https://zjuam.zju.edu.cn"
LOGIN_URL = ZJUAM_URL + "/cas/login?service=http://jwbinfosys.zju.edu.cn/default2.aspx"
RSA_PUBKEY_URL = ZJUAM_URL + "/cas/v2/getPubKey"

JWBINFO_URL = "http://jwbinfosys.zju.edu.cn"
GRADES_URL = JWBINFO_URL + f"/xscj.aspx"
EXAMS_URL = JWBINFO_URL + f"/xskscx.aspx"

INIT_GRADES_URL = "http://jwbinfosys.zju.edu.cn/default2.aspx"
INIT_EXAMS_URL = "http://jwbinfosys.zju.edu.cn/default2.aspx"

CHALAOSHI_URL = "https://chalaoshi.2799web.com/"
LOGIN_EXPIRED_KEYWORD = r"<title>Object moved</title>"

os.environ["EXECJS_RUNTIME"] = "Node"

Packed = namedtuple('Packed', ['ok', 'data'])


class LoginFailedException(Exception):
    pass


class NotLoggedInError(Exception):
    pass


class LoginStateExpiredException(Exception):
    pass


@dataclass
class Exam:
    code: str | None = None
    name: str | None = None
    term: str | None = None
    time_final: str | None = None
    location_final: str | None = None
    seat_final: str | None = None
    time_mid: str | None = None
    location_mid: str | None = None
    seat_mid: str | None = None
    remark: str | None = None
    is_retake: bool | str | None = None
    credits: float | str | None = None


@dataclass
class Course:
    # WARNING: CHANGE THE ORDER OF ARGS MAY RESULT IN ERROR, SINCE UNPACKING MAY OPERATED ON TUPLE
    code: str | None = None
    name: str | None = None
    score: str | float | None = None
    credit: str | float | None = None
    grade_point: str | float | None = None
    re_exam_score: str | float | None = None
    location: str | None = None
    class_time: str | None = None
    exam: str | None = None
    book: str | None = None
    aliases: str | None = None


class Fetcher(object):
    def __init__(self, username=None, password=None, *, simulated=False):
        self.cookies = {}
        self.exams = []
        self.courses = []
        self.logged = False
        self.username = username
        self.password = password
        self.update_gap = 5 * 60  # seconds
        self.IS_SIMULATED_LOGIN = simulated

    @staticmethod
    def is_float(*args) -> bool:
        """If all the given arguments(strings) are valid float numbers, return True"""
        for num_str in args:
            try:
                _ = float(num_str)
            except ValueError:
                return False
        return True

    def serialize(self, file: str):
        if file is None:
            raise ValueError("No file specified")
        with open(file, 'wb') as f:
            pickle.dump(self.__dict__, file=f)

    def unserialize(self, file: str):
        if file is None:
            raise ValueError("No file specified")
        with open(file, 'rb') as f:
            saved = pickle.load(file=f)
            if not isinstance(saved, dict):
                raise ValueError("Not a valid fetcher store file")
            self.__dict__ = saved

    async def simulated_login(self, username: str, password: str) -> Packed:
        # Not work behind a proxy.
        service = Service(ChromeDriverManager().install())
        options = Options()
        additional_options = [
            '--headless',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            'start-maximized',
            '--disable-extensions',
            '--disable-browser-side-navigation',
            'enable-automation',
            '--disable-infobars',
            'enable-features=NetworkServiceInProcess',
        ]
        for option in additional_options:
            options.add_argument(option)
        driver = webdriver.Chrome(service=service, options=options)
        try:
            driver.get(LOGIN_URL)
            driver.find_element(By.ID, "username").send_keys(username)
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.ID, "dl").click()
            cookies = driver.get_cookies()
        except Exception as e:
            return Packed(False, repr(e))
        else:
            if "iPlanetDirectoryPro" not in str(cookies):
                # Got invalid cookie
                return Packed(False, f"Wrong password/username! cookies:{cookies}")
            else:
                simplified_cookies = {
                    cookie["name"]: cookie["value"] for cookie in cookies}
                return Packed(True, simplified_cookies)

    async def post_login(self, username: str, password: str) -> Packed:
        # @TODO injection prevention
        assert isinstance(password, str)

        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(), headers=DEFAULT_HEADERS) as session:
            # _pv0 cookie need to be carried to get a right key pair
            async with session.get(RSA_PUBKEY_URL) as r:
                res_text = await r.text(encoding='utf-8')
                result = json.loads(res_text)
                modulus_hex: str = result['modulus']
                exponent_hex: str = result['exponent']
                for _, cookie in r.cookies.items():
                    session.cookie_jar.update_cookies(
                        {cookie.key: cookie.value})

            enc_script = open(ECRYPTION_FILE, encoding="utf-8").read()
            ctx = execjs.compile(enc_script)
            encrypted_pwd = ctx.call(
                "zjuish_encryption", password, exponent_hex, modulus_hex)

            async with session.get(LOGIN_URL) as r:  # get the 'execution' segment
                res_text = await r.text(encoding='utf-8')
                execution = re.search(
                    r'name="execution" value="(.*?)"', res_text).group(1)
                for _, cookie in r.cookies.items():
                    session.cookie_jar.update_cookies(
                        {cookie.key: cookie.value})
            data = {
                'username': username,
                'password': encrypted_pwd,
                'authcode': '',
                            'execution': execution,
                            '_eventId': 'submit'
            }
            async with session.post(LOGIN_URL, data=data, allow_redirects=True) as r:  # login
                for _, cookie in r.cookies.items():
                    session.cookie_jar.update_cookies(
                        {cookie.key: cookie.value})
            cookies = session.cookie_jar.filter_cookies(ZJUAM_URL)
            if "iPlanetDirectoryPro" not in str(cookies):
                # Got invalid cookie
                return Packed(False, f"Wrong password/username! Status Code:{r.status}\
                    (expected to be 302) , cookies:{cookies}")
            else:
                simplified_cookies = {
                    cookie.key: cookie.value for _, cookie in cookies.items()}
                return Packed(True, simplified_cookies)

    async def login(self, username, password):
        self.cookies = {}
        if self.IS_SIMULATED_LOGIN == True:
            login_result = await self.simulated_login(username, password)
        else:
            login_result = await self.post_login(username, password)
        if not login_result[0]:
            raise LoginFailedException(
                "Login failed. Maybe the password or username is NOT correct?")
        else:
            self.cookies = login_result[1]
            self.logged = True
            self.username = username
            self.password = password
            self.serialize(CACHE_FILE.format(username=self.username))

    @staticmethod
    # FIXME: The cache may be out-dated and need to be updated as some points
    def login_acquired(func):
        @wraps(func)
        def _impl(self, *args, **kwargs):  # TODO: type checking
            if not self.logged or self.username is None:
                try:
                    self.unserialize(CACHE_FILE.format(
                        username=self.username))
                except FileNotFoundError:
                    pass
                except:
                    print(
                        "WARNING: Unable to recover cache file for login infos. Is it be modified inadvertently?")
                    pass
            if not self.logged:
                if self.password is not None and self.username is not None:
                    self.login(self.username, self.password)
                if not self.logged:
                    raise NotLoggedInError("You shall log-in first.")
            try:
                res = func(self, *args, **kwargs)
                return res
            except LoginStateExpiredException:
                self.login(self.username, self.password)
                res = func(self, *args, **kwargs)
                return res
        return _impl

    @login_acquired
    async def get_exams(self, year: str | None = None, term: str | None = None):
        """Get student exams info(time, form, remark).\n
        If year or term arg is left as None, it means: all!
        """
        # headers["Content-Type"] = "application/x-www-form-urlencoded"
        # headers["Referer"] = EXAMS_URL + f"?xh={self.username}"
        # headers["Connection"] = "keep-alive"
        # headers["Origin"] = "http://jwbinfosys.zju.edu.cn"
        headers = DEFAULT_HEADERS | {
            "Accept": """text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9""",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
            "Proxy-Connection": "keep-alive",
        }

        async with aiohttp.ClientSession(cookies=self.cookies, headers=headers) as session:
            async with session.get(INIT_EXAMS_URL) as r:
                # get ASP.NET_SessionID cookie
                res_text = await r.text()
                for _, cookie in r.cookies.items():
                    session.cookie_jar.update_cookies(
                        {cookie.key: cookie.value})
                    self.cookies[cookie.key] = cookie.value

            async with session.get(EXAMS_URL + f"?xh={self.username}") as r:
                res_text = await r.text()
                if LOGIN_EXPIRED_KEYWORD in res_text:
                    raise LoginStateExpiredException

            # print(res_text)
            if year is None:
                # get all possible years
                year_seg_pattern = r'id="xnd">(.*?)</select>'
                print(res_text, file=open('1.tmp', "w"))
                year_seg = re.search(
                    year_seg_pattern, res_text, flags=re.DOTALL | re.M).group(1)
                value_pattern = r'value="(.*?)"'
                years = re.findall(value_pattern, year_seg,
                                   flags=re.DOTALL | re.M)
            else:
                years = [year]

            if term is None:
                # get all possible terms
                term_seg_pattern = r'id="xqd">(.*?)</select>'
                term_seg = re.search(
                    term_seg_pattern, res_text, flags=re.DOTALL | re.M).group(1)
                value_pattern = r'value="(.*?)"'
                terms = re.findall(value_pattern, term_seg,
                                   flags=re.DOTALL | re.M)
            else:
                terms = [term]
            print("y:", years, "t:", terms)

            # Chaining all exams in a iterator
            res_iter = iter(())
            for year in years:
                for term in terms:
                    viewstate = re.search(
                        r'name="__VIEWSTATE" value="(.*?)"', res_text).group(1)
                    data = {
                        "__EVENTTARGET": "xnd",
                        "__EVENTARGUMENT": "",
                        "__VIEWSTATE": viewstate,
                        "xnd": year,
                        "xqd": term,
                    }
                    encoded_data = aiohttp.FormData(data, charset="gb2312")
                    async with session.post(EXAMS_URL + f"?xh={self.username}", data=encoded_data) as r:
                        res_text = await r.text()
                        # print(res_text, file=open("./tmp1.tmp", "w", encoding='utf-8'))
                    exam_seg_pattern = r'class="datagridhead">.*?</tr>(.*?)</table></div>'
                    exam_seg = re.search(
                        exam_seg_pattern, res_text, flags=re.M | re.DOTALL)
                    if exam_seg is None:
                        continue
                    else:
                        exam_seg = exam_seg.group(1)

                    exam_extract_pattern = r"""<td>(?P<code>.*?)</td><td>(?P<course_name>.*?)</td><td>(?P<credits>.*?)</td><td>(?P<is_retake>.*?)</td><td>(?P<student_name>.*?)</td><td>(?P<term>.*?)</td><td>(?P<time_final>.*?)</td><td>(?P<location_final>.*?)</td><td>(?P<seat_final>.*?)</td><td>(?P<time_mid>.*?)</td><td>(?P<location_mid>.*?)</td><td>(?P<seat_mid>.*?)</td><td>(?P<remark>.*?)</td>"""

                    def exclude_nbsp(s: str) -> str | None:
                        if "&nbsp;" in s:
                            return None
                        else:
                            return s
                    res_iter = chain(res_iter,
                                     (Exam(code=exclude_nbsp(exam['code']),
                                           name=exclude_nbsp(
                                               exam['course_name']),
                                           term=exclude_nbsp(exam['term']),
                                           credits=exclude_nbsp(
                                         exam['credits']),
                                         is_retake=(lambda x: "&nbsp;" not in x)(
                                         exam['is_retake']),
                                         time_final=exclude_nbsp(
                                         exam['time_final']),
                                         location_final=exclude_nbsp(
                                         exam['location_final']),
                                         seat_final=exclude_nbsp(
                                         exam['seat_final']),
                                         time_mid=exclude_nbsp(
                                         exam['time_mid']),
                                         location_mid=exclude_nbsp(
                                         exam['location_mid']),
                                         seat_mid=exclude_nbsp(
                                         exam['seat_mid']),
                                         remark=exclude_nbsp(exam['remark']),
                                     ) for exam in re.finditer(exam_extract_pattern, exam_seg)))
                    # I don't know why the formatter makes it looks like s**t, but let it be
            return res_iter

    @login_acquired
    async def get_timetable(self) -> list[dict]:
        """Get student course timetable"""
        raise NotImplementedError

    @login_acquired
    async def get_grades(self):
        """Get student grades and scores of each course"""
        async with aiohttp.ClientSession(cookies=self.cookies, headers=DEFAULT_HEADERS) as session:
            # @TODO synchronization of self.cookies & parameter is overcomplex. Modify it!
            async with session.get(INIT_GRADES_URL) as r:
                # get ASP.NET_SessionID cookie
                res_text = await r.text()
                for _, cookie in r.cookies.items():
                    session.cookie_jar.update_cookies(
                        {cookie.key: cookie.value})
                    self.cookies[cookie.key] = cookie.value
                    # print(cookie.key, cookie.value)

            async with session.get(GRADES_URL + f"?xh={self.username}") as r:
                res_text = await r.text()
                if LOGIN_EXPIRED_KEYWORD in res_text:
                    raise LoginStateExpiredException
            viewstate = re.search(
                r'name="__VIEWSTATE" value="(.*?)"', res_text).group(1)
            button2 = re.search(
                r'name="Button2" value="(.*?)"', res_text).group(1)
            data = {
                "__VIEWSTATE": viewstate,
                "ddlXN": "",
                "ddlXQ": "",
                "txtQSCJ": "",
                "txtZZCJ": "",
                "Button2": button2,  # text of "在校成绩查询", actually a fixed value
            }

            async with session.post(GRADES_URL + f"?xh={self.username}", data=data) as r:
                text = await r.text()
                pattern = r"<td>(?P<code>.*?)</td><td>(?P<name>.*?)</td><td>(?P<score>.*?)</td><td>(?P<credit>.*?)</td><td>(?P<grade_point>.*?)</td><td>(?P<re_exam_score>.*?)</td>"
                # self.courses = [Course(*course) for course in courses]
                return (Course(code=course['code'],
                               name=course['name'],
                               score=course['score'],
                               credit=course['credit'],
                               grade_point=course['grade_point'],
                               re_exam_score=course['re_exam_score']
                               ) for course in re.finditer(pattern, text))

    @login_acquired
    async def get_all_exams(self):
        return await self.get_exams(None, None)

    @login_acquired
    async def get_GPA(self) -> float:
        credits_sum = 0
        grade_points_sum_weighted = 0.0
        for course in await self.get_grades():
            if self.__class__.is_float(course.score, course.credit, course.grade_point):
                credits_sum += float(course.credit)
                grade_points_sum_weighted += float(course.credit) * \
                    float(course.grade_point)
        if credits_sum != 0:
            return grade_points_sum_weighted / credits_sum
        else:
            return 0.0

    @login_acquired
    async def get_deadlines(self):
        raise NotImplementedError

    @login_acquired
    async def get_activities(self):
        raise NotImplementedError

    @login_acquired
    async def get_notice(self):
        raise NotImplementedError


if __name__ == '__main__':
    async def main():
        username = input("username>>>")
        pwd = input("pwd>>>")
        test = Fetcher(username, pwd, simulated=False)
        print(await test.get_GPA())
        print(list(await test.get_exams()))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
