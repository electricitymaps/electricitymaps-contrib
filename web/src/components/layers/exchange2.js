const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-interpolate'),
  require('d3-selection'),
);
const moment = require('moment');

function GIFGroover() {
    "use strict";
    var interlacedBufSize, deinterlaceBuf, pixelBufSize, pixelBuf, st, timerID, currentFrame, currentTime, playing, loading, complete, cancel, disposalMethod, transparencyGiven, delayTime, transparencyIndex, gifWidth, gifHeight, duration, frameTime, playSpeed, nextFrameTime, nextFrame, lastFrame, bgColorCSS, gifSrc, paused, colorRes, globalColourCount, bgColourIndex, globalColourTable;
    const bitValues = new Uint32Array([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]);
    const interlaceOffsets  = [0, 4, 2, 1];
    const interlaceSteps    = [8, 8, 4, 2];
    const frames   = [];
    const comments = [];
    const events   = [];
   
    nextFrameTime  = undefined;
    nextFrame      = null;
    playSpeed      = 1;
    frameTime = duration = gifHeight = gifWidth = 0;
    cancel = complete = loading = playing = false;

    const GIF_FILE = { // gif file data block headers
        GCExt   : 249,
        COMMENT : 254,
        APPExt  : 255,
        UNKNOWN : 1,    // not sure what this is but need to skip it in parser
        IMAGE   : 44,   // This block contains compressed image data
        EOF     : 59,   // This is entered as decimal
        EXT     : 33,
    };

    function Stream(data) {
        var pos = this.pos = 0;
        const dat = this.data = new Uint8Array(data);
        const len = this.data.length;
        this.getString = function (count) { // returns a string from current pos 
            var s = "";
            pos = this.pos;
            while (count--) { s += String.fromCharCode(dat[pos++]) }
            this.pos = pos;
            return s;
        };
        this.readSubBlocks = function () { // reads a set of blocks as a string
            var size, count, data  = "";
            pos = this.pos;            
            while (size !== 0 && pos < len) {
                count = size = dat[pos++];
                while (count--) { data += String.fromCharCode(dat[pos++]) }
            }
            this.pos = pos;            
            return data;
        }
        this.readSubBlocksB = function () { // reads a set of blocks as binary
            var size, count, data = [], idx = 0;
            pos = this.pos;            
             while (size !== 0 && pos < len) {
                count = size = dat[pos++];
                while (count--) { data[idx++] = dat[pos++] }
            }
            this.pos = pos;            
            return data;
        }
    }
    function decodePixels(minSize, data) {
        var i, pixelPos, pos, clear, end, size, busy, key, last, plen, len;
        const bitVals = bitValues;
        const dic     = [];
        pos = pixelPos = 0;
        clear    = bitVals[minSize];
        end      = clear + 1;
        size     = minSize + 1;
        busy     = true;
        for (i = 0; i < clear; i++) { dic[i] = [i] }
        len = end + 1;
        while (busy) { 
            last = key; 
            key = 0;
            for (i = 0; i < size; i++) {
                if (data[pos >> 3] & bitVals[pos & 7]) { key |= bitVals[i] }
                pos++;
            }
            if (key === clear) { // reset the dictionary
                size = minSize + 1;
                len = end + 1;
                for (i = 0; i < end; i++) { dic[i] = [i] }
                dic[end] = [0];
                dic[clear] = [0];
            } else {
                if (key === end) { break }  // THIS IS EXIT POINT
                if (key >= len) { dic[len ++] = [...dic[last], dic[last][0]] }
                else if (last !== clear) { dic[len ++] = [...dic[last], dic[key][0]] }
                plen = dic[key].length;
                for (i = 0; i < plen; i++) { pixelBuf[pixelPos++] = dic[key][i] }
                if (size < 12 && len === bitVals[size]) { size += 1 }
            }
        }
    };

    function createColourTable(count) {
        var i = 0;
        count <<= 2;
        const colours = new Uint8Array(count);
        while (i < count) { 
            colours[i++] = st.data[st.pos++];
            colours[i++] = st.data[st.pos++];
            colours[i++] = st.data[st.pos++];
            colours[i++] = 255;
        }
        return new Uint32Array(colours.buffer);
    }
    function parse (){        // read the header. This is the starting point of the decode and async calls parseBlock
        st.pos              += 6;
        gifWidth             = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        gifHeight            = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        pixelBuf             = new Uint8Array(gifWidth * gifHeight);
        const bitField       = st.data[st.pos++];
        gif.colorRes         = (bitField & 112) >> 4;  //0b1110000
        globalColourCount    = 1 << ((bitField & 7) + 1);
        bgColourIndex        = st.data[st.pos++];
        st.pos++;            // ignoring pixel aspect ratio. if not 0, aspectRatio = (pixelAspectRatio + 15) / 64
        if (bitField & 128) {  // global colour flag
            globalColourTable = createColourTable(globalColourCount);
            const bg   = globalColourTable[bgColourIndex];
            bgColorCSS = bg !== undefined ? `rgb(${bg&255},${(bg>>8)&255},${(bg>>16)&255})` : `black`;
        }
        fireEvent("decodestart", { width : gifWidth, height : gifHeight}, true);
        setTimeout(parseBlock,0);
    }
    function parseAppExt() { // get application specific data.
        st.pos += 1;
        if ('NETSCAPE' === st.getString(8)) { st.pos += 8 }  // ignoring this data. iterations (word) and terminator (byte)
        else { st.pos += 3; st.readSubBlocks() } // 3 bytes of string usually "2.0"
    };
    function parseGCExt() { // get GC data
        st.pos++;
        const bitField    = st.data[st.pos++];
        disposalMethod    = (bitField & 28) >> 2;
        transparencyGiven = bitField & 1 ? true : false; // ignoring bit two that is marked as  userInput???
        delayTime         = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        transparencyIndex = st.data[st.pos++];
        st.pos++;
    };
    function parseImg() {                           // decodes image data to create the indexed pixel image
        function deinterlace(width) {               // de interlace pixel data if needed
            var fromLine, pass, toLine;
            const lines = pixelBufSize / width;
            fromLine = 0;
            if (interlacedBufSize !== pixelBufSize) {  
                deinterlaceBuf = new Uint8Array(pixelBufSize);
                interlacedBufSize = pixelBufSize;
            }
            for (pass = 0; pass < 4; pass++) {
                for (toLine = interlaceOffsets[pass]; toLine < lines; toLine += interlaceSteps[pass]) {
                    deinterlaceBuf.set(pixelBuf.subarray(fromLine, fromLine + width), toLine * width);
                    fromLine += width;
                }
            }
        };
        const frame = {}
        frames.push(frame);
        frame.disposalMethod = disposalMethod;
        frame.time     = duration;
        frame.delay    = delayTime * 10;
        duration      += frame.delay;
        frame.leftPos  = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        frame.topPos   = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        frame.width    = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        frame.height   = (st.data[st.pos++]) + ((st.data[st.pos++]) << 8);
        const bitField = st.data[st.pos++];
        frame.localColourTableFlag = bitField & 128 ? true : false;
        if (frame.localColourTableFlag) { frame.localColourTable = createColourTable(1 << ((bitField & 7) + 1)) }
        if (pixelBufSize !== frame.width * frame.height) { pixelBufSize = frame.width * frame.height }
        if (transparencyGiven) { frame.transparencyIndex = transparencyIndex }
        else { frame.transparencyIndex = undefined }
        decodePixels(st.data[st.pos++], st.readSubBlocksB()); 
        if (bitField & 64) {     
            frame.interlaced = true;
            deinterlace(frame.width);
        } else { frame.interlaced = false }
        processFrame(frame);   
    };
    function processFrame(frame) { // creates a RGBA canvas image from the indexed pixel data.
        var useT, i, pixel, pDat, col;
        frame.image        = document.createElement('canvas');
        frame.image.width  = gifWidth;
        frame.image.height = gifHeight;
        frame.image.ctx    = frame.image.getContext("2d");
        const ct = frame.localColourTableFlag ? frame.localColourTable : globalColourTable;
        lastFrame = lastFrame ? lastFrame : frame;
        useT = (lastFrame.disposalMethod === 2 || lastFrame.disposalMethod === 3) ? true : false;
        if (!useT) { frame.image.ctx.drawImage(lastFrame.image, 0, 0, gifWidth, gifHeight) }
        const cData = frame.image.ctx.getImageData(frame.leftPos, frame.topPos, frame.width, frame.height);
        const ti  = frame.transparencyIndex;
        const dat = new Uint32Array(cData.data.buffer);
        if (frame.interlaced) { pDat = deinterlaceBuf }
        else { pDat = pixelBuf }
        for (i = 0; i < pixelBufSize; i++) {
            pixel = pDat[i];
            if (ti !== pixel) { dat[i] = ct[pixel] }
            else if (useT) { dat[i] = 0 }
        }
        frame.image.ctx.putImageData(cData, frame.leftPos, frame.topPos);
        if (!playing) { gif.image = frame.image }
        lastFrame = frame;
    };
    function cleanup() { // a little house keeping
        lastFrame         = null;
        st                = undefined;
        disposalMethod    = undefined;
        transparencyGiven = undefined;
        delayTime         = undefined;
        transparencyIndex = undefined;
        pixelBuf          = undefined;
        deinterlaceBuf    = undefined;
        pixelBufSize      = undefined;
        deinterlaceBuf    = undefined;
        complete          = true;

    }
    function finnished() { // called when the load has completed
        loading = false;
        if (!playing) {
            currentTime = currentFrame = 0;
            if (frames.length > 0) { gif.image = frames[0].image }
        }
        doOnloadEvent();
        cleanup();
    }
    function canceled () { finnished() }
    function parseExt() {              // parse extended blocks
        const blockID = st.data[st.pos++];
        if      (blockID === GIF_FILE.GCExt)   { parseGCExt() }
        else if (blockID === GIF_FILE.COMMENT) { comments.push(st.readSubBlocks()) }
        else if (blockID === GIF_FILE.APPExt)  { parseAppExt() }
        else {
            if (blockID === GIF_FILE.UNKNOWN) { st.pos += 13 } // skip unknown block
            st.readSubBlocks();
        }
    }
    function parseBlock() { // parsing the blocks
        if (cancel === true) { return canceled() }
        const blockId = st.data[st.pos++];
        if (blockId === GIF_FILE.IMAGE ) {
            parseImg();
            fireEvent("progress", { progress : ((st.pos / st.data.length) * 1000 | 0) / 10, frameCount : frames.length });            
            if (gif.firstFrameOnly) { return finnished() }
        } else if (blockId === GIF_FILE.EOF) { return finnished() }
        else { parseExt() }
        setTimeout(parseBlock,0); 
        
    };
    function cancelLoad() { // cancels the loading. This will cancel the load before the next frame is decoded
        if (complete) { return false }
        return cancel = true;
    }
    function error(message) {
     
        fireEvent("error", {message : message}, false);
        //events.decodestart = events.onload  = undefined;
        loading = false;
    }
    function doOnloadEvent() { // fire onload event if set
        currentTime = currentFrame = 0;
        fireEvent("load", {frameCount : frames.length}, true);
        if (gif.playOnLoad) { gif.play() }
    }
    function dataLoaded(data) { // Data loaded create stream and parse
        st = new Stream(data);
        parse();
    }
    function loadGif(filename) { // starts the load
        var ajax = new XMLHttpRequest();
        gifSrc = filename;
        loading = true;
        ajax.responseType = "arraybuffer";
        ajax.onload = function (e) {
            if (e.target.status === 404) { 
                gifSrc = undefined;
                error("File not found") 
                
            } else if (e.target.status >= 200 && e.target.status < 300 ) { dataLoaded(ajax.response) }
            else { 
                gifSrc = undefined;
                error("Loading error : " + e.target.status) 
                
             }
        };
        ajax.onerror = function (e) { 
            gifSrc = undefined;
            error("File error " + e.message) 
        
        };
        ajax.open('GET', filename, true);
        ajax.send();
    }
    function startLoad(filename) {
        if (gifSrc === undefined) {

            gifSrc = filename;
            setTimeout(()=>loadGif(gifSrc),0);
        } else {
            const message = "GIF is limited to a single load. Create a new GIF object to load another gif."
            error(message);
            console.warn(message);
        }
    }
    function setPlaySpeed(speed) {
        playSpeed = (speed * 100 | 0) / 100;
        nextFrameTime = undefined;
        if (Math.abs(playSpeed) === 0) {
            playSpeed = 0;
            if (playing) { pause() }
        }
    }
    function play() { // starts play if paused
        if (!playing) {
            if (playSpeed === 0) { playSpeed = 1 }
            paused  = false;
            playing = true;
            tick();
        }
    }
    function pause() { // stops play
        paused  = true;
        playing = false;
        clearTimeout(timerID);
        nextFrameTime = undefined;
    }
    function togglePlay(){
        if (paused || !playing) { gif.play() }
        else { gif.pause() }
    }
    function seekFrame(index) { // seeks to frame number.
        clearTimeout(timerID);
        nextFrameTime = undefined;
        nextFrame = null;
        currentFrame = ((index % frames.length) + frames.length) % frames.length;
        if (playing) { tick() }
        else {
            gif.image = frames[currentFrame].image;
            currentTime = frames[currentFrame].time;

        }
    }
    function getFrameAtTime(timeMs) { // returns frame that is displayed at timeMs (ms 1/1000th)
        if (timeMs < 0) { timeMs = 0 }
        timeMs %= duration;
        var frame = 0;
        while (frame < frames.length && timeMs > frames[frame].time + frames[frame].delay) { frame += 1 }
        return frame;
    }
    function seek(time) { // time in Seconds  // seek to frame that would be displayed at time
        clearTimeout(timerID);
        nextFrameTime = undefined;
        nextFrame     = null;
        currentFrame  = getFrameAtTime(time * 1000);
        if (playing) { tick() }
        else {
            currentTime = frames[currentFrame].time;
            gif.image   = frames[currentFrame].image;
        }
    }
    function tick() {
        var delay, frame, framesSkipped = false, delayFix = 0;
        if (playSpeed === 0) {
            gif.pause();
            return;
        } else {
            if (nextFrameTime !== undefined && nextFrame === null){
                const behind = nextFrameTime - performance.now();
                if (behind < -frameTime / 2) {
                    framesSkipped = true;
                    nextFrameTime = ((nextFrameTime + behind  / playSpeed) % duration) + duration; // normalize to positive
                    currentFrame  = getFrameAtTime(nextFrameTime);
                    if (playSpeed < 0) { frame = currentFrame === 0 ?  frames.length - 1 : currentFrame - 1 }
                    else { frame = currentFrame }
                } else if (behind < 0) { delayFix = behind } // always behind as code take time to execute;
            }
            if (! framesSkipped){
                if (playSpeed < 0) {
                    if (nextFrame !== null) { currentFrame = nextFrame }
                    else { currentFrame = currentFrame === 0 ?  frames.length - 1 : currentFrame - 1 }
                    frame = currentFrame === 0 ?  frames.length - 1 : currentFrame - 1;
                } else {
                    if (nextFrame !== null) { currentFrame = nextFrame }
                    frame = currentFrame = (currentFrame + 1) % frames.length;
                }
            }
            delay         = Math.abs(frames[frame].delay / playSpeed) + delayFix;
            frameTime     = Math.abs(frames[frame].delay / playSpeed);
            nextFrameTime = performance.now() + delay;
            gif.image     = frames[currentFrame].image;
            currentTime   = frames[currentFrame].time;
            timerID       = setTimeout(tick, delay);
            nextFrame     = null;
        }
    }
    function fireEvent(name, data, clearEvent = false) {
        if (events["on" + name]) {
            setTimeout(() => {
                data.type = name;
                data.gif = gif;
                events["on" + name](data);
                if (clearEvent) { _removeEventListener(name) }
            }, 0);
        }
    }
    function _addEventListener(name, func) {
        if (typeof func === "function") {
            if (name !== "progress") { func = func.bind(gif) }
            events["on" + name] = func
        };
    }
    function _removeEventListener(name) {
        if (events["on" + name] !== undefined) { events["on" + name] = undefined }
    }
    const gif = {                               // the gif image object
        image          : null,                  // the current image at the currentFrame
        comments       : comments,

        //==============================================================================================================
        // Play status
        get paused()    { return paused },      // true if paused
        get playing()   { return playing },     // true if playing
        get loading()   { return loading },     // true if still loading
        get complete()  { return complete },    // true when loading complete. Does not mean success

        //==============================================================================================================
        // Use to load the gif.
        set src(URL)    { startLoad(URL) },  // load the gif from URL. Note that the gif will only start loading after current execution is complete.
        cancel : cancelLoad,                 // Stop loading cancel() returns true if cancels, false if already loaded

        //==============================================================================================================
        // General properties getters or functions
        get backgroundColor() { return bgColorCSS },// returns the background colour as a CSS color value
        get src()          { return gifSrc },       // get the gif URL
        get width()        { return gifWidth },     // Read only. Width in pixels
        get height()       { return gifHeight },    // Read only. Height in pixels
        get naturalWidth() { return gifWidth },    // Read only. Height in pixels 
        get naturalHeight(){ return gifHeight },    // Read only. Height in pixels 
        get allFrames()    { return frames.map(frame => frame.image) },  // returns array of frames as images (canvas).
        get duration()     { return duration },     // Read only. gif duration in ms (1/1000 second)
        get currentFrame() { return currentFrame }, // gets the current frame index
        get currentTime()  { return currentTime },  // gets the current frame index
        get frameCount()   { return frames.length },// Read only. Current frame count, during load is number of frames loaded
        get playSpeed()    { return playSpeed },    // play speed 1 normal, 2 twice 0.5 half, -1 reverse etc...
        getFrame(index) {                           // return the frame at index 0. If index is outside range closet first or last frame is returned
            return frames[index < 0 ? 0 : index >= frames.length ? frames.length-1 : index].image;
        },

        //==============================================================================================================
        // Shuttle control setters
        set currentFrame(index)   { seekFrame(index) },    // seeks to frame index
        set currentTime(time)     { seek(time) },          // seeks to time
        set playSpeed(speed)      { setPlaySpeed(speed) }, // set the play speed. NOTE speed will not take affect if playing until the current frame duration is up.

        //==============================================================================================================
        // load control flags
        playOnLoad     : true,       // if true starts playback when loaded
        firstFrameOnly : false,      // if true only load the first frame

        //==============================================================================================================
        // events. Please note setting to a non function will be ignored.
        set onload(func)        { _addEventListener("load",func) },       // fires when gif loaded and decode. Will fire if you cancel before all frames are decode.
        set onerror(func)       { _addEventListener("error",func) },      // fires on error
        set onprogress(func)    { _addEventListener("progress",func) },   // fires a load progress event
        set ondecodestart(func) { _addEventListener("decodestart",func) },// event fires when gif file content has been read and basic header info is read (width, and height)  and before decoding of frames begins.

        //==============================================================================================================
        // play controls
        play           : play,       // Start playback of gif
        pause          : pause,      // Pauses gif at currentframe
        seek           : seek,       // Moves current time to position seek(time) time in seconds
        seekFrame      : seekFrame,  // Moves time to frame number time is set to frame start.
        togglePlay     : togglePlay, // toggles play state

    };
    return gif;
}

