/*
 * Requires:
 *     psiturk.js
 *     utils.js
 */

// Initalize psiturk object
var psiTurk = PsiTurk();

// Task object to keep track of the current phase
var currentview;

var replacebody = function(pagehtml) {
	$('body').html(pagehtml);
};

var showpage = function(pagename) {
	psiTurk.getPage(pagename, replacebody);
};


var Drawing = function() {
	
	showpage('test.html');

	var sketchpad = Raphael.sketchpad("editor", {
		width: 400,
		height: 400,
		editing: true
	});
	
	$('.continue').click(function() {
		drawing_data = sketchpad.json(); 
		psiTurk.recordUnstructuredData("drawing_json", drawing_data);
		debriefing();
	});

};


var debriefing = function() { window.location="/debrief?uniqueId=" + psiTurk.taskdata.id; };


/*******************
 * Run Task
 ******************/
$(window).load( function(){
    currentview = new Drawing();
});

// vi: noexpandtab tabstop=4 shiftwidth=4
