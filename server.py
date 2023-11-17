import argparse
import json
import logging
import os
import ssl
import uuid
from aiohttp import web
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaRelay
from vad_analyzer import Analyzer

ROOT = os.path.dirname(__file__)
logger = logging.getLogger("pc")
relay_audio = MediaRelay()


class AudioTrackProcessing(MediaStreamTrack):
    """
    Audio stream track that processess AudioFrames from tracks.
    """

    def __init__(self, track: MediaStreamTrack, analyzer: Analyzer):
        """
        Costructor of the AudioTrackProcessing class.

        Args:
            track (MediaStreamTrack): track to process
            analyzer (Analyzer): analyzer that will analyze the track
        """
        super().__init__()
        self.track = track
        self.analyzer = analyzer

    async def recv(self):
        """
        Async function called from addTrack function.
        This function calls the analyze function of the analyzer passed in the constructor on the AudioFrame
        extracted from the track passed in the constructor
        """
        frame = await self.track.recv()
        self.analyzer.analyze(frame)
        return frame


async def index(request):
    """
    Async utility function to serve the index file of the server

    Args:
        request (Request): HTTP request
    Returns:
        Response: HTTP response
    """
    content = open(os.path.join(ROOT, "web/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    """
    Async utility function to serve the javascript file of the index page

    Args:
        request (Request): HTTP request
    Returns:
        Response: HTTP response
    """
    content = open(os.path.join(ROOT, "web/client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def style(request):
    """
    Async utility function to serve the css file of index page

    Args:
        request (Request): HTTP request
    Returns:
        Response: HTTP response
    """
    content = open(os.path.join(ROOT, "web/main.css"), "r").read()
    return web.Response(content_type="text/css", text=content)


async def offer(request):
    """
    Async function to respond to the request of starting the WebRTC connection from the client
    
    Args:
        request (Request): SDP offer to start the connection
    Returns:
        Response: SDP answer in response to the SDP offer
    """

    # get the SDP offer
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()

    def log_info(msg, *args):
        logger.info(pc_id + " " + msg, *args)

    log_info("Created for %s", request.remote)

    # prepare local media
    recorder = MediaBlackhole()
    analyzer = Analyzer()

    # pc connectionstatechange event handler
    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()

    # pc track event handler
    @pc.on("track")
    def on_track(track):
        log_info("Track %s received", track.kind)

        if track.kind == "audio":
            print("Started Listening")
            relayed_audio = relay_audio.subscribe(track) # obtain the relayed track
            # use the addTrack function to call the recv function in the AudioTrackProcessing class on the relayed track
            recorder.addTrack(AudioTrackProcessing(relayed_audio, analyzer)) 

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)  # type: ignore

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC audio / video / data-channels demo"
    )
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    args = parser.parse_args()

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    # enable logging with level INFO
    logging.basicConfig(level=logging.INFO)

    app = web.Application()

    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_get("/main.css", style)
    app.router.add_post("/offer", offer)
    web.run_app(
        app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    )
