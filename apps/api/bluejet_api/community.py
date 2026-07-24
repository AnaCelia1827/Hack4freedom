import uuid


class CommunityService:
    def __init__(self):
        self.posts = []
        self.reports = []
        self.opportunities = []
        self.comments = []
        self.reactions = set()

    def post(self, pubkey, category, content, media_asset_id=None):
        if category not in {"learning", "question", "achievement"} or len(content) > 2000:
            raise ValueError("invalid public post")
        item = {"id": uuid.uuid4().hex, "nostr_event_id": uuid.uuid4().hex, "author_pubkey": pubkey, "category": category, "content": content, "media_asset_id": media_asset_id, "moderation_status": "VISIBLE"}
        self.posts.append(item); return item

    def comment(self, pubkey, post_id, content):
        if not content.strip() or not any(p["id"] == post_id for p in self.posts):
            raise ValueError("invalid comment")
        item = {"id": uuid.uuid4().hex, "post_id": post_id, "author_pubkey": pubkey, "content": content}
        self.comments.append(item)
        return item

    def react(self, pubkey, post_id):
        key = (pubkey, post_id)
        if not any(p["id"] == post_id for p in self.posts):
            raise ValueError("post not found")
        if key in self.reactions:
            self.reactions.remove(key)
            return {"active": False}
        self.reactions.add(key)
        return {"active": True}
