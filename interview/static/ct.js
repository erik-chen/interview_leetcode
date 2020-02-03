
function dp(){
	document.getElementById('light').style.display='none';
	document.getElementById('light2').style.display='none';
    document.getElementById('fade').style.display='none';
}

function rg(){
	$('#light2').slideDown();
	$('#fade').show();
}

function sh(){
	$('#light').slideDown();
	$('#fade').show();
//	document.getElementById('light').style.display='block';
//	document.getElementById('fade').style.display='block';
}

function cg(id){
	$('.subs').hide();
	$('#sub'+id).show();
	$('#txtselectedsubid').val(id);
	$('#txtanswer').val($('#txtanswersub'+id).val());
}

function register(){
	var uid=$('#txtuid2').val();
	var pwd=$('#txtpwd2').val();
	var pwd2=$('#txtpwd22').val();
	if(!uid||!pwd||!pwd2){
		$('#retmsg2').html('不允许空');
		return;
	}
	if(uid.length<6){
		$('#retmsg2').html('用户名长度不能小于6位');
		return;
	}
	if(pwd.length<8){
		$('#retmsg2').html('密码长度不能小于8位');
		return;
	}
	if(pwd!=pwd2){
		$('#retmsg2').html('两次密码不一致');
		return;
	}
	$.post('/register/',{uid:uid,pwd:pwd},function(r){
		if(r=='False'){
			$('#retmsg2').html('注册失败，该用户名已存在');
		}
		else{
			$('#retmsg2').html('注册成功！请登录');
			//dp();
		}
	});
}

function login(){
	var uid=$('#txtuid').val();
	var pwd=$('#txtpwd').val();
	if(!uid){
		$('#retmsg').html('用户名不能为空！');
		return;
	}
	if(!pwd){
		$('#retmsg').html('密码不能为空！');
		return;
	}
	$.post('/login/',{uid:uid,pwd:pwd},function(r){
		if(r=="FALSE"){
			$('#retmsg').html('用户名或者密码错误！');
		}
		else{
			$('#retmsg').html('登陆成功！');
			window.location.href='/';

		}
	});
}

function btnsubmit(){
	var quizid=$('#txtquizid').val();
	var subid=$('#txtselectedsubid').val();
	var answer=$("#txtanswer").val();
	if(!answer){
		alert('答案不允许为空');
		return;
	}
	$.post('/operation/?action=submit',{quizid:quizid,subid:subid,answer:answer},function(r){
		alert(r);
		$('#txtanswersub'+subid).val(answer);
		$('#txtanswer').val('');
	});
}


function finish(){
	var flag=confirm("确定结束面试吗？");
	if(flag==false){return;}
	var quizid=$('#txtquizid').val();
	$.post('/operation/?action=finish',{quizid:quizid},function(r){
		alert(r);
		window.location.href='/';
	});
}

function autofinish(){
	var quizid=$('#txtquizid').val();
	$.post('/operation/?action=finish',{quizid:quizid},function(r){
		alert(r);
		window.location.href='/';
	});
}


function logcg(company_id){
	alert(company_id);
}


function countTime(delay,id) {
                var leftTime = delay;
                var d, h, m, s, ms;
                if(leftTime >= 0) {
                    d = Math.floor(leftTime / 1000 / 60 / 60 / 24);
                    h = Math.floor(leftTime / 1000 / 60 / 60 % 24);
                    m = Math.floor(leftTime / 1000 / 60 % 60);
                    s = Math.floor(leftTime / 1000 % 60);
                    ms = Math.floor(leftTime % 1000);
                    if(ms < 100) {
                        ms = "0" + ms;
                    }
                    if(s < 10) {
                        s = "0" + s;
                    }
                    if(m < 10) {
                        m = "0" + m;
                    }
                    if(h < 10) {
                        h = "0" + h;
                    }
                    //将倒计时赋值到div中
                document.getElementById(id).innerHTML = h + ":" + m + ":" + s ;
                } else {
                    //将倒计时赋值到div中
                    document.getElementById(id).innerHTML = "已截止";
                    autofinish();
                }
                //递归每秒调用countTime方法，显示动态时间效果
               return leftTime
            }
