from typing import Callable, Tuple, List


def run_processes(opts: List[Tuple[Callable, Tuple]]):
    import multiprocessing

    processes = [
        multiprocessing.Process(target=opt[0], args=opt[1])
        for opt in opts
    ]

    [routine.start() for routine in processes]
    [routine.join() for routine in processes]
