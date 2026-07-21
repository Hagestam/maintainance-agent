const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// LocalAuth saves your session locally so you only scan the QR code once
const client = new Client({
    authStrategy: new LocalAuth(),
    webVersion: '2.2412.54',
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/wppconnect-team/wa-version/main/html/2.2412.54.html'
    }
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
    if (msg.from === 'status@broadcast') return;
    if (msg.fromMe && msg.from !== msg.to) return;

    let messageText = msg.body || '';
    let imageBase64 = null;
    let imageMimeType = null;

    // Handle media messages (photos)
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

    // Skip if no text and no image
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