from __future__ import annotations

import json
import time
import threading
import requests
from pydantic import BaseModel, Field, model_validator

class RCException(Exception): pass
class User(BaseModel):
    grade: int        # njdm_id  年级代码  njdm_id_xs
    specialty_id: int # zyh_id   专业号    zyh_id_xs
    class Config: extra = "forbid"

class Course(BaseModel):
    course_name: str
    course_id: str    # kch_id   课程号
    class_id: str     # jxb_ids  教学班
    group_id: str     # xkkz_id  选课课组..?
    weight: int       # qz       权重
    class Config: extra = "forbid"


ACCOUNT_PASSWORD_RSA = "<YOUR ENCODED ACCOUNT AND PASSWORD STRING>"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
})
course_list = [
    Course(
        course_name = "乒乓球",
        course_id   = "GBT0005",
        class_id    = "35290618A46256B7E0653B1639231815",
        group_id    = "3D50D978C91F5139E0653B1639231815",
        weight      = 0,
    ),
    Course(
        course_name = "太极拳",
        course_id   = "GBT0011",
        class_id    = "3535E82148032B29E0653B1639231815",
        group_id    = "3D50D978C91F5139E0653B1639231815",
        weight      = 0,
    ),
    Course(
        course_name = "瑜伽",
        course_id   = "GBT0010",
        class_id    = "3529F1EED0595F89E0653B1639231815",
        group_id    = "3D50D978C91F5139E0653B1639231815",
        weight      = 0,
    ),
    Course(
        course_name = "英语 陈英",
        course_id   = "C0EE7FEE7F3F2783E053D8FDA8C047F2",
        class_id    = "358D2E52F33C6000E0653B1639231815",
        group_id    = "3D50E28424B8513BE0653B1639231815",
        weight      = 0,
    )
]


def login():
    print("[0/5] 登录...")
    resp = session.get("https://my.bfsu.edu.cn/tp_up/view?m=up").text
    lt   = resp.split('name="lt" value="', 1)[1].split('"')[0]
    execution = resp.split('name="execution" value="', 1)[1].split('"')[0]

    print("[1/5] 发送账号密码...")
    resp = session.post(
        "https://passport.bfsu.edu.cn/tpass/device",
        data = {
            "ul": 18,
            "pl": 8,
            "rsa": ACCOUNT_PASSWORD_RSA,
            "method": "login"
        }
    ).json()
    if resp["info"] != "ok":
        raise RCException("登录失败.")

    resp = session.post(
        "https://passport.bfsu.edu.cn/tpass/login",
        params = {
            "service": "https://my.bfsu.edu.cn/tp_up/"
        },
        data = {
            "rsa": ACCOUNT_PASSWORD_RSA,
            "ul": 18,
            "pl": 8,
            "lt": lt,
            "execution": execution,
            "_eventId": "submit"
        }
    ).text
    login_succeeded = "手机验证码" not in resp
    if not login_succeeded:
        raise RCException("登录失败.")

    print("[2/5] 登录成功!")
    return session


def login_into_infomation_index():
    print("      跳转到信息主页...")
    resp = session.get("https://jwxt.bfsu.edu.cn/sso/driot4login")
    print("[3/5] 获取学生信息...")
    resp = session.get(
        "https://jwxt.bfsu.edu.cn/jwglxt/xtgl/index_cxYhxxIndex.html",
        params = { # jwglxt = 教务管理系统, cxyhxx = 查询用户信息
            "xt": "jw", # 系统 = 教务
            "localeKey": "zh_CN",
            "gnmkdm": "index" # gnmkdm = 功能模块代码
        }
    ).text
    student_name = resp.split('<h4 class="media-heading">', 1)[1].split("&", 1)[0]
    print(f"[4/5] 学生: {student_name}")


def get_user():
    print("      获取学生的专业 ID 和学年 ID...")
    resp = session.get(
        "https://jwxt.bfsu.edu.cn/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html",
        params = { # cxzzxk = 查询自主选课
            "gnmkdm": "N253512",
            "layout": "default"
        }
    ).text
    njdm_id = int(resp.split('id="njdm_id" value="', 1)[1].split('"')[0])
    zyh_id = int(resp.split('id="zyh_id" value="', 1)[1].split('"')[0])
    njdm_id_xs = int(resp.split('id="njdm_id_xs" value="', 1)[1].split('"')[0])
    zyh_id_xs = int(resp.split('id="zyh_id_xs" value="', 1)[1].split('"')[0])
    assert njdm_id == njdm_id_xs
    assert zyh_id == zyh_id_xs

    print(f"[5/5] 专业 ID: {zyh_id}, 学年 ID: {njdm_id}")
    return User(
        grade = njdm_id,
        specialty_id = zyh_id
    )


def set_weight(course: Course, weight: int):
    session.post(
        "https://jwxt.bfsu.edu.cn/jwglxt/xsxk/zzxkyzb_xkBcQzZzxkYzb.html",
        params = { # xkbcqzzzxk = 选课保存权重自主选课
            "gnmkdm": "N253512"
        },
        data = {
            "jxb_id": course.class_id,
            "qz": weight
        }
    )


def choose_course(user: User, course: Course):
    resp = session.post(
        "https://jwxt.bfsu.edu.cn/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html",
        params = { # xkbczyzzxk = 选课保存专业?志愿?自主选课
            "gnmkdm": "N253512"
        },
        data = {
            "jxb_ids": course.class_id,
            "kch_id": course.course_id,
            "qz": course.weight,
            "xkkz_id": course.group_id,
            "njdm_id": user.grade,
            "zyh_id": user.specialty_id,
            "njdm_id_xs": user.grade,
            "zyh_id_xs": user.specialty_id
        }
    ).json()
    if resp["flag"] == "0":
        errmsg = resp["msg"]
        print(f"\033[0;31m[失败]\033[0m[{course.course_name}]: {errmsg}")
        raise RCException(errmsg)
    if resp["flag"] == "1":
        print(f"\033[0;32m[成功]\033[0m[{course.course_name}]: 选课成功!")
        set_weight(course, 7912)
        return

    print("NotImplemented:", resp)
    raise RCException("NotImplemented")


exited = {}
def rob_course(user: User, course: Course):
    print(f"开始抢课 {course.course_name} 线程.")
    while True:
        # time.sleep(0.1)
        if exited:
            break

        try:
            choose_course(user, course)
            break
        except RCException as exc:
            exc_info = str(exc)
            if exc_info == "一门课程只能选一个教学班，不可再选！":
                break
            if exc_info == "所选教学班的上课时间与其他教学班有冲突！":
                break
            if exc_info == "超过通识选修课本学期本专业最高选课门次限制，不可选！":
                break
            continue


thread_list: list[threading.Thread] = []
def start_robbing_courses(user: User):
    for course in course_list:
        thread = threading.Thread(
            target = rob_course, args = (user, course)
        )
        thread_list.append(thread)
    for thread in thread_list:
        thread.start()


def wait_until_thread_finishes():
    try:
        while thread_list:
            for thread in thread_list.copy():
                thread.join(1)
                if not thread.is_alive():
                    thread_list.remove(thread)
    except KeyboardInterrupt:
        exited["event"] = True




if __name__ == "__main__":
    login()
    login_into_infomation_index()
    user = get_user()
    start_robbing_courses(user)
    wait_until_thread_finishes()
