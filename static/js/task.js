// JavaScript Document
$(function(){
	//create address
	$(".to_delete_task").click(function(){
        var posturl = $(this).data("posturl");
		$(this).openWin({
			title:"删除任务提示",
			submitBtn:"确定",
		},
		{
			temp:$("#delete_task"),
		},
		function(){
		        $.post(posturl, $("#delete_task_form").serialize(),
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

	$(".to_copy_task").click(function(){
        var posturl = $(this).data("posturl");
		$(this).openWin({
			title:"复制任务提示",
			submitBtn:"确定",
		},
		{
			temp:$("#copy_task"),
		},
		function(){
		        $.post(posturl, $("#copy_task_form").serialize(),
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
