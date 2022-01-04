window.onload = function() {
    let opened = false;
    var links = document.getElementsByTagName('a');
    let toOpen = "";
    let staticOpen = false;
    let index_id = window.location.href;
    
    url = window.localStorage.getItem(index_id);
    if (url){
        let id = 'school-position-' + url + "done";
        let done = window.localStorage.getItem(id);
        if (url && url.includes("/")){
            if (done !== "true"){
                toOpen = url;
                staticOpen = true;
                opened = true;
            }
        }
    }
    
    for(var i = 0; i< links.length; i++){
        let id = 'school-position-' + links[i].href + "done";
        let done = window.localStorage.getItem(id);
        let href = links[i].href;
        links[i].addEventListener('click', function(){
            onClick(href);
        });
        
        if (done !== "true" && opened == false){
            toOpen = links[i].href;
            opened = true;
        } else if (done == "true"){
            links[i].style.color = "#1b59A8";
            if (opened == true && staticOpen == false){
                toOpen = "";
            }
        }
    }
    if (toOpen){
        let tab = window.open(toOpen,'_blank');
        tab.focus();
    }
}

onClick = function(href) {
    let index_id = window.location.href;
    let url = href;
    window.localStorage.setItem(index_id, url); 
    
};