class ExchangeLayer {
  constructor(selectorId, map) {
    this.canvas = document.getElementById(selectorId);
    this.canvas.style['pointer-events'] = 'none';
    this.map = map;
    this.isDragging = false;

    const gifURL = 'http://localhost:8000/images/arrow-80-animated-0.gif';
    const myGif = GIFGroover(); // creates a new gif
    myGif.onload = (event) => {
      const { gif } = event;
      const ctx = this.canvas.getContext('2d'); // get a rendering context

      // Display loop
      const scale = 0.3;
      const displayGif = () => {
        if (!this.isDragging) {
          ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); // Clear in case the gif is transparent
          const projection = this.map.projection();
          this.data.forEach((d) => {
            const [centerX, centerY] = projection(d.lonlat);
            const rotation = d.rotation + (d.netFlow > 0 ? 180 : 0);
            ctx.setTransform(scale, 0, 0, scale, centerX, centerY);
            ctx.rotate(rotation);
            ctx.drawImage(gif.image, -gif.image.width / 2, -gif.image.height / 2);
          });
        }
        requestAnimationFrame(displayGif);
      };
      requestAnimationFrame(displayGif); // start displaying the gif.
    };
    myGif.src = gifURL;

    /* This is the *map* transform applied at last render */
    this.initialMapTransform = undefined;

