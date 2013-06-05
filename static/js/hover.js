
jQuery(function($){
        /*Loop through thumbnails*/
    var loop = '',
        curr,
        next;
    $('.images').mouseover(function(){
        var $this = $(this);
        curr = $('span', $this).filter(function() { return $(this).is(':visible'); });
        loop = setInterval(function(){
            next = curr.nextFirst();
            if (next.length == 0) return;
            curr.fadeOut(40, function() {
                next.fadeIn(40);
                curr = next;
            });
        }, 80);
    }).mouseout(function(){
        clearInterval(loop);
    });
});

/*Get next sibling if it exists. If not, get first sibling. Round &amp; a round we go.*/
jQuery.fn.nextFirst = function(e){
    var next = this.next(e);
    return (next.length) ? next : this.prevAll(e).last();
};