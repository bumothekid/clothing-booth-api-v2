from typing import Optional
from datetime import datetime

class PrivateUser:
    def __init__(self, userid: str , username: str, createdAt: datetime, updatedAt: datetime, email: str, profilePicture: Optional[str] = None, friends: Optional[list] = None, outgoingFriendRequests: Optional[list] = None, incomingFriendRequests: Optional[list] = None):
        self.user_id = userid
        self.username = username
        self.email = email
        self.profile_picture = profilePicture
        self.created_at = createdAt
        self.updated_at = updatedAt
        self.friends = friends
        self.outgoing_friend_requests = outgoingFriendRequests
        self.incoming_friend_requests = incomingFriendRequests
    
    def as_dict(self) -> dict:
        return self.__dict__
        
class PublicUser:
    def __init__(self, userid: str , username: str, createdAt: datetime, profilePicture: Optional[str] = None, friends: Optional[list] = None):
        self.user_id = userid
        self.username = username
        self.profile_picture = profilePicture
        self.created_at = createdAt
        self.friends = friends