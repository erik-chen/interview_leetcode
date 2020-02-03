from django.db import models


class User(models.Model):
    """
    表名：用户表
    作用：用来记录所有用户数据

    username字段：     记录用户名，要求不重复
    password字段：     记录密码
    create_date字段：  记录创建时间，自动添加

    """
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=30)
    create_datetime = models.DateTimeField(auto_now_add=True)


class Company(models.Model):
    """
    表名：公司表
    作用：用来记录所有公司数据

    name字段： 记录公司名，要求不重复

    """
    name = models.CharField(max_length=50, unique=True)

    @property
    def avatar(self):
        if self.name == '百度':
            return '/static/baidu.png'
        elif self.name == '腾讯':
            return '/static/qq.png'


class Question(models.Model):
    """
    表名：题目表
    作用：用来记录所有题目数据

    title字段：        记录题目标题，要求不重复
    description字段：  记录题目描述，可以为空

    """
    title = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=1000, null=True)


class User_Question(models.Model):
    """
    表名：用户题目关系表
    作用：用来记录用户和题目的关系（是否做过这道题）

    user字段：     外键，联系用户表
    question字段： 外键，联系题目表

    """
    user = models.ForeignKey(User, on_delete=User)
    question = models.ForeignKey(Question, on_delete=Question)


class Company_Question(models.Model):
    """
    表名：公司题目关系表
    作用：用来记录公司和题目的关系（题目是否在公司题库中）

    company字段：  外键，联系公司表
    question字段： 外键，联系题目表

    """
    company = models.ForeignKey(Company, on_delete=Company)
    question = models.ForeignKey(Question, on_delete=Question)


class Quiz(models.Model):
    """
    表名：测验表（即面试表）
    取名说明：因为interview出现太多了，所以这里叫quiz好了
    作用：用来记录测验信息

    user字段：                 外键，联系用户表
    company字段：              外键，联系公司表
    start_datetime字段：       记录开始时间，自动添加
    finish_datetime字段：      记录结束时间，可以为空（非正常离开就会为空）
    submitted_questions字段：  记录提交的题目，预设为空字符串，可以为空
    duration字段：             记录测试时长，可以为空

    """
    user = models.ForeignKey(User, on_delete=User)
    company = models.ForeignKey(Company, on_delete=Company)
    start_datetime = models.DateTimeField(auto_now_add=True)
    finish_datetime = models.DateTimeField(null=True)
    submitted_questions = models.CharField(max_length=20, default="", null=True)
    duration = models.CharField(max_length=20, null=True)


