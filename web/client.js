// get DOM elements
var iceConnectionLog = document.getElementById('ice-connection-state'),
    iceGatheringLog = document.getElementById('ice-gathering-state'),
    signalingLog = document.getElementById('signaling-state'),
    roundTripTime = document.getElementById('round-trip-time'),
    jitter = document.getElementById('jitter'),
    packetsSent = document.getElementById('packets-sent'),
    packetsLost = document.getElementById('packets-lost'),
    packetSendDelay = document.getElementById('packet-send-delay');

var statistics_interval;

const audioInputSelect = document.querySelector('select#audioSource');

//function to get the available devices for the input source select option
function gotDevices(deviceInfos) {
    for (let i = 0; i !== deviceInfos.length; ++i) {
        const deviceInfo = deviceInfos[i];
        const option = document.createElement('option');
        option.value = deviceInfo.deviceId;
        if (deviceInfo.kind === 'audioinput') {
            option.text = deviceInfo.label || `microphone ${audioInputSelect.length + 1}`;
            audioInputSelect.appendChild(option);
        }
    }
}

//function to hangle the getUserMedia errors
function handleError(error) {
    console.log('navigator.MediaDevices.getUserMedia error: ', error.message, error.name);
}

//code to inizialize the audio input options for the selection
navigator.mediaDevices.enumerateDevices().then(gotDevices).catch(handleError);

// peer connection
var pc = null;
// data channel
var dc = null;

//function that creates the RTCPeerConnection
function createPeerConnection() {
    var config = {
        sdpSemantics: 'unified-plan',
        iceServers: [{
            'urls': 'stun:stun.l.google.com:19302'
        }]
    };

    pc = new RTCPeerConnection(config);

    // register some listeners to help debugging
    pc.addEventListener('icegatheringstatechange', function () {
        iceGatheringLog.textContent += ' -> ' + pc.iceGatheringState;
    }, false);
    iceGatheringLog.textContent = pc.iceGatheringState;

    pc.addEventListener('iceconnectionstatechange', function () {
        iceConnectionLog.textContent += ' -> ' + pc.iceConnectionState;
    }, false);
    iceConnectionLog.textContent = pc.iceConnectionState;

    pc.addEventListener('signalingstatechange', function () {
        signalingLog.textContent += ' -> ' + pc.signalingState;
    }, false);
    signalingLog.textContent = pc.signalingState;

    return pc;
}

//function that create the offer and proceds with the signaling to complete the connection
function negotiate() {
    return pc.createOffer().then(function (offer) {
        return pc.setLocalDescription(offer);
    }).then(function () {
        // wait for ICE gathering to complete
        return new Promise(function (resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function () {
        var offer = pc.localDescription;

        //send SDP offer to the server with http request 
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function (response) {
        return response.json();
    }).then(function (answer) {
        return pc.setRemoteDescription(answer);
    }).catch(function (e) {
        alert(e);
    });
}

//function to start the connection
function start() {
    document.getElementById('start').style.display = 'none';
    document.getElementById('audioSource').disabled = true;

    pc = createPeerConnection();
    dc = pc.createDataChannel("datachannel");

    var constraints = {
        audio: true,
        video: false
    };

    //get the audio stream and adds it to the connection
    navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
        stream.getTracks().forEach(function (track) {
            pc.addTrack(track, stream);
        });
        return negotiate();
    }, function (err) {
        alert('Could not acquire media: ' + err);
    });

    document.getElementById('stop').style.display = 'inline-block';
    statistics_interval = setInterval(statistics, 1000)
}

//function to stop the connection
function stop() {
    document.getElementById('start').style.display = 'inline-block';
    document.getElementById('stop').style.display = 'none';
    clearInterval(statistics_interval)
    iceConnectionLog.textContent = '';
    iceGatheringLog.textContent = '';
    signalingLog.textContent = '';
    roundTripTime.textContent = '';
    jitter.textContent = '';
    packetsSent.textContent = '';
    packetsLost.textContent = '';
    packetSendDelay = '';
    document.getElementById('audioSource').disabled = false;

    //close data channel
    if(dc){
        dc.close();
    }

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function (transceiver) {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // close local audio / video
    pc.getSenders().forEach(function (sender) {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(function () {
        pc.close();
    }, 500);
}

//function to collect connection statistics
async function statistics() {
    const stats = await pc.getStats();
    stats.forEach((report) => {
        if (report.type === "remote-inbound-rtp") {
            roundTripTime.textContent = report.roundTripTime.toFixed(6);
            jitter.textContent = report.jitter.toFixed(6);
            packetsLost.textContent = report.packetsLost;
        }
        if (report.type === "outbound-rtp"){
            packetsSent.textContent = report.packetsSent;
            packetSendDelay.textContent = report.totalPacketSendDelay;
        }
    });
}

// Add an event listener to the document for the keydown event
document.addEventListener('keydown', function(event) {
    // Check if the pressed key is the space bar (key " ")
    if (event.key === " ") {
        end_of_turn = Date.now();
        //send the time over the data streaming
        dc.send(end_of_turn);
    }
});