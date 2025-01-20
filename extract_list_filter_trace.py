"""
A demonstration of how action traces (with observations) can be extracted
for WorkArena tasks without modifying the task code.

Author: Alexandre Drouin (alexandre.drouin@servicenow.com)

Notes:
- This approach relies on monkey patching the playwright actions to log the actions and observations.
  It has not been tested for parallel execution. It might work with multiprocessing, but it will for
  sure not work with multithreading.

"""

import importlib
import logging
import os
import pickle
import playwright.sync_api as playwright_sync

import json
from time import sleep
from browsergym.core.env import BrowserEnv
from browsergym.workarena import ALL_WORKARENA_TASKS
from collections import defaultdict
from tenacity import retry, stop_after_attempt, wait_fixed
from time import time
from tqdm import tqdm

#import os
#os.environ['SNOW_INSTANCE_URL'] = 'https://dev206867.service-now.com/'
#os.environ['SNOW_INSTANCE_UNAME'] = 'admin'
#os.environ['SNOW_INSTANCE_PWD'] = 'fx@U4AYf!k0E'


N_PER_TASK = 5

GLOBAL_OBS_CALLBACK = lambda: None
GLOBAL_TRACE = []


def monkey_patch_playwright():
#(observation_callback, trace_storage):
    """
    A function that overrides the default playwright actions to log the actions and observations.

    Parameters:
    ------------
    observation_callback: callable
        A function that returns the observation of the environment.
    trace_storage: list
        A list to store the trace of the actions and observations.
        These will be appended in-place.

    """

    def wrapper(func, interface):
        def wrapped(*args, **kwargs):
            # Get the observation
            obs = GLOBAL_OBS_CALLBACK()
            # observation_callback()

            # Get the BID of the element on which we are acting.
            if interface.__name__ == "Locator":
                # Get the locator
                locator = args[0]
                # Get the BID
                bid = locator.element_handle().evaluate('(el) => el.getAttribute("bid")')
            elif interface.__name__ == "Keyboard":
                # Get the BID of the element
                bid = "keyboard"
            else:
                # Get the BID of the element
                bid = args[0].evaluate('(el) => el.getAttribute("bid")')

            logging.info(f"Action: {func.__name__} BID: {bid}  --   Args: {args[1:]} {kwargs}")
            
            #trace_storage
            GLOBAL_TRACE.append(
                {
                    "obs": obs,
                    "action": func.__name__,
                    "args": args[1:],
                    "kwargs": kwargs,
                    "bid": bid,
                    "time": time(),
                }
            )

            # Resume action
            return func(*args, **kwargs)

        return wrapped

    # Interfaces and actions we want to monkey patch
    importlib.reload(playwright_sync)
    from playwright.sync_api import Page, Frame, Locator, Keyboard, ElementHandle

    # TODO: Make sure the list of interfaces and actions is exhaustive
    #       It covers all that is used in WorkArena cheats as of April 11, 2024
    interfaces = [Page, Frame, Locator, Keyboard, ElementHandle]
    actions = ["click", "select_option", "set_checked", "fill", "press", "type", "down", "up"]

    for interface in interfaces:
        for action in actions:
            if hasattr(interface, action):
                setattr(interface, action, wrapper(getattr(interface, action), interface))
                print(f"Monkey patched {interface.__name__}.{action}")
                
monkey_patch_playwright()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def extract_trace(task_cls, task_config = None, headless=True):
    """
    Extracts the trace of actions and observations for a given task.

    Parameters:
    ------------
    task_cls: class
        The class of the task to extract the trace from.

    """
    # Instantiate a new environment
    env = BrowserEnv(task_entrypoint=task_cls, task_kwargs = {'fixed_config': task_config}, headless=headless, slow_mo=1000)
    
    #print(task_cls.fixed_config)

    # Setup customized tracing
    trace = []
    #monkey_patch_playwright(observation_callback=env._get_obs, trace_storage=trace)
    
    global GLOBAL_OBS_CALLBACK 
    global GLOBAL_TRACE
    
    GLOBAL_OBS_CALLBACK = env._get_obs
    GLOBAL_TRACE = trace

    env.reset()
    env.task.cheat(env.page, env.chat.messages)
    
    env.close()
    
    return trace


if __name__ == "__main__":
    os.makedirs("trace_profiling", exist_ok=True)

    task_traces = defaultdict(list)
    #for task in ALL_WORKARENA_TASKS:
    task = ALL_WORKARENA_TASKS[-24]
    print("Task:", task)
    with open("./filter_asset_list_task.json") as f:
        data = json.load(f)
    
    for i in tqdm(range(0, len(data))):
        task_config = data[i]
        
        print(f"Extracting trace {i+1}/{len(data)}")
        
        trace = extract_trace(task, task_config, headless=True)
        
        task_traces[task].append(GLOBAL_TRACE)
        pickle.dump(task_traces, open("trace_profiling/task_traces.pkl", "wb"))

    pickle.dump(task_traces, open("trace_profiling/task_traces.pkl", "wb"))
