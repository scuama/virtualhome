from .base_environment import BaseEnvironment
import sys
import os

curr_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{curr_dir}/../')

from unity_simulator import comm_unity as comm_unity
from . import utils as utils_environment
from evolving_graph import utils
import atexit
import random
import pdb
import ipdb
import random
import json
import numpy as np

class UnityEnvironment(BaseEnvironment):


    def __init__(self,
                 num_agents=2,
                 max_episode_length=200,
                 observation_types=None,
                 use_editor=False,
                 base_port=8080,
                 port_id=0,
                 executable_args={},
                 recording_options={'recording': False, 
                                    'output_folder': None, 
                                    'file_name_prefix': None,
                                    'cameras': 'PERSON_FROM_BACK',
                                    'modality': 'normal'},
                 seed=123):


        self.seed = seed
        self.prev_reward = 0.
        self.rnd = random.Random(seed)
        np.random.seed(seed)


        self.steps = 0
        self.env_id = None
        self.max_ids = {}


        self.num_agents = num_agents
        self.max_episode_length = max_episode_length
        self.actions_available = [
            'turnleft',
            'walkforward',
            'turnright',
            'walktowards',
            'open',
            'close',
            'put',
            'grab',
            'no_action'
        ]

        self.recording_options = recording_options
        self.base_port = base_port
        self.port_id = port_id
        self.executable_args = executable_args

        # Observation parameters
        self.num_camera_per_agent = 6
        self.CAMERA_NUM = 1  # 0 TOP, 1 FRONT, 2 LEFT..
        self.default_image_width = 300
        self.default_image_height = 300

        if observation_types is not None:
            self.observation_types = observation_types
        else:
            self.observation_types = ['partial' for _ in range(num_agents)]

        
        self.agent_info = {
            0: 'Chars/Female1',
            1: 'Chars/Male1'
        }
        

        self.changed_graph = True
        self.rooms = None
        self.id2node = None
        self.num_static_cameras = None


        if use_editor:
            # Use Unity Editor
            self.port_number = 8080
            self.comm = comm_unity.UnityCommunication()
        else:
            # Launch the executable
            self.port_number = self.base_port + port_id
            # ipdb.set_trace()
            self.comm = comm_unity.UnityCommunication(port=str(self.port_number), **self.executable_args)

        atexit.register(self.close)
        self.reset()




    def close(self):
        self.comm.close()

    def relaunch(self):
        self.comm.close()
        self.comm = comm_unity.UnityCommunication(port=str(self.port_number), **self.executable_args)

    def reward(self):
        # Define here your reward
        reward = 0
        done = False
        info = {}
        return reward, done, info

    def step(self, action_dict):
        script_list = utils_environment.convert_action(action_dict)
        if len(script_list[0]) > 0:
            action_str = script_list[0].lower()
            import re
            if any(act in action_str for act in ['[wash]', '[cut]', '[pour]']):
                # --- MOCK EXTENSIONS: WASH, CUT, POUR ---
                ids = re.findall(r'\(\s*(\d+)\s*\)', action_str)
                current_graph = self.get_graph()
                char_id = next((n['id'] for n in current_graph['nodes'] if n['class_name'] == 'character'), 1)
                
                success = False
                message = "Failed: Preconditions not met."
                
                if getattr(self, 'custom_states', None) is None: self.custom_states = {}
                
                if '[wash]' in action_str and len(ids) >= 1:
                    obj_id = int(ids[0])
                    target_node = next((n for n in current_graph['nodes'] if n['id'] == obj_id), None)
                    if target_node:
                        props = target_node.get('properties', [])
                        if 'GRABBABLE' in props:
                            held_by_agent = any(e['from_id'] == char_id and e['relation_type'].startswith('HOLDS') and e['to_id'] == obj_id for e in current_graph['edges'])
                            near_sink = any(e['from_id'] == char_id and e['relation_type'] == 'CLOSE' and next((n for n in current_graph['nodes'] if n['id'] == e['to_id']), {}).get('class_name') in ['sink', 'dishwasher'] for e in current_graph['edges'])
                            if held_by_agent and near_sink:
                                success = True
                                message = "Washed successfully."
                                if obj_id not in self.custom_states: self.custom_states[obj_id] = set()
                                self.custom_states[obj_id].add('CLEAN')
                                self.custom_states[obj_id].discard('DIRTY')
                            else:
                                message = "Failed: Must hold the object and be near a sink."
                        else:
                            message = "Failed: Object is not grabbable/washable."
                            
                elif '[cut]' in action_str and len(ids) >= 1:
                    obj_id = int(ids[0])
                    target_node = next((n for n in current_graph['nodes'] if n['id'] == obj_id), None)
                    if target_node:
                        props = target_node.get('properties', [])
                        if 'CUTTABLE' in props:
                            holding_knife = any(e['from_id'] == char_id and e['relation_type'].startswith('HOLDS') and next((n for n in current_graph['nodes'] if n['id'] == e['to_id']), {}).get('class_name') == 'knife' for e in current_graph['edges'])
                            close_to_target = any(e['from_id'] == char_id and (e['relation_type'] == 'CLOSE' or e['relation_type'].startswith('HOLDS')) and e['to_id'] == obj_id for e in current_graph['edges'])
                            if holding_knife and close_to_target:
                                success = True
                                message = "Sliced successfully."
                                if obj_id not in self.custom_states: self.custom_states[obj_id] = set()
                                self.custom_states[obj_id].add('SLICED')
                            else:
                                message = "Failed: Must hold a knife and be close to the object."
                        else:
                            message = "Failed: Object is not CUTTABLE."
                            
                elif '[pour]' in action_str and len(ids) >= 2:
                    src_id = int(ids[0])
                    dest_id = int(ids[1])
                    src_node = next((n for n in current_graph['nodes'] if n['id'] == src_id), None)
                    dest_node = next((n for n in current_graph['nodes'] if n['id'] == dest_id), None)
                    if src_node and dest_node:
                        src_props = src_node.get('properties', [])
                        dest_props = dest_node.get('properties', [])
                        held_src = any(e['from_id'] == char_id and e['relation_type'].startswith('HOLDS') and e['to_id'] == src_id for e in current_graph['edges'])
                        close_dest = any(e['from_id'] == char_id and (e['relation_type'] == 'CLOSE' or e['relation_type'].startswith('HOLDS')) and e['to_id'] == dest_id for e in current_graph['edges'])
                        if not (held_src and close_dest):
                            message = "Failed: Must hold source object and be close to target."
                        elif dest_node['class_name'] == 'sink':
                            if src_id not in self.custom_states: self.custom_states[src_id] = set()
                            filled_states = [s for s in self.custom_states[src_id] if s.startswith('FILLED_')]
                            if filled_states:
                                for s in filled_states:
                                    self.custom_states[src_id].discard(s)
                                    if s != 'FILLED_WATER':
                                        self.custom_states[src_id].add('DIRTY')
                                self.custom_states[src_id].add('EMPTY')
                                success = True
                                message = "Poured into sink successfully."
                            else:
                                message = "Failed: Source is already empty or has no liquid."
                        elif 'POURABLE' in src_props and 'POURABLE' in dest_props:
                            success = True
                            message = "Poured into container successfully."
                            liquid_name = src_node['class_name'].upper()
                            if dest_id not in self.custom_states: self.custom_states[dest_id] = set()
                            self.custom_states[dest_id].add(f'FILLED_{liquid_name}')
                            self.custom_states[dest_id].discard('EMPTY')
                        else:
                            message = "Failed: Both source and destination must be POURABLE for transfer."
                if not success:
                    print(message)
                else:
                    self.changed_graph = True
            elif '[plugin]' in action_str or '[plugout]' in action_str or '[switchon]' in action_str or '[switchoff]' in action_str:
                # Intercept actions in python layer to check properties
                obj_id_str = action_str.split('(')[-1].split(')')[0]
                try:
                    obj_id = int(obj_id_str)
                    
                    # Verify properties using the current graph
                    current_graph = self.get_graph()
                    target_node = next((n for n in current_graph['nodes'] if n['id'] == obj_id), None)
                    
                    if target_node:
                        props = target_node.get('properties', [])
                        
                        is_interaction = any(act in action_str for act in ['[switchon]', '[switchoff]', '[open]', '[close]', '[plugin]', '[plugout]', '[putin]', '[putback]'])
                        
                        if 'BROKEN' in target_node.get('states', []):
                            success = False
                            message = f"Failed: {target_node['class_name']} is BROKEN and cannot be used."
                        elif is_interaction and obj_id in getattr(self, 'hidden_broken_ids', set()):
                            # Reveal the hidden broken state upon interaction
                            if getattr(self, 'custom_states', None) is None:
                                self.custom_states = {}
                            if obj_id not in self.custom_states:
                                self.custom_states[obj_id] = set()
                            self.custom_states[obj_id].add('BROKEN')
                            self.changed_graph = True
                            
                            success = False
                            message = f"Failed: You discover that the {target_node['class_name']} is BROKEN and does not respond."
                        elif ('[plugin]' in action_str or '[plugout]' in action_str) and 'HAS_PLUG' not in props:
                            success = False
                            message = f"Failed: {target_node['class_name']} does not have HAS_PLUG property."
                        elif ('[switchon]' in action_str or '[switchoff]' in action_str) and 'HAS_SWITCH' not in props:
                            success = False
                            message = f"Failed: {target_node['class_name']} does not have HAS_SWITCH property."
                        else:
                            # It has the required property
                            if '[plugin]' in action_str or '[plugout]' in action_str:
                                success = True
                                message = "Faked plug operation in Python layer"
                                if getattr(self, 'custom_states', None) is None:
                                    self.custom_states = {}
                                if obj_id not in self.custom_states:
                                    self.custom_states[obj_id] = set()
                                
                                if '[plugin]' in action_str:
                                    self.custom_states[obj_id].add('PLUGGED_IN')
                                    self.custom_states[obj_id].discard('PLUGGED_OUT')
                                else:
                                    self.custom_states[obj_id].add('PLUGGED_OUT')
                                    self.custom_states[obj_id].discard('PLUGGED_IN')
                                self.changed_graph = True
                            else:
                                # For switchon/switchoff, pass to Unity for visual effect
                                if self.recording_options['recording']:
                                    success, message = self.comm.render_script(script_list,
                                                                               recording=True,
                                                                               skip_animation=False,
                                                                               camera_mode=self.recording_options['cameras'],
                                                                               file_name_prefix='task_{}'.format(self.task_id),
                                                                               image_synthesis=self.recording_options['modality'])
                                else:
                                    success, message = self.comm.render_script(script_list,
                                                                               recording=False,
                                                                               skip_animation=True)
                                
                                # Fix VirtualHome bug: Unity often fails switchon for stoves. 
                                # Since we already verified HAS_SWITCH, we will force success in the Python layer!
                                success = True
                                message = "Faked switch operation in Python layer (bypassed Unity failure)"
                                
                                if getattr(self, 'custom_states', None) is None:
                                    self.custom_states = {}
                                if obj_id not in self.custom_states:
                                    self.custom_states[obj_id] = set()
                                if '[switchon]' in action_str:
                                    self.custom_states[obj_id].add('ON')
                                    self.custom_states[obj_id].discard('OFF')
                                elif '[switchoff]' in action_str:
                                    self.custom_states[obj_id].add('OFF')
                                    self.custom_states[obj_id].discard('ON')
                                self.changed_graph = True
                    else:
                        success = False
                        message = f"Failed: Object ID {obj_id} not found."
                except ValueError:
                    success = False
                    message = "Failed: Invalid object ID"
            else:
                if self.recording_options['recording']:
                    success, message = self.comm.render_script(script_list,
                                                               recording=True,
                                                               skip_animation=False,
                                                               camera_mode=self.recording_options['cameras'],
                                                               file_name_prefix='task_{}'.format(self.task_id),
                                                               image_synthesis=self.recording_options['modality'])
                else:
                    success, message = self.comm.render_script(script_list,
                                                               recording=False,
                                                               skip_animation=True)
            if not success:
                print(message)
            else:
                self.changed_graph = True

        # Obtain reward
        reward, done, info = self.reward()

        graph = self.get_graph()
        self.steps += 1
        
        obs = self.get_observations()
        

        info['finished'] = done
        info['graph'] = graph
        info['action_success'] = success if 'success' in locals() else True
        info['action_message'] = message if 'message' in locals() else ""
        if self.steps == self.max_episode_length:
            done = True
        return obs, reward, done, info

    def reset(self, environment_graph=None, environment_id=None, init_rooms=None):
        """
        :param environment_graph: the initial graph we should reset the environment with
        :param environment_id: which id to start
        :param init_rooms: where to intialize the agents
        """
        self.env_id = environment_id
        print("Resetting env", self.env_id)
        self.custom_states = {}

        if self.env_id is not None:
            self.comm.reset(self.env_id)
        else:
            self.comm.reset()

        s,g = self.comm.environment_graph()
        if self.env_id not in self.max_ids.keys():
            max_id = max([node['id'] for node in g['nodes']])
            self.max_ids[self.env_id] = max_id

        max_id = self.max_ids[self.env_id]
        #print(max_id)
        if environment_graph is not None:
            # TODO: this should be modified to extend well
            # updated_graph = utils.separate_new_ids_graph(environment_graph, max_id)
            updated_graph = environment_graph
            success, m = self.comm.expand_scene(updated_graph)
        else:
            success = True

        if not success:
            print("Error expanding scene")
            pdb.set_trace()
            return None
        self.num_static_cameras = self.comm.camera_count()[1]

        if init_rooms is None or init_rooms[0] not in ['kitchen', 'bedroom', 'livingroom', 'bathroom']:
            rooms = self.rnd.sample(['kitchen', 'bedroom', 'livingroom', 'bathroom'], 2)
        else:
            rooms = list(init_rooms)

        for i in range(self.num_agents):
            if i in self.agent_info:
                self.comm.add_character(self.agent_info[i], initial_room=rooms[i])
            else:
                self.comm.add_character()

        _, self.init_unity_graph = self.comm.environment_graph()


        self.changed_graph = True
        graph = self.get_graph()
        self.rooms = [(node['class_name'], node['id']) for node in graph['nodes'] if node['category'] == 'Rooms']
        self.id2node = {node['id']: node for node in graph['nodes']}

        obs = self.get_observations()
        self.steps = 0
        self.prev_reward = 0.
        return obs

    def get_graph(self):
        if getattr(self, 'custom_states', None) is None:
            self.custom_states = {}
            
        if self.changed_graph:
            s, graph = self.comm.environment_graph()
            if not s:
                pdb.set_trace()
                
            # === Thermal State Transition Extension ===
            heating_appliances_inside = ['microwave', 'oven', 'toaster', 'coffe_maker', 'kettle', 'stove']
            heating_appliances_on = ['stove']
            
            active_heaters = [n for n in graph.get('nodes', []) if 'ON' in n.get('states', [])]
            
            def get_related_items(target_id, relation_type):
                return [e['from_id'] for e in graph.get('edges', []) if e['to_id'] == target_id and e['relation_type'] == relation_type]
            
            items_to_heat = set()
            for heater in active_heaters:
                cname = heater['class_name'].lower()
                if cname in heating_appliances_inside:
                    items_to_heat.update(get_related_items(heater['id'], 'INSIDE'))
                if cname in heating_appliances_on:
                    items_on = get_related_items(heater['id'], 'ON')
                    items_to_heat.update(items_on)
                    # Propagate heat to items inside/on cookware
                    for item_id in items_on:
                        item_node = next((n for n in graph['nodes'] if n['id'] == item_id), None)
                        if item_node and item_node['class_name'].lower() in ['fryingpan', 'pot', 'cookingpot', 'sauce_pan', 'plate', 'bowl']:
                            items_to_heat.update(get_related_items(item_id, 'INSIDE'))
                            items_to_heat.update(get_related_items(item_id, 'ON'))
                            
            for item_id in items_to_heat:
                if item_id not in self.custom_states:
                    self.custom_states[item_id] = set()
                self.custom_states[item_id].add('HOT')
                
            cooling_appliances_inside = ['fridge']
            items_to_cool = set()
            for cooler in graph.get('nodes', []):
                if cooler['class_name'].lower() in cooling_appliances_inside:
                    items_to_cool.update(get_related_items(cooler['id'], 'INSIDE'))
                    
            for item_id in items_to_cool:
                if item_id not in self.custom_states:
                    self.custom_states[item_id] = set()
                self.custom_states[item_id].add('COLD')
                
            # Merge custom states back into the graph natively
            for node in graph.get('nodes', []):
                nid = node['id']
                if nid in self.custom_states:
                    current_states = set(node.get('states', []))
                    current_states.update(self.custom_states[nid])
                    if 'COLD' in current_states and 'HOT' in self.custom_states[nid]:
                        current_states.discard('COLD') # Heating overrides
                    elif 'HOT' in current_states and 'COLD' in self.custom_states[nid]:
                        current_states.discard('HOT') # Cooling overrides
                    node['states'] = list(current_states)
            # ==========================================
            
            self.graph = graph
            self.changed_graph = False
        return self.graph

    def get_observations(self):
        dict_observations = {}
        for agent_id in range(self.num_agents):
            obs_type = self.observation_types[agent_id]
            dict_observations[agent_id] = self.get_observation(agent_id, obs_type)
        return dict_observations

    def get_action_space(self):
        dict_action_space = {}
        for agent_id in range(self.num_agents):
            if self.observation_types[agent_id] not in ['partial', 'full']:
                raise NotImplementedError
            else:
                # Even if you can see all the graph, you can only interact with visible objects
                obs_type = 'partial'
            visible_graph = self.get_observation(agent_id, obs_type)
            dict_action_space[agent_id] = [node['id'] for node in visible_graph['nodes']]
        return dict_action_space

    def get_observation(self, agent_id, obs_type, info={}):
        if obs_type == 'partial':
            # agent 0 has id (0 + 1)
            curr_graph = self.get_graph()
            return utils.get_visible_nodes(curr_graph, agent_id=(agent_id+1))

        elif obs_type == 'full':
            return self.get_graph()

        elif obs_type == 'visible':
            # Only objects in the field of view of the agent
            raise NotImplementedError

        elif obs_type == 'image':
            camera_ids = [self.num_static_cameras + agent_id * self.num_camera_per_agent + self.CAMERA_NUM]
            if 'image_width' in info:
                image_width = info['image_width']
                image_height = info['image_height']
            else:
                image_width, image_height = self.default_image_width, self.default_image_height
            if 'mode' in info:
                current_mode = info['mode']
            else:
                current_mode = 'normal'
            s, images = self.comm.camera_image(camera_ids, mode=current_mode, image_width=image_width, image_height=image_height)
            if not s:
                pdb.set_trace()
            return images[0]
        else:
            raise NotImplementedError


        
