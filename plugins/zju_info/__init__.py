from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Event, Message, PrivateMessageEvent
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText, EventMessage
from nonebot.plugin import on_command
from nonebot.typing import T_State
import base64
import os
import json
import zju_fetcher as fetchers
from zju_fetcher.school_fetcher import Exam

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

MAX_LEN = 8
ACCOUNT_JSON_FILE = os.path.join(PLUGIN_DIR, 'accounts.json')
print("ACCOUNT_JSON_FILE=", ACCOUNT_JSON_FILE)

gpa = on_command("GPA", rule=lambda: True, aliases={"看看绩点", "gpa"})
chalaoshi = on_command("chalaoshi", rule=lambda: True, aliases={"查老师"})
course = on_command("course", rule=lambda: True, aliases={"查课程", "课程", "查课"})
bind = on_command("bind", rule=lambda: True, aliases={"绑定"})
exam = on_command("exam", rule=lambda: True, aliases={"考试"})

qq_to_account = {}
# initializing
try:
    with open(ACCOUNT_JSON_FILE, "r") as f:
        qq_to_account = json.loads(f.read())
except FileNotFoundError:
    pass
except:
    print("WARNING: Could not recover account JSON file.")
    pass


def is_private_msg(event: Event):
    # message.private
    return isinstance(event, PrivateMessageEvent)


@gpa.handle()
async def handle_gpa(matcher: Matcher, event: Event):
    qq = event.get_user_id()
    if qq not in qq_to_account.keys():
        await matcher.finish("未绑定qq,请先*私聊*进行绑定！")
    username = qq_to_account[qq]['username']
    password = qq_to_account[qq]['password']
    student = fetchers.zju.Fetcher(username, password)
    message = f"{username}的GPA是:{await student.get_GPA():0>.3f}/5.00"
    await matcher.send(message)


@chalaoshi.handle()
async def handle_chalaoshi_first(state: T_State, matcher: Matcher, arg: Message = CommandArg()):
    teacher = arg.extract_plain_text()
    if teacher:
        matcher.set_arg("id", arg)


@chalaoshi.got("id", prompt="你想要查询哪位老师呢？")
async def handle_chalaoshi(state: T_State, matcher: Matcher, teacher: str = ArgPlainText("id")):
    state.setdefault("id", teacher)
    # print("now:",teacher)
    try:
        if teacher and teacher.isdigit():
            tmp_id = int(teacher)
            if 'teachers' not in state.keys():
                teacher_id = tmp_id
            else:
                if tmp_id >= 0 and tmp_id < len(state['teachers']):
                    teacher_id = int(state['teachers'][tmp_id].id)
                else:
                    raise IndexError("Invalid choice")
        else:
            if 'teachers' in state.keys():
                raise IndexError("Invalid choice")
            try:
                state['teachers'] = list(await fetchers.chalaoshi.search_teachers(teacher))
            except Exception as e:
                print(e)
                return
            if len(state['teachers']) == 0:
                await matcher.finish("未找到符合条件的老师……")
            elif len(state['teachers']) == 1:
                teacher_id = state['teachers'][0].id
            else:
                choice_msg = f"""有多位符合条件的老师呢。请输入编号以选择一位："""
                for index, the_teacher in enumerate(state['teachers']):
                    choice_msg += f"""\n{index}.{the_teacher.name}老师  {the_teacher.college} {the_teacher.rating}分"""
                    if index == MAX_LEN:
                        break
                choice_msg += f"""\n(仅显示前{MAX_LEN}条)"""
                await matcher.reject(choice_msg)  # Ask for a choice
    except IndexError:
        await matcher.reject("请好好选一个，谢谢配合")
    the_teacher = await fetchers.chalaoshi.get_teacher_info(teacher_id)
    message = f"""{the_teacher.name}老师 @{the_teacher.college}
学生评价：{the_teacher.rating} ({the_teacher.rating_count:.0f}人评价)
点名可能性：{the_teacher.taking_rolls_likelihood}%
"""
    if the_teacher.grades_per_course:
        message += "\n✳课程给分情况："
    for course, stats in the_teacher.grades_per_course.items():
        message += f"""\n{course:<6}: 均绩{stats.avg_grade_points:>.02f}/5.00"""
    await matcher.finish(message)


