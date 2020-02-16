import datetime
import graphene
import random
from graphene_django.types import DjangoObjectType
from .models import User, Company, Question, User_Question, Company_Question, Quiz


"""
把6个model都注册成Node
"""


class UserNode(DjangoObjectType):
    class Meta:
        model = User


class CompanyNode(DjangoObjectType):
    class Meta:
        model = Company


class QuestionNode(DjangoObjectType):
    class Meta:
        model = Question


class UserQuestionNode(DjangoObjectType):
    class Meta:
        model = User_Question


class CompanyQuestionNode(DjangoObjectType):
    class Meta:
        model = Company_Question


class QuizNode(DjangoObjectType):
    class Meta:
        model = Quiz


class Query(graphene.ObjectType):
    user = graphene.Field(UserNode, id=graphene.Int())
    users = graphene.List(UserNode)
    company = graphene.Field(CompanyNode, id=graphene.Int())
    companies = graphene.List(CompanyNode)
    question = graphene.Field(QuestionNode, id=graphene.Int())
    questions = graphene.List(QuestionNode)
    quiz = graphene.Field(QuizNode, id=graphene.Int())
    quizzes = graphene.List(QuizNode)

    def resolve_user(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return User.objects.get(pk=id)

        return None

    def resolve_users(self, info, **kwargs):
        return User.objects.all()

    def resolve_company(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Company.objects.get(pk=id)

        return None

    def resolve_companies(self, info, **kwargs):
        return Company.objects.all()

    def resolve_question(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Question.objects.get(pk=id)

        return None

    def resolve_questions(self, info, **kwargs):
        return Question.objects.all()

    def resolve_quiz(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Quiz.objects.get(pk=id)

        return None

    def resolve_quizzes(self, info, **kwargs):
        return Quiz.objects.all()


class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(UserNode)

    @staticmethod
    def mutate(root, info, username, password):
        if len(username) < 6 or len(username) > 20:
            return CreateUser(ok=False, user=None)
        if User.objects.filter(username=username):
            return CreateUser(ok=False, user=None)
        user_instance = User(username=username, password=password)
        user_instance.save()
        return CreateUser(ok=True, user=user_instance)


class GetThreeQuestions(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        company = graphene.ID(required=True)

    ok = graphene.Boolean()
    questions = graphene.List(QuestionNode)

    @staticmethod
    def mutate(root, info, username, company):
        company_questions_set = set(Question.objects.filter(company_question__company_id=company))
        if len(company_questions_set) < 3:
            return GetThreeQuestions(ok=False, questions=[])
        if not User.objects.filter(username=username):
            return GetThreeQuestions(ok=False, questions=[])
        user = User.objects.get(username=username)
        # 获取用户做过的题
        user_questions_set = set(Question.objects.filter(user_question__user=user.id))
        # 获取公司题库中用户没做过的题目，即剩下的题
        questions_undone_set = company_questions_set - user_questions_set

        # 情况一：如果剩下的题超过3道，就从剩下的题目中随机抽取3道，并把这三道题添加到用户题目关系表
        if len(questions_undone_set) > 3:
            # 从剩下的题中随机抽3道
            questions_list = random.sample(questions_undone_set, 3)
            # 把这3道题添加到用户题目关系表里
            for question in questions_list:
                User_Question.objects.create(user=user, question=question)
        
        # 情况二：如果剩下的题不超过3道，就把剩下的n道题都出了，并且在做过的题中出（3-n）道题，并对数据库做相应调整
        else:
            # 把剩下的n道题目全部抽出，打乱顺序
            head_questions_list = random.sample(questions_undone_set, len(questions_undone_set))
            # 获取公司题库中做过的题
            questions_done_set = company_questions_set - questions_undone_set
            # 从做过的题目中随机抽取（3-n）道题，打乱顺序
            tail_questions_list = random.sample(questions_done_set, 3 - len(questions_undone_set))
            # 出的题目包括n道没做过的题和（3-n）道做过的题
            questions_list = head_questions_list + tail_questions_list
            # 把所有做过的题，都标记成没做过（因为做了一轮了，要全部重新做）
            for question in questions_done_set:
                User_Question.objects.filter(user_id=user.id, question=question).delete()
            # 把（3-n）重新出的题，都标记成做过
            for question in tail_questions_list:
                User_Question.objects.create(user_id=user.id, question=question)

        # 把本次面试的用户和公司记录到数据库，以备查询
        quiz_object = Quiz(user=user, company_id=company)
        quiz_object.save()
        return GetThreeQuestions(ok=True, questions=questions_list)


class GetInterviewRecord(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        company = graphene.ID(required=True)

    ok = graphene.Boolean()
    quiz_number = graphene.Int()
    records = graphene.List(QuizNode)

    @staticmethod
    def mutate(root, info, username, company):
        if not Company.objects.filter(id=company):
            return GetInterviewRecord(ok=True, quiz_number=0, records=None)
        if not User.objects.filter(username=username):
            return GetInterviewRecord(ok=True, quiz_number=0, records=None)
        quizzes_queryset = Quiz.objects.filter(user__username=username, company_id=company)
        # 获取面试次数
        # 新建列表，用来存放处理后的数据
        for quiz in quizzes_queryset:
            # 处理面试时间
            if not quiz.quiz_time or not quiz.submit_times or not quiz.duration:
                quiz_time = str(quiz.start_datetime)[:19]
                quiz.quiz_time = quiz_time
                try:
                    submit_times = quiz.submitted_questions.count(",")
                except AttributeError:  # 捕捉 submitted_questions 字段为 None 的情况
                    submit_times = 0
                quiz.submit_times = submit_times
                try:
                    duration_int = (quiz.finish_datetime - quiz.start_datetime).seconds
                    hour = duration_int // 3600
                    minute = duration_int % 3600 // 60
                    second = duration_int % 60
                    duration = '%d小时' % hour * bool(hour) + '%d分' % minute * bool(minute) + '%d秒' % second * bool(second)
                    if not duration:
                        duration = '0秒'
                except TypeError:  # 捕捉 finish_datetime 未记录的情况
                    duration = '非正常退出，无法获取时长'
                # 讲计算结果存入 duration 字段
                quiz.duration = duration
                quiz.save()
        quizzes_queryset = Quiz.objects.filter(user__username=username, company_id=company)
        return GetInterviewRecord(ok=True, quiz_number=len(quizzes_queryset), records=quizzes_queryset)


class FinishInterview(graphene.Mutation):
    class Arguments:
        quiz = graphene.ID(required=True)

    ok = graphene.Boolean()
    quiz_record = graphene.Field(QuizNode)

    @staticmethod
    def mutate(root, info, quiz):
        if not Quiz.objects.filter(id=quiz):
            return FinishInterview(ok=False, quiz_record=None)
        quiz_instance = Quiz.objects.get(id=quiz)
        if quiz_instance.finish_datetime:
            return FinishInterview(ok=False, quiz_record=None)
        # 获取结束时间
        finish_datetime = datetime.datetime.now()
        if (finish_datetime - quiz_instance.start_datetime).seconds > 90 * 60:
            finish_datetime = quiz_instance.start_datetime + datetime.timedelta(seconds=90 * 60)
        # 将结束时间保存到 finish_datetime 字段
        quiz_instance.finish_datetime = finish_datetime
        quiz_instance.save()
        return FinishInterview(ok=True, quiz_record=quiz_instance)


class Submit(graphene.Mutation):
    class Arguments:
        quiz = graphene.ID(required=True)
        question = graphene.ID(required=True)

    ok = graphene.Boolean()
    quiz_record = graphene.Field(QuizNode)

    @staticmethod
    def mutate(root, info, quiz, question):
        if not Quiz.objects.filter(id=quiz):
            return Submit(ok=False, quiz_record=None)
        if not Question.objects.filter(id=question):
            return Submit(ok=False, quiz_record=None)
        quiz_instance = Quiz.objects.get(id=quiz)
        # 如果 submitted_questions 字段为None，则将其变为空字符串''
        if not quiz_instance.submitted_questions:
            quiz_instance.submitted_questions = ''

        # 如果该题目没有提交过，则把题目 id 和逗号加进 submitted_questions 字段
        if str(question) + ',' not in quiz_instance.submitted_questions:
            quiz_instance.submitted_questions += str(question) + ','
        quiz_instance.save()
        return FinishInterview(ok=True, quiz_record=quiz_instance)


class Mutation(graphene.ObjectType):
    get_three_questions = GetThreeQuestions.Field()
    get_interview_record = GetInterviewRecord.Field()
    create_user = CreateUser.Field()
    finish_interview = FinishInterview.Field()
    submit = Submit.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
