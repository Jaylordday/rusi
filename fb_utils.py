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
        url = f"{self.base_url}/{self.page_id}/posts?fields=message,created_time,id,full_picture&limit={limit}&access_token={self.access_token}"
        response = requests.get(url)
        return response.json().get('data', [])

    def get_comments(self, post_id, limit=50):
        url = f"{self.base_url}/{post_id}/comments?fields=from,message,created_time&limit={limit}&access_token={self.access_token}"
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
        # Requires 'pages_messaging' permission
        url = f"{self.base_url}/{self.page_id}/conversations?fields=messages{{message,from,created_time}},senders,updated_time&limit={limit}&access_token={self.access_token}"
        response = requests.get(url)
        data = response.json().get('data', [])
        return data

    def reply_to_comment(self, comment_id, message):
        url = f"{self.base_url}/{comment_id}/comments?message={message}&access_token={self.access_token}"
        response = requests.post(url)
        return response.json()
