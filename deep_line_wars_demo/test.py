
from collections import deque
import datetime
import numpy as np
import pandas as pd
import shutil
import random
import os
import time
import deep_line_wars


from keras import Sequential
from keras.layers import Dense

from tensorflow.keras.optimizers import Adam



import gym



time = str(datetime.datetime.today())

class DeepLineWarsEnvMultiAgentWrapper:
    # TODO Have not tested this.
    def __init__(self, env):
        self.env = env

    def reset(self):
        return self.env.reset()

    def step(self, actions):
        assert len(actions) == 2, "Must have two items in dict"
        agent_data = {}

        for agent_id, action in actions.items():
            agent_data[agent_id] = self.env.step(action)
            self.env.unwrapped.env.flip_player()
        return agent_data

    def render(self):
        return self.env.render()


class DQN:


    """ Implementation of deep q learning algorithm """

    def __init__(self, action_space, state_space):

        self.action_space = action_space
        self.state_space = state_space
        self.epsilon = 1
        self.gamma = .95
        self.batch_size = 64
        self.epsilon_min = .01
        self.epsilon_decay = .995
        self.learning_rate = 0.001
        self.memory = deque(maxlen=100000)
        self.input_shape = 5
        self.model = self.build_model()
        self.dueling = False

    def build_model(self):
        #  to dense layer på siden av hverandre
        model = Sequential()
        model.add(Dense(64, input_shape=(self.state_space,), activation='relu'))
        model.add(Dense(64, activation='relu'))
        model.add(Dense(self.action_space, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))
        model.trainable = True
        return model


    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):

        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_space)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])

    def replay(self):

        if len(self.memory) < self.batch_size:
            return

        minibatch = random.sample(self.memory, self.batch_size)
        states = np.array([i[0] for i in minibatch])
        actions = np.array([i[1] for i in minibatch])
        rewards = np.array([i[2] for i in minibatch])
        next_states = np.array([i[3] for i in minibatch])
        dones = np.array([i[4] for i in minibatch])

        states = np.squeeze(states)
        next_states = np.squeeze(next_states)

        targets = rewards + self.gamma*(np.amax(self.model.predict_on_batch(next_states), axis=1))*(1-dones)
        targets_full = self.model.predict_on_batch(states)

        ind = np.array([i for i in range(self.batch_size)])
        targets_full[[ind], [actions]] = targets

        self.model.fit(states, targets_full, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def saver(self, episode, returnrewards1, steps):
        df = pd.DataFrame({"episode" : np.arange(episode), "reward p1" : returnrewards1, "steps" : steps})
        df.to_csv("log/"+time +"/numbers.csv", index=False)
        self.model.save("log/"+time +"/model.h5")
        # print("file saved!")

def post_process_state(state, state_space):
    return np.reshape(state, (1, state_space))#/1200

def TrainDQN(num_episodes):
    # Reset environment
    env = gym.make("deeplinewars-deterministic-11x11-v0", env_config=dict(
        window=True,
        gui=False
    ))
    env = DeepLineWarsEnvMultiAgentWrapper(env)

    loss = []
    step_array = []
    reward_array = []
    episode_array = []

    action_space = 12
    state_space = 715
    agent = DQN(action_space, state_space)
    for episode in range(num_episodes):

        state = post_process_state(env.env.reset(), state_space)


        score = 0
        step = 0
        # Set terminal state to false
        terminal = False

        while not terminal:
            # agent.saver(episode, score, step)
            step += 1

            env.render()  # For image you MUST call this
            # next_state, r, t, _
            action = agent.act(state)
            data = env.step(dict(
                agent_1 = action,
                agent_2 = action
            ))
            next_state, r, t, _ = data["agent_1"]
            score += r
            next_state = post_process_state(next_state, (state_space))
            agent.remember(state, action, r, next_state, t)
            state = next_state
            agent.replay()
            # env.env.flip_player()


            loss.append(score)
            # Perform action in environment


            terminal = t






        print(f"Epsisode: {episode} of {num_episodes}")
        step_array.append(step)
        reward_array.append(score)
        episode += 1

        agent.saver(episode, reward_array, step_array)

if __name__ == '__main__':

    # save files to store the hyperparameters that was used
    os.mkdir("log/" + time)
    shutil.copy('Test.py', "log/" + time + '/DQN.txt')

    num_episodes = 1000
    loss = TrainDQN(num_episodes)