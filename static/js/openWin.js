// JavaScript Document
/*  data for example
winInfo = {
	title:"标题",
	content:"内容",
	submitBtn:"按钮"
},
contentInfo = {
	temp:"模板节点",
	tempData:{
		模板数据
	}
},
callback
*/
//close open window
	var openwinClose = function(){
		$("#open-window").remove();
	}
	
$.fn.openWin = function(winInfo,contentInfo,submitData){
	var winTemp = $("#openWin").html();
	var winWidth = $(window).width();
	var winHeight = $(window).height();
	var htmlHeight = $("html").height();
	var closeBtn = $("#open-window").find(".close-btn");
	var submitBtn = $("#open-window").find(".submit-btn")
	
    console.log(winTemp)
	//open window
	var winHtml = Mustache.to_html(winTemp,winInfo);
    console.log(winHtml)
	if($("#open-window").length>0){
		$("#open-window").remove();
	}
	$("body").append(winHtml);
	if(contentInfo){
		if(contentInfo.tempData){
			var contentHtml = Mustache.to_html(contentInfo.temp.html(),contentInfo.tempData);
		}else{
			var contentHtml = Mustache.to_html(contentInfo.temp.html(),$(this).data());
		}
		$("#open-window").find(".openwin-content").html(contentHtml);
	}
	$("#open-window").show();
	var winBox = $("#open-window").find(".openwin-box");
	var winMask = $("#open-window").find(".openwin-mask");
	var winBoxHeight = winBox.height();
	var winBoxWidth = winBox.width();
	var winTop = (winHeight-winBoxHeight)/2;
	var winLeft = (winWidth-winBoxWidth)/2;
    console.log(winBoxHeight, winBoxWidth, winTop, winLeft);
	winBox.css({"top":winTop+"px","left":winLeft+"px"});
	if(htmlHeight>winHeight){
		winMask.height(htmlHeight);
	}else{
		winMask.height(winHeight);
	}
	
	//close window
	closeBtn.live("click",function(){
		openwinClose();
	})
	
	//submit data callback
	winBox.on("click", "a.submit-btn", function(){
		submitData();
	})
	
	//scroll effect
	var winBoxPos = parseInt(winBox.css("top"));
	$(window).scroll(function(){
		var winScrollHeight = winBoxPos + $(window).scrollTop() + "px";
		console.log($(window).scrollTop())
		var winScroll = null;
		winScroll = setTimeout(function(){
			winBox.css("top",winScrollHeight);
			clearTimeout(winScroll);
		},100)
	})
	
}

/*
$(function(){
		
	//change my password
	$(".choose_reason").click(function(){
		$(this).openWin({
			title:"修改密码",
			submitBtn:"确认修改"
		},
		{
			temp:$("#myself-password-content")
		},
		function(){
			console.log("ok");
			openwinClose();
		});
	});

})*/
