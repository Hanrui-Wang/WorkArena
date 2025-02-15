import random

from browsergym.core.env import BrowserEnv
from browsergym.workarena import ALL_WORKARENA_TASKS, LIST_TASKS, LIST_TASKS_SORT
from time import sleep

import pdb

if __name__ == '__main__':

    pdb.set_trace()

    # random.shuffle(LIST_TASKS_SORT)
    task = LIST_TASKS_SORT[0]

    while True:
        print("Task:", task)

        # Instantiate a new environment
        env = BrowserEnv(task_entrypoint=task,
                        headless=False)
        env.reset()

        # Cheat functions use Playwright to automatically solve the task
        env.chat.add_message(role="assistant", msg="On it. Please wait...")
        cheat_messages = []
        env.task.cheat(env.page, cheat_messages)

        # Send cheat messages to chat
        for cheat_msg in cheat_messages:
            env.chat.add_message(role=cheat_msg["role"], msg=cheat_msg["message"])

        # Post solution to chat
        env.chat.add_message(role="assistant", msg="I'm done!")

        # Validate the solution
        reward, stop, message, info = env.task.validate(env.page, cheat_messages)
        if reward == 1:
            env.chat.add_message(role="user", msg="Yes, that works. Thanks!")
        else:
            env.chat.add_message(role="user", msg=f"No, that doesn't work. {info.get('message', '')}")

        sleep(3)
        env.close()


    for task in LIST_TASKS_SORT:
        print("Task:", task)

        # Instantiate a new environment
        env = BrowserEnv(task_entrypoint=task,
                        headless=False)
        env.reset()

        # Cheat functions use Playwright to automatically solve the task
        env.chat.add_message(role="assistant", msg="On it. Please wait...")
        cheat_messages = []
        env.task.cheat(env.page, cheat_messages)

        # Send cheat messages to chat
        for cheat_msg in cheat_messages:
            env.chat.add_message(role=cheat_msg["role"], msg=cheat_msg["message"])

        # Post solution to chat
        env.chat.add_message(role="assistant", msg="I'm done!")

        # Validate the solution
        reward, stop, message, info = env.task.validate(env.page, cheat_messages)
        if reward == 1:
            env.chat.add_message(role="user", msg="Yes, that works. Thanks!")
        else:
            env.chat.add_message(role="user", msg=f"No, that doesn't work. {info.get('message', '')}")

        sleep(3)
        env.close()
