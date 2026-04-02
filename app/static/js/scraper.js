  function isBlank(str) {
          return (!str || /^\s*$/.test(str));
  }
  $(".myswap-link").each(function(index ){
          var title;
                  $.ajax({
                  type: 'POST',
                  url: '/Scraper/Scrap',
                  data: {'url': $(this).text() },
                  success: function(_callback){
                     if(_callback.length>6){
                          $(".myswap-link").eq(index).text(_callback);
                          
                    }
                  }
          });
          
  });


$(".myswap-link-test").each(function(index ){
	$(".myswap-link").eq(index).text($.url.decode($(this).text()));
  });
