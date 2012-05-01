// ViewPort parent class
function ViewPort(element, id) {
    if (element && id) {
	this.element = element; 
	this.id = id;
	this.init();
    }
}
ViewPort.prototype = {
    constructor: ViewPort,
    init: function() {
	var html_str = this.composeHTML();
	this.element.html(html_str);
    }, // end init
    composeHTML: function() {
	return '<span id='+this.id+' class="view_port"></span>';
    }, // end composeHTML
    addRecord: function(records) {
	if (!(records instanceof Array)) {
	    records = [records];
	}
	var record_str = "";
	for (var i in records) {
	    record_str += '<span>'+records[i]+'</span>';
	}
	$('#'+this.id).append(record_str);
    },
    clearRecord: function() {
	$('#'+this.id).html("");
    }
};


// ScrollTable child class
// constructor
// element should be a jQuery selection of an empty DOM element (ie. div),
// id is a string, and columns is an object containing column model information
function ScrollTable(element,id,columns) {
    this.element = element;
    this.id = id;
    this.columns = columns;
    this.rows = {};
    this.records = {};
    this.init();
}
// prototype: inherit from ViewPort
var st_proto = new ViewPort();
ScrollTable.prototype = st_proto;
ScrollTable.prototype.constructor = ScrollTable;

// add ScrollTable-specific methods
ScrollTable.prototype.composeHTML = function() {
    // Compose table tags with column headers
    var html_str = '<table class="scroll_table" id="'
                   +this.id+'"><thead class="fixed_header">';
    html_str += '<tr style="position:relative;display:block">'
    for (i in this.columns) {
	col = this.columns[i];

	html_str += '<th class='+col.id;
	if (col.hidden) {
	    html_str += ' style="display:none"';
	}

	var w = col.width; // should convert to pixels

	// Add 16px to the width of the last header element
	// for the scroll bar
	if (i==this.columns.length-1) {
	    w+=16;
	}
	html_str += ' width='+w+'px';
	html_str += '>';

	if (col.swap) {
	    html_str += '<div style="position:relative">'+
		        '<span class="dropdown_icon"></span>'+
	                col.name+'</div>';
	} else { 
	    html_str += col.name;
	}
	
	html_str += '</th>';
    }
    html_str += '</tr></thead>';

    // Add table body
    html_str += '<tbody class="scroll_body" width="100%" '+
                'height="'+ 
                (parseInt(this.element.height())-32) +'px"' +
	        'style="display:block;overflow:auto;position:relative">';

    html_str += '</tbody>';

    html_str += '</table>';

    return html_str;
}; // end composeHTML

ScrollTable.prototype.addRecord = function(records) {
    if (!(records instanceof Array)) {
	records = [records];
    }

    // Get current rows from table
    // This allows the table to keep any classes or formatting
    // added to the row after it was created
    var tbody = $('#'+this.id+' tbody');
    var all_rows = this.rows;
    tbody.find("tr").each(function(){
	    var key = $(this).attr('id');
	    all_rows[key] = $(this).wrap('<div>').parent().html();
	}); // end find/each tr

    for (var i in records) {

	var record = records[i];

	// Add the record to the stored records object
	this.records[record['key']] = record;

	// Generate a table row from input data
	var table_row = "";

	// Give it an id corresponding to the key specified in the record
	table_row += '<tr id="'+record['key']+'">';

	var sort_col = null;
	for (var j in this.columns) {
	    col = this.columns[j];
	    if (col.sort && !sort_col) {
		sort_col = col;
	    }
	    if (col.hidden) {
		table_row += '<td class="'+col.id+
		             '" width="'+col.width+'px" style="display:none">'+
		             record[col.field]+'</td>';
	    } else {
		table_row += '<td class="'+col.id+
		             '" width="'+col.width+'px">'+record[col.field]+'</td>';
	    }
	}
	table_row += '</tr>';
	
	// Add the new row to the list of rows
	all_rows[record['key']] = table_row;
    }

    var ordering = [];
    for (i in this.records) {
	ordering.push(this.records[i]);
    }
    // If desired, sort by the field in the sort column
    if (sort_col) {
	ordering.sort(function(a,b){
	    if (a[sort_col.field] < b[sort_col.field]) {
		return -1;
	    }
	    if (a[sort_col.field] > b[sort_col.field]) {
		return 1;
	    }
	    return 0;
	}); // end sort
    }

    // Compose an html string containing all rows
    var rows_str = "";
    for (i in ordering) {
	rows_str += all_rows[ordering[i]['key']];
    }

    // Replace the tbody with these rows
    tbody.html(rows_str);

    // Check for overflow: if none, add 16px to all elements
    // in the  last table column 
    var last_col = this.columns[this.columns.length-1];
    if (tbody[0].clientHeight==tbody[0].scrollHeight) {
	$('#'+this.id+' td.'+last_col.id).attr(
	    "width",(last_col.width+16)+"px");
    } else {
	$('#'+this.id+' td.'+last_col.id).attr(
	    "width",last_col.width+"px");
    }

}; // end addRecord

