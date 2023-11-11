import multiprocessing
from vad_analyzer_multiprocessing import analyze
from server_multiprocessing import main

if __name__ == "__main__":
    queue = multiprocessing.Queue()
    audio_queue = multiprocessing.Queue()
    latency_queue = multiprocessing.Queue()
    server = multiprocessing.Process(target=main, args=(audio_queue, latency_queue, ))
    analyzer = multiprocessing.Process(target=analyze, args=(audio_queue, latency_queue, ))

    server.start()
    analyzer.start()

    server.join()
    analyzer.join()
