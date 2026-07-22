const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const express = require('express');

const app = express();
app.use(express.json());

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: false, // Set to false so you can see the browser window
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

client.on('qr', (qr) => {
    console.log('\nScan this QR code with WhatsApp on your phone:');
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
    console.log('Authentication successful! Loading WhatsApp Web...');
});

client.on('auth_failure', (msg) => {
    console.error('Authentication failure:', msg);
});

client.on('ready', () => {
    console.log('\nWhatsApp Web Agent is Connected and Ready!');
});

// 1. ENDPOINT FOR PYTHON: Listens for backend dispatches on port 3000
app.post('/send-message', async (req, res) => {
    const { phone, message } = req.body;
    try {
        let chatId = phone.includes('@c.us') ? phone : `${phone}@c.us`;
        await client.sendMessage(chatId, message);
        console.log(`[SENT VIA BRIDGE] Emergency alert sent to ${chatId}`);
        res.status(200).json({ status: 'success' });
    } catch (error) {
        console.error('Failed to send message via bridge:', error);
        res.status(500).json({ status: 'error', error: error.message });
    }
});

// 2. LISTENER FOR WHATSAPP INCOMING MESSAGES
client.on('message_create', async (msg) => {
    if (msg.from === 'status@broadcast') return;
    if (msg.fromMe && msg.from !== msg.to) return;

    let messageText = msg.body || '';
    let imageBase64 = null;
    let imageMimeType = null;

    if (msg.hasMedia) {
        try {
            const media = await msg.downloadMedia();
            if (media && media.mimetype.startsWith('image/')) {
                imageBase64 = media.data;
                imageMimeType = media.mimetype;
                console.log(`Image received from ${msg.from}, type: ${media.mimetype}`);
            }
        } catch (err) {
            console.error('Failed to download media:', err);
        }
    }

    if (!messageText.trim() && !imageBase64) return;

    console.log(`\nMessage from ${msg.from}: "${messageText}"`);

    try {
        const response = await axios.post('http://localhost:8000/api/chat', {
            user: msg.from,
            message: messageText || 'I sent a photo of the issue.',
            image_base64: imageBase64,
            image_mime_type: imageMimeType
        });

        const replyText = response.data.reply;
        if (replyText) {
            await msg.reply(replyText);
            console.log(`Sent reply to ${msg.from}`);
        }
    } catch (error) {
        console.error('Error communicating with FastAPI server:', error.message);
    }
});

client.initialize();

// Start Express HTTP Server on Port 3000
app.listen(3000, () => {
    console.log('Bridge HTTP server listening on port 3000');
});