    let zoomEndTimeout = null; // debounce events
    map.onDragStart((transform) => {
      if (this.hidden) { return; }
      this.isDragging = true;
      if (zoomEndTimeout) {
        // We're already dragging
        clearTimeout(zoomEndTimeout);
        zoomEndTimeout = undefined;
      } else {
        if (!this.initialMapTransform) {
          this.initialMapTransform = transform;
        }
      }
    });
    map.onDrag((transform) => {
      if (this.hidden) { return; }
      if (!this.initialMapTransform) { return; }
      // `relTransform` is the transform of the map
      // since the last render
      const relScale = transform.k / this.initialMapTransform.k;
      const relTransform = {
        x: (this.initialMapTransform.x * relScale) - transform.x,
        y: (this.initialMapTransform.y * relScale) - transform.y,
        k: relScale,
      };
      this.canvas.style.transform =
        `translate(${relTransform.x}px,${relTransform.y}px) scale(${relTransform.k})`;
    });
    map.onDragEnd(() => {
      if (this.hidden) { return; }
      zoomEndTimeout = setTimeout(() => {
        this.canvas.style.transform = 'inherit';
        this.initialMapTransform = null;
        this.render();
        zoomEndTimeout = undefined;
        this.isDragging = false;
      }, 500);
    });
  }

  setData(arg) {
    this.data = arg.filter(d => d.lonlat);
    return this;
  }

  render() {
    if (!this.data) { return; }

    const width = parseInt(this.canvas.parentNode.getBoundingClientRect().width, 10);
    const height = parseInt(this.canvas.parentNode.getBoundingClientRect().height, 10);
    // Canvas needs to have it's width and height attribute set
    this.canvas.width = width;
    this.canvas.height = height;

    // const unprojection = this.map.unprojection();
    return this;
  }
}

module.exports = ExchangeLayer;
