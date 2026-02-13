const express = require('express');
const axios = require('axios');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration
const ACCESS_TOKEN = "EAF2xZBKUAR7oBQpwCYzKNv3lcN1jXtKtLWo9yhkSHVfYdcZBiYHs9qVFVUXc2145pfj2h3OUDO8XeTqBPocP7KMGf2N0dcUVWmedJDEEYLVUIyGhfcYyCEGEPcPSo3a4X7DqN2RUmBK5V7PBpgRvHDrcIGrmBjw3GYDI1nn8oihEIKCc79LOphEIEg2OIYybZBd";
const PAGE_ID = "831829270014292";
const BASE_URL = "https://graph.facebook.com/v19.0";

app.use(express.json());
app.use(express.static('public'));

// Database Setup
const db = new sqlite3.Database('./rusi_v2.db');
db.serialize(() => {
    db.run("CREATE TABLE IF NOT EXISTS activity (id TEXT PRIMARY KEY, type TEXT, content TEXT, user TEXT, created_at DATETIME)");
});

// FB API Wrapper Endpoints
app.get('/api/page-info', async (req, res) => {
    try {
        const response = await axios.get(`${BASE_URL}/${PAGE_ID}?fields=name,about,fan_count,link,picture&access_token=${ACCESS_TOKEN}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/feed', async (req, res) => {
    try {
        const response = await axios.get(`${BASE_URL}/${PAGE_ID}/posts?fields=message,created_time,id,full_picture,reactions.summary(true),comments.summary(true)&limit=10&access_token=${ACCESS_TOKEN}`);
        res.json(response.data.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/comments/:postId', async (req, res) => {
    try {
        const response = await axios.get(`${BASE_URL}/${req.params.postId}/comments?fields=from{name,picture},message,created_time,like_count&access_token=${ACCESS_TOKEN}`);
        res.json(response.data.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/conversations', async (req, res) => {
    try {
        const response = await axios.get(`${BASE_URL}/${PAGE_ID}/conversations?fields=messages{message,from,created_time},participants,updated_time,unread_count&access_token=${ACCESS_TOKEN}`);
        res.json(response.data.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/notifications', async (req, res) => {
    try {
        // Fetches notifications for the page
        const response = await axios.get(`${BASE_URL}/${PAGE_ID}/notifications?fields=id,title,link,created_time,message,from&access_token=${ACCESS_TOKEN}`);
        res.json(response.data.data || []);
    } catch (error) {
        // If notifications endpoint is restricted by token, return empty instead of 500
        res.json([]);
    }
});

app.get('/api/messages/:convId', async (req, res) => {
    try {
        const response = await axios.get(`${BASE_URL}/${req.params.convId}/messages?fields=message,from,created_time&access_token=${ACCESS_TOKEN}`);
        res.json(response.data.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/reply/comment', async (req, res) => {
    const { commentId, message } = req.body;
    try {
        const response = await axios.post(`${BASE_URL}/${commentId}/comments?message=${encodeURIComponent(message)}&access_token=${ACCESS_TOKEN}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/reply/message', async (req, res) => {
    const { recipientId, message } = req.body;
    try {
        const response = await axios.post(`${BASE_URL}/me/messages?access_token=${ACCESS_TOKEN}`, {
            recipient: { id: recipientId },
            message: { text: message }
        });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Keep-alive ping
const APP_URL = process.env.RENDER_EXTERNAL_URL;
if (APP_URL) {
    setInterval(() => {
        axios.get(APP_URL).catch(() => {});
    }, 600000); // 10 mins
}

app.listen(PORT, () => {
    console.log(`RUSI Server running on port ${PORT}`);
});
