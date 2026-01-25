# In-memory bot storage (will add DB later)
bots_db = {}

def get_all_bots():
    return list(bots_db.values())

def get_bot(bot_id):
    return bots_db.get(bot_id)

def create_bot(bot_id, config):
    bots_db[bot_id] = {
        "id": bot_id,
        "status": "stopped",
        **config
    }
    return bots_db[bot_id]

def update_bot_status(bot_id, status):
    if bot_id in bots_db:
        bots_db[bot_id]["status"] = status
        return bots_db[bot_id]
    return None

def delete_bot(bot_id):
    if bot_id in bots_db:
        del bots_db[bot_id]
        return True
    return False
