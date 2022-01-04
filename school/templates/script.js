var active = false;
var multiple = false;

var id = 'school-position-' + window.location.href;
var id_done = id + 'done'
var position = window.localStorage.getItem(id);
var rate = 1.0;

const defaultImplementation = function(seconds, guide) {
    seconds = seconds < 0 ? 0 : seconds;
    let s = Math.floor(seconds % 60);
    let m = Math.floor(seconds / 60 % 60);
    let h = Math.floor(seconds / 3600);
    const gm = Math.floor(guide / 60 % 60);
    const gh = Math.floor(guide / 3600);

    // handle invalid times
    if (isNaN(seconds) || seconds === Infinity) {
        // '-' is false for all relational operators (e.g. <, >=) so this setting
        // will add the minimum number of fields specified by the guide
        h = m = s = '-';
        }
    // Check if we need to show hours
    h = (h > 0 || gh > 0) ? h + ':' : '';

    // If hours are showing, we may need to add a leading zero.
    // Always show at least one digit of minutes.
    m = (((h || gm >= 10) && m < 10) ? '0' + m : m) + ':';
    // Check if leading zero is need for seconds
    s = (s < 10) ? '0' + s : s;
    return h + m + s;
};

let players = [];


function setup(video_id){
    var player = videojs(video_id);
    if (video_id != "video"){
        player.muted(true);
    }
    
    players.push(player);
    
    document.onkeypress = function (e) {
        if (e.key == 'a'){
            rate = rate + 0.1;
        } else if (e.key == 'z'){
            rate = rate - 0.1
        } else if (e.key == 'e'){
            rate = 2
        }
    };
    
    function formatTime(seconds, guide){
        seconds = seconds / rate;
        guide = guide / rate;
        return defaultImplementation(seconds, guide);
    }
    
    videojs.setFormatTime(formatTime)
    
    if (position){
        var old_onload = window.onload;
        window.onload = function() {
            if (old_onload){
                old_onload();
            }
            player.currentTime(position);
        }
    }
    
    player.on('ratechange', function() {
        rate = player.playbackRate();
    });
    
    player.on('loadedmetadata', function() {
        let ratio = player.videoWidth() / player.videoHeight();
        if (ratio < 4/3 + 0.01){
            let video = document.getElementById(video_id);
            video.className = video.className.replace("vjs-16-9", "vjs-4-3");
            document.getElementsByClassName("videocontent")[0].className = "videocontentsmall";
        }
    });
        
    player.on('play', function() {
        active = true;
        if (!multiple){
            if(!player.isFullscreen()){
                player.requestFullscreen();
            }
        }
    });

    window.onunload = function () {
        var checkpoint = player.currentTime();
        if (checkpoint > player.duration() - 10){
            checkpoint = checkpoint;
            window.localStorage.setItem(id_done, true);
        } else if (active){
            checkpoint -= 10;
            window.localStorage.removeItem(id_done);
        }
            window.localStorage.setItem(id, checkpoint);
        }

    player.on('ended', function() {
        window.localStorage.setItem(id_done, true);
        if (!multiple){
            player.exitFullscreen();
        }
        //window.close();
    });
}
setup("video");

number = 2;
video_name = "video" + number;
video = document.getElementById(video_name);
while(video){
    multiple = true;
    setup(video_name);
    number = number + 1;
    video_name = "video" + number;
    video = document.getElementById(video_name);
}
    
window.onmousewheel = function (e) {
    const up = e.deltaY < 0;
    if (up){
        rate = rate + 0.1;
        }
    else {
        rate = rate - 0.1;
    }
    players.forEach(player => player.playbackRate(rate));
};
