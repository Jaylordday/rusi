import requests

class FacebookManager:
    def __init__(self, access_token, page_id):
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v19.0"

    def get_page_info(self):
        url = f"{self.base_url}/{self.page_id}?fields=name,about,fan_count,link,picture&access_token={self.access_token}"
        response = requests.get(url)
        return response.json()

    def get_posts(self, limit=10):
        # Fetches posts with reactions and comment counts
        url = f"{self.base_url}/{self.page_id}/posts?fields=message,created_time,id,full_picture,reactions.summary(true),comments.summary(true)&limit={limit}&access_token={self.access_token}"
        response = requests.get(url)
        return response.json().get('data', [])

    def get_comments(self, post_id, limit=50):
        # Fetches comments with user profile pictures if possible
        url = f"{self.base_url}/{post_id}/comments?fields=from{{name,picture}},message,created_time,like_count&limit={limit}&access_token={self.access_token}"
        response = requests.get(url)
        return response.json().get('data', [])

    def get_all_recent_comments(self, post_limit=5):
        posts = self.get_posts(limit=post_limit)
        all_comments = []
        for post in posts:
            comments = self.get_comments(post['id'])
            for c in comments:
                c['post_id'] = post['id']
                c['post_message'] = post.get('message', 'No message')
                all_comments.append(c)
        return all_comments

    def get_messages(self, limit=20):
        # Fetches list of conversations
        url = f"{self.base_url}/{self.page_id}/conversations?fields=messages{{message,from,created_time}},participants,updated_time,unread_count&limit={limit}&access_token={self.access_token}"
        response = requests.get(url)
        return response.json().get('data', [])

    def get_conversation_history(self, conv_id):
        # Fetches all messages in a specific conversation
        url = f"{self.base_url}/{conv_id}/messages?fields=message,from,created_time&access_token={self.access_token}"
        response = requests.get(url)
        return response.json().get('data', [])

    def send_private_message(self, recipient_id, message_text):
        # Sends a message to a specific user (recipient_id is the PSID)
        url = f"{self.base_url}/me/messages?access_token={self.access_token}"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        response = requests.post(url, json=payload)
        return response.json()

    def reply_to_comment(self, comment_id, message):
        url = f"{self.base_url}/{comment_id}/comments?message={message}&access_token={self.access_token}"
        response = requests.post(url)
        return response.json()
