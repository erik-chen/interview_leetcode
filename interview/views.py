import datetime
import random

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from interview.models import Company, Question, Quiz, User, User_Question


def index(request):
	"""
	这是主页的后端代码

	主页的主要功能是 	1.展示所有公司
					2.提供每一家公司的“模拟面试”接口、“面试记录”接口

	主页的次要功能是	1.注册和登陆功能
					2.在未登录时，禁止匿名使用功能

	主页的跳转关系是	1.点选某家公司的“开始一场面试”按钮，跳转到该公司的“模拟面试”界面
					2.点选某家公司的“回看面试记录”按钮，跳转到该公司的“面试记录”界面
					3.未登录状态，点选“注册”按钮，进入注册功能框
					4.未登录状态，点选“登陆”按钮，进入登陆功能框
					5.登陆状态，点选“退出”按钮，跳转到未登录的主页

	"""
	# 情况一：已登录，则从session中获取用户名
	if 'username' in request.session:
		username = request.session.get('username')
	# 情况二：未登录，则用61代替用户名
	else:
		username = 61  # 61作为用户名是非法的，不会被注册到
	# 获取全部公司
	companies_queryset = Company.objects.all()
	# 渲染index.html
	return render(request, 'index.html', {'username': username, 'companies_queryset': companies_queryset})


def interview(request, company_id, interview_question_number=3):
	"""
	这是“模拟面试”界面的后端代码

	该界面的功能是		1.根据公司生成3道面试题目
						2.记录面试信息

	该界面的跳转关系是		1.点选“结束面试”按钮，跳转到主页

	备注：本界面没有用户退出的按钮，因为业务逻辑是：在模拟面试过程中，用户应当结束面试后再退出。

	"""
	# 检查用户是否登录，未登录就切换到主页
	if 'username' not in request.session:
		return HttpResponseRedirect('/')

	# 获取公司题库
	company_questions_set = set(Question.objects.filter(company_question__company_id=company_id))
	# 如果公司题库数量不足3道，则无法出题
	if len(company_questions_set) < interview_question_number:
		HttpResponse('题库数量不足')
	# 获取当前登录用户
	username = request.session.get('username')
	user = User.objects.get(username=username)
	# 获取用户做过的题
	user_questions_set = set(Question.objects.filter(user_question__user=user.id))
	# 获取公司题库中用户没做过的题目，即剩下的题
	questions_undone_set = company_questions_set - user_questions_set

	# 情况一：如果剩下的题超过3道，就从剩下的题目中随机抽取3道，并把这三道题添加到用户题目关系表
	if len(questions_undone_set) > interview_question_number:
		# 从剩下的题中随机抽3道
		questions_list = random.sample(questions_undone_set, interview_question_number)
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
		tail_questions_list = random.sample(questions_done_set, interview_question_number - len(questions_undone_set))
		# 出的题目包括n道没做过的题和（3-n）道做过的题
		questions_list = head_questions_list + tail_questions_list
		# 把所有做过的题，都标记成没做过（因为做了一轮了，要全部重新做）
		for question in questions_done_set:
			User_Question.objects.filter(user_id=user.id, question=question).delete()
		# 把（3-n）重新出的题，都标记成做过
		for question in tail_questions_list:
			User_Question.objects.create(user_id=user.id, question=question)

	# 把本次面试的用户和公司记录到数据库，以备查询
	quiz_object = Quiz(user=user, company_id=company_id)
	quiz_object.save()
	# 渲染quiz.html
	return render(request, 'quiz.html', {'questions_list': questions_list, 'quiz_id': quiz_object.id})


