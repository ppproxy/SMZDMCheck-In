[什么值得买](http://www.smzdm.com/)自动签到脚本
==============

## 功能

* 自动签到
* 签到后可以配置发送邮件提醒

特色:

* 第一次 login 成功后, 会保存 session 信息, 以后签到不需要再次 login, 避免频繁请求
* 使用原生包, 不需要安装依赖

注: 请使用 python3 运行

## 配置方法

编辑 config.ini, 填入对应的 smzdm 帐号, 密码.

填入邮箱信息可以在签到后收到邮件, 签到失败时会收到签到失败的邮件, 方便及时补签. 目前只测试过 QQ 邮箱.

另外使用 QQ 邮箱需要获取特殊的密码(授权吗), 具体请参考[什么是授权码，它又是如何设置？](http://service.mail.qq.com/cgi-bin/help?subtype=1&&no=1001256&&id=28)

如果不使用邮箱, 请将主函数中的 `sendMail(-1, message)` 改成 `pass`

## 配置定时任务

在操作系统上配置定时任务:

```bash
$ chmod +x path/to/smzdm_checkin.py
$ crontab -e

## config to execute the script on 6 and 20 O'clock everyday
0 6,20 * * * cd /home/green/smzdm && python3 smzdm_checkin.py > /tmp/smzdm.log 2>&1

```
