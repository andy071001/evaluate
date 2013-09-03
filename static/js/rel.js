// JavaScript Document
$(function(){
	//create address
	$(".choose_reason").click(function(){
    console.log('test');
		console.log('in create btn');
		var posturl = $(this).data("posturl");
		$(this).openWin({
			title:"创建新账户",
			submitBtn:"创建账号"
		},
		{
			temp:$("#choose-content")
		},
		function(){
		        $.post(posturl,$("#create_account_form").serialize(),
		        	function(data){
		        		if (data.status == 'success'){
		        			openwinClose();
		        			alert(data.info);
						window.location.reload();
		        				
		        		}else{
		        			alert(data.info);
		        		}
		        	}, 'json');
		});
	});
})