@course.handle()
async def handle_course_first(state: T_State, matcher: Matcher, arg: Message = CommandArg()):
    teacher = arg.extract_plain_text()
    if teacher:
        matcher.set_arg("query", arg)


@course.got("query", prompt="你想要查询哪门课程呢？")
async def handle_course(matcher: Matcher, course: str = ArgPlainText("query")):
    res = await fetchers.chalaoshi.get_course_info(course)
    if isinstance(res, int):
        await matcher.finish(f"发生错误。HTTP状态码:{res}")
        return
    teachers_of_course = list(res)
    msg = ""
    if len(teachers_of_course) == 0:
        msg = "似乎并没有相关数据呢。"
    else:
        msg = "教学此门课的老师如下："
        for index, teacher in enumerate(teachers_of_course):
            msg += f"""\n{teacher.teacher_name:<4}  平均绩点{teacher.avg_grade_points:<4}  \
标准差{teacher.sigma:<4} ({teacher.rating_count:<5}人评分)"""
            if index == MAX_LEN:
                break
    if len(teachers_of_course) > MAX_LEN:
        msg += f"\n(超出上限，仅显示前{MAX_LEN}条)"
    await matcher.finish(msg)


@bind.handle()
async def bind_first(state: T_State, matcher: Matcher, event: Event, arg: Message = CommandArg(), msg: Message = EventMessage()):
    if not is_private_msg(event):
        await matcher.finish("请私聊进行绑定：你也不想大伙登进你的学在浙大吧？")
    args = str(arg).lstrip(" ").rstrip(" ").split(" ")

    args = list(filter(lambda x: x != "", args))

    if len(args) > 2:
        await matcher.finish("非法的格式喵。最多两个参数です。")

    if len(args) >= 1:
        matcher.set_arg("username", Message(args[0]))
        if len(args) == 2:
            matcher.set_arg("password", Message(args[1]))


@bind.got("username", prompt="请输入学号的Base64编码")
async def bind_username(matcher: Matcher, event: Event, username: str = ArgPlainText("username")):
    qq = event.get_user_id()
    qq_to_account.setdefault(qq, {})
    try:
        qq_to_account[qq]["username"] = base64.decodebytes(
            bytes(username, encoding="utf-8")).decode('utf-8')
    except:
        await matcher.finish("绑定失败。提请注意：输入的学号密码均需经过Base64编码")


@bind.got("password", prompt="请输入密码的Base64编码")
async def bind_password(matcher: Matcher, event: Event, password: str = ArgPlainText("password")):
    qq = event.get_user_id()
    qq_to_account.setdefault(qq, {})
    try:
        qq_to_account[qq]["password"] = base64.decodebytes(
            bytes(password, encoding="utf-8")).decode('utf-8')
    except:
        await matcher.finish("绑定失败。提请注意：输入的学号密码均需经过Base64编码")
    # print(qq_to_account[qq])
    with open(ACCOUNT_JSON_FILE, "w") as f:
        f.write(json.dumps(qq_to_account))
    await matcher.finish(f"""Done!用户名开头{qq_to_account[qq]["username"][0]}，密码开头{qq_to_account[qq]["password"][0]}""")

@exam.handle()
async def handle_exam(matcher: Matcher, event: Event):
    qq = event.get_user_id()
    if qq not in qq_to_account.keys():
        await matcher.finish("未绑定qq,请先*私聊*进行绑定！")
    username = qq_to_account[qq]['username']
    password = qq_to_account[qq]['password']
    student = fetchers.zju.Fetcher(username, password)
    msg = "考试列表："
    for exam in await student.get_all_exams():
        if exam.time_final is not None or exam.time_mid is not None:
            msg += f"\n{exam.name} 期末：{exam.time_final}@【{exam.location_final}】No.{exam.seat_final}"
            if exam.time_mid is not None:
                msg += f"期中：{exam.time_mid}@【{exam.location_mid}】No.{exam.seat_mid}"
        
    await matcher.finish(msg)
    