ScrollTable.prototype.clearRecord = function() {
    // Clear out the tbody, leaving the thead alone
    $('#'+this.id+' tbody').html("");

    // Reset records and rows objects
    this.records = {};
    this.rows = {};
}; // end clearRecord



// TimePlot child class
// constructor
// element should be a jQuery selection of an empty DOM element (ie. div),
// id is a string, and columns is an object containing column model information
function TimePlot(element,id,options) {
    this.element = element;
    this.id = id;
    this.options = options;
    this.plot = null;
    this.null_plot = true;
    this.init();
}
// prototype: inherit from ViewPort
var tp_proto = new ViewPort();
TimePlot.prototype = tp_proto;
TimePlot.prototype.constructor = TimePlot;

// add TimePlot-specific methods
TimePlot.prototype.init = function(record) {

    // Add an empty div to the element
    var html_str = this.composeHTML();
    this.element.html(html_str);

    // Create an empty jqPlot in the element
    this.addRecord();

}; // end init

TimePlot.prototype.composeHTML = function() {
    return '<div id='+this.id+' class="time_plot"></div>';
}; // end composeHTML


TimePlot.prototype.addRecord = function(records) {

    // If there is an existing plot, get its data, then destroy it
    var data_dict = {};
    if (this.plot) {
	if (!this.null_plot) {
	    data_dict = this.plot.data_dict;
	}
	this.plot.destroy();
    }

    var mindate = this.options.mindate;
    var maxdate = this.options.maxdate;
    var series_colors;

    // record: eg. {series:'v', date:'...', data:0.95, error:0.05}
    if (records) {
	if (!(records instanceof Array)) {
	    records = [records];
	}
	for (var i in records) {
	    var record = records[i];

	    if (data_dict[record['series']]==undefined) {
		data_dict[record['series']] = {};
	    }
	    if (data_dict[record['series']][record['date']]==undefined) {
		data_dict[record['series']][record['date']] = {'data':null,
							       'error':null};
	    }
	    data_dict[record['series']][record['date']]['data'] = 
                record['data'];
	    data_dict[record['series']][record['date']]['error']= 
		record['error'];
	}
    }

    var data = [], band_data = [], series_to_use = [];
    var i, j, series, date, 
        value, error, lower, upper, sdata, ldata, udata, dates;
    ////here -- need to pull out desired series
    for (series in data_dict) {
	series_to_use.push(series);
    }
    for (j in series_to_use) {
	series = series_to_use[j];
	sdata=[], ldata=[], udata=[], dates =[];

	// Pull out dates first and sort them
	for (date in data_dict[series]) {
	    dates.push(date);
	}
	dates.sort();

	for (i in dates) {
	    date = dates[i];
	    value = data_dict[series][date]['data'];
	    error = data_dict[series][date]['error'];
	    lower = value - error;
	    upper = value + error;
	    sdata.push([date,value]);
	    ldata.push([date,lower]);
	    udata.push([date,upper]);
	}
	data.push(sdata);
	if (series_to_use.length==1) {
	    band_data.push(ldata);
	    band_data.push(udata);
	}
    }

    if (data.length>0) {
	this.null_plot = false;
	series_colors = this.options.series_colors;
    } else {
	this.null_plot = true;
	data = [[[mindate,0],[maxdate,0]]];
	series_colors = [this.options.bg_color];
    }

    var config = { "title":this.options.title,
		   axes: { xaxis: {renderer:$.jqplot.DateAxisRenderer,
				   tickOptions:{formatString:"%H:%M",
						angle:-30,
		                                fontSize:"8pt"},
				   tickInterval:"1 hour",
				   tickRenderer:$.jqplot.CanvasAxisTickRenderer,
				   label: this.options.xaxis_label,
				   labelOptions: {fontSize:"10pt",
		                                  textColor:"black"},
				   labelRenderer:$.jqplot.CanvasAxisLabelRenderer,
				   min:mindate,
				   max:maxdate},
			   yaxis: {tickOptions:{formatString:"%0.2f",
		                                fontSize:"8pt"},
				   tickRenderer:$.jqplot.CanvasAxisTickRenderer,
				   label: this.options.yaxis_label,
				   labelOptions: {fontSize:"10pt",
		                                  textColor:"black"},
				   labelRenderer:$.jqplot.CanvasAxisLabelRenderer}
	                 },
		   cursor: {show: true,
			    zoom: true,
			    looseZoom: false,
			    showTooltip: false,
			    useAxesFormatters:false},
		   grid: {background:this.options.bg_color,
			  drawBorder:false,
			  shadow: false},
		   series: [{rendererOptions: {bandData:band_data,
					       highlightMouseOver:false}}],
		   seriesColors: series_colors
                 };

    this.plot = $.jqplot(this.id, data, config);

    // Store the data dictionary in the plot
    this.plot.data_dict = data_dict;

}; // end addRecord

