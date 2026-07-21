const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// LocalAuth saves your session locally so you only scan the QR code once
const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', (qr) => {
    console.log('\nScan this QR code with WhatsApp on your phone:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('\nWhatsApp Web Agent is Connected and Ready!');
});

// Use 'message_create' instead of 'message' so it captures self-testing
client.on('message_create', async (msg) => {
    // Ignore status updates
    if (msg.from === 'status@broadcast') return;

    // Ignore outgoing messages sent to OTHER people (prevents replying to yourself in other chats)
    if (msg.fromMe && msg.from !== msg.to) return;

    // Guard: Ignore empty messages, media without text, voice notes, stickers
    if (!msg.body || msg.body.trim() === '') return;

    console.log(`\nReceived message: "${msg.body}" from ${msg.from}`);

    try {
        // Post message to your Python FastAPI server
        const response = await axios.post('http://localhost:8000/api/chat', {
            user: msg.from,
            message: msg.body
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