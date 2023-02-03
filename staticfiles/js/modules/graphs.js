function graphshandlehtmxafterSwap(evt){
    if (![undefined, ''].includes(evt.detail.pathInfo.requestPath) && ![undefined, ''].includes(evt.detail.target.id)){
        
    }
}

function dynamicColors(backgroundColor_transparancy, borderColor_transparancy) {
    var r = Math.floor(Math.random() * 255);
    var g = Math.floor(Math.random() * 255);
    var b = Math.floor(Math.random() * 255);
    
    return ["rgba(" + r + "," + g + "," + b + ", " + backgroundColor_transparancy + ")","rgba(" + r + "," + g + "," + b + ", " + borderColor_transparancy + ")"]
};