def history(request, company_id):
	"""
	这是“面试记录”界面的后端代码

	该界面的功能是		1.展示所有公司
						2.根据公司回看面试记录

	该界面的跳转关系是		1.点选其他公司的“XX面试记录”按钮，跳转到其他公司的“模拟面试”界面
						2.点选“返回”按钮，跳转到主页
						3.点选“退出”按钮，跳转到未登录的主页

	"""
	# 检查用户是否登录，未登录就切换到主页
	if 'username' not in request.session:
		return HttpResponseRedirect('/')

	# 获取当前登录用户
	username = request.session.get('username')
	# 由于面试的面试时间、提交数、用时都要再处理，因此从 Quiz 表中获取原始数据，处理成直接可用的数据，再传给 html
	# 获取原始数据
	quizzes_queryset = Quiz.objects.filter(user__username=username, company_id=company_id)
	# 获取面试次数
	quiz_number = len(quizzes_queryset)
	# 新建列表，用来存放处理后的数据
	records_list = []
	for quiz in reversed(quizzes_queryset):
		# 处理面试时间
		quiz_time = str(quiz.start_datetime)[:19]
		# 处理提交数
		try:
			submit_times = quiz.submitted_questions.count(",")
		except AttributeError:  # 捕捉 submitted_questions 字段为 None 的情况
			submit_times = 0
		# 处理用时
		# 如果非首次查询，直接从 quiz 表的 duration 字段获取
		if quiz.duration:
			duration = quiz.duration
		# 如果是首次查询，则根据开始时间和结束时间计算出用时，并存入 duration 字段
		else:
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
		# 讲处理过的数据存入列表
		records_list.append(
			{
				'quiz_time': quiz_time,
				'submit_times': submit_times,
				'duration': duration
			}
		)
	# 获取当前公司名称
	company_name = Company.objects.get(id=company_id).name
	# 获取全体公司
	companies_queryset = Company.objects.all()
	# 渲染 history.html
	return render(request, 'history.html', {'username': username, 'quiz_number': quiz_number, 'records_list': records_list, 'company_name': company_name, 'companies_queryset': companies_queryset})


def operation(request):
	"""
	这是用户在模拟面试时，记录面试数据的代码

	功能是	1.用户点击“提交”按钮时，记录提交的题号
			2.用户点击“结束面试”按钮时，记录结束时间

	"""
	action = request.GET.get('action')
	if request.method == 'POST':
		# 情况一：点击“结束面试”按钮或时间满1个半小时
		if action == 'finish':
			# 获取面试对象
			quiz_id = request.POST.get('quizid')
			quiz = Quiz.objects.get(id=quiz_id)
			# 获取结束时间
			finish_datetime = datetime.datetime.now()
			if (finish_datetime - quiz.start_datetime).seconds > 90 * 60:
				finish_datetime = quiz.start_datetime + datetime.timedelta(seconds=90 * 60)
			# 将结束时间保存到 finish_datetime 字段
			quiz.finish_datetime = finish_datetime
			quiz.save()
			return HttpResponse('面试结束')
		# 情况一：点击“提交”按钮
		if action == 'submit':
			# 获取面试对象
			quiz_id = request.POST.get('quizid')
			quiz = Quiz.objects.get(id=quiz_id)
			# 如果 submitted_questions 字段为None，则将其变为空字符串''
			if not quiz.submitted_questions:
				quiz.submitted_questions = ''
			# 获取提交的题目 id
			question_id = request.POST.get('subid')
			# 如果该题目没有提交过，则把题目 id 和逗号加进 submitted_questions 字段
			if question_id + ',' not in quiz.submitted_questions:
				quiz.submitted_questions += question_id + ','
			quiz.save()
			return HttpResponse('提交成功')
	return HttpResponseRedirect('/')


def register(request):
	"""
	这是“注册”功能的代码

	"""
	username = request.POST.get('uid')
	password = request.POST.get('pwd')
	if not username:
		return HttpResponseRedirect('/')
	if User.objects.filter(username=username).exists():
		return HttpResponse('False')
	else:
		User.objects.create(username=username, password=password)
		return HttpResponse('True')


def login(request):
	"""
	这是“登陆”功能的代码

	"""
	username = request.POST.get('uid')
	password = request.POST.get('pwd')
	if not username:
		return HttpResponseRedirect('/')
	if User.objects.filter(username=username, password=password).exists():
		request.session['username'] = username
		return HttpResponse('True')
	else:
		return HttpResponse("FALSE")


def logout(request):
	"""
	这是“退出”功能的代码

	"""
	if "username" in request.session:
		del request.session['username']
	return HttpResponseRedirect('/')

