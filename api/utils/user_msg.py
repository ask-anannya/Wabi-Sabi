

def get_recent_user_message(res:dict)->list:
        msgs = res['messages']
        user_msgs = []
        for msg in reversed(msgs):
            if msg['role'] == 'human':
                user_msgs.append(msg['content'])
            if len(user_msgs) >=5:
                return user_msgs
        
        return user_msgs