TimePlot.prototype.clearRecord = function() {
    // Clear out old plot
    if (this.plot) {
	this.plot.destroy();
	this.plot = null;
    }
    // Replace with an empty plot
    this.addRecord();

}; // end clearRecord


// TooltipOverlay child class
// constructor
// element should be a jQuery selection of an empty DOM element (ie. div),
// id is a string, and columns is an object containing column model information
function TooltipOverlay(element,id,selection) {
    this.element = element;
    this.id = id;
    this.selection = selection;
    this.messages = {};
    this.init();
}
// prototype: inherit from ViewPort
var to_proto = new ViewPort();
TooltipOverlay.prototype = to_proto;
TooltipOverlay.prototype.constructor = TooltipOverlay;

// add TooltipOverlay-specific methods
TooltipOverlay.prototype.init = function() {

    // Add an empty div to the element
    var html_str = this.composeHTML();

    ////here -- should this append or overwrite?
    this.element.append(html_str);

    // Add mouseenter/mouseleave event handlers to the selection
    var hovering = null;
    var delay = 500;
    var messages = this.messages;
    var tooltip = $("#"+this.id);
    $(document).on("mouseenter",this.selection,function() {
	var trigger = $(this);

	// Calculate position of tooltip
	var tt_left, tt_top;
	var trg_pos = trigger.offset();
	var trg_h =  trigger.outerHeight();
	var trg_w =  trigger.outerWidth();
	var tt_h = tooltip.outerHeight();
	var tt_w = tooltip.outerWidth();
	var screen_w = $(window).width();
	var screen_h = $(window).height();
	var overflow_btm = (trg_pos.top + trg_h + tt_h) - screen_h;
	if (overflow_btm>0) {
	    tt_top = trg_pos.top - tt_h - 5;
	} else {
	    tt_top = trg_pos.top + trg_h + 5;
	}
	var trg_ctr = trg_pos.left + Math.round(trg_w/2);
	var overflow_rt = (trg_ctr + tt_w) - screen_w;
	if (overflow_rt>0) {
	    tt_left = trg_ctr - overflow_rt - 5;
	} else {
	    tt_left = trg_ctr;
	}
	
	// Position tooltip
	tooltip.css({
	    left: tt_left,
	    top: tt_top,
	    position: "absolute"
	});

	// Add the message
	var key = trigger.attr("id");
	if (key==undefined) {
	    key = trigger.parent().attr("id");
	}
	var msg = messages[key];
	if (msg==undefined) {
	    msg = "No message";
	}
	tooltip.text(msg);

	// Set delay so that tooltip does not trigger on 
	// accidental mouseover
	hovering = setTimeout(function() {
	    // Show the tooltip
	    tooltip.show();
	}, delay); // end timeout
    }); // end mouseenter
    $(document).on("mouseleave",this.selection,function() {
	if (hovering) {
	    clearTimeout(hovering);
	    hovering = null;
	}
        tooltip.hide();
    }); // end mouseleave


}; // end init
TooltipOverlay.prototype.composeHTML = function() {
    return '<div id='+this.id+' class="tooltip" style="display:none"></div>';
}; // end composeHTML

TooltipOverlay.prototype.addRecord = function(records) {
    if (!(records instanceof Array)) {
	    records = [records];
    }
    for (var i in records) {
	var record = records[i];
	this.messages[record.key] = record.message;
    }
}; // end addRecord

TooltipOverlay.prototype.clearRecord = function() {
    // Clear any current hovering states
    $(this.selection).mouseout();

    $('#'+this.id).html("");
};
