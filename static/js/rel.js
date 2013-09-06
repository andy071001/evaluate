// JavaScript Document
$(function(){
	//create address
	$(".choose_reason").click(function(){
        var posturl = $(this).data("posturl");
        var query_item_id  = $(this).data("query_item_id");

        var r_name = '', b_name = '', f_name = '';
        if ($(this).data("source") == "makepolo")
        {
            r_name = 'm_rating_' + query_item_id;
            b_name = 'm_business_' + query_item_id;
            f_name = 'm_free_' + query_item_id;
        }

        if ($(this).data("source") == "alibaba")
        {
            r_name = 'a_rating_' + query_item_id;
            b_name = 'a_business_' + query_item_id;
            f_name = 'a_free_' + query_item_id;
        }
        var m_rating = $("input[name="+r_name+"]:checked");
        var m_business = $("input[name="+b_name+"]:checked");
        var m_free = $("input[name="+f_name+"]:checked");
        var form_data = $(this).data();
        var rating = "";
        var business = "";
        var free = "";


        if (m_rating.length > 0){
            rating = m_rating[0].value;
        }

        if (m_business.length > 0){
            business = m_business[0].value;
        }

        if (m_free.length > 0){
            free = m_free[0].value;
        }

        console.log("rating");
        console.log(rating);
        var tempData = {rating: rating,
                        is_business: business,
                        is_free: free,
                        };
        console.log("tempData");
        console.log(tempData);
        var total_data = $.extend({}, form_data, tempData);
        
		$(this).openWin({
			title:"低分原因备注",
			submitBtn:"确定",
		},
		{
			temp:$("#choose-content"),
		},
		function(){
                var form_data_string = $("#choose_reason_form").serialize();
                var temp_string = "";
                for(var key in tempData){
                    temp_string += '&'+key+'='+tempData[key];
                }
                total_string = form_data_string + temp_string;
                console.log("total string");
                console.log(total_string);
                console.log("tempData");
                console.log(tempData);
		        $.post(posturl, total_string,
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
