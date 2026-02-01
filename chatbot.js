// TradingBrainz Chatbot Widget
(function() {
    const chatbotHTML = `
    <div id="chatbot-container">
        <div id="chatbot-bubble" onclick="toggleChat()">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
            </svg>
        </div>
        <div id="chatbot-window">
            <div id="chatbot-header">
                <span>TradingBrainz Support</span>
                <button onclick="toggleChat()" style="background:none;border:none;color:white;cursor:pointer;font-size:20px;">&times;</button>
            </div>
            <div id="chatbot-messages">
                <div class="bot-message">Hi! 👋 How can I help you today? Choose a topic or type your question:</div>
                <div class="quick-replies">
                    <button onclick="askQuestion('pricing')">Pricing & Plans</button>
                    <button onclick="askQuestion('requirements')">Requirements</button>
                    <button onclick="askQuestion('bundle')">Bundle Details</button>
                    <button onclick="askQuestion('refund')">Refund Policy</button>
                    <button onclick="askQuestion('contact')">Contact Support</button>
                </div>
            </div>
            <div id="chatbot-input">
                <input type="text" id="user-input" placeholder="Type your question..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>`;

    const chatbotCSS = `
        #chatbot-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        #chatbot-bubble { width: 60px; height: 60px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4); transition: transform 0.3s, box-shadow 0.3s; color: white; }
        #chatbot-bubble:hover { transform: scale(1.1); box-shadow: 0 6px 30px rgba(59, 130, 246, 0.6); }
        #chatbot-window { display: none; position: absolute; bottom: 70px; right: 0; width: 350px; height: 450px; background: #1a1a2e; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); overflow: hidden; flex-direction: column; border: 1px solid rgba(255,255,255,0.1); }
        #chatbot-window.open { display: flex; }
        #chatbot-header { background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 15px 20px; color: white; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
        #chatbot-messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .bot-message, .user-message { padding: 12px 16px; border-radius: 12px; max-width: 85%; line-height: 1.5; font-size: 14px; }
        .bot-message { background: rgba(59, 130, 246, 0.2); color: #e4e4e7; align-self: flex-start; border-bottom-left-radius: 4px; }
        .user-message { background: #3b82f6; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
        .quick-replies { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .quick-replies button { background: rgba(139, 92, 246, 0.2); border: 1px solid rgba(139, 92, 246, 0.4); color: #a78bfa; padding: 8px 12px; border-radius: 20px; cursor: pointer; font-size: 12px; transition: all 0.2s; }
        .quick-replies button:hover { background: rgba(139, 92, 246, 0.4); color: white; }
        #chatbot-input { display: flex; padding: 15px; border-top: 1px solid rgba(255,255,255,0.1); gap: 10px; }
        #chatbot-input input { flex: 1; padding: 12px 15px; border: 1px solid rgba(255,255,255,0.2); border-radius: 25px; background: rgba(255,255,255,0.05); color: white; outline: none; font-size: 14px; }
        #chatbot-input input::placeholder { color: #888; }
        #chatbot-input button { background: linear-gradient(135deg, #3b82f6, #8b5cf6); border: none; color: white; padding: 12px 20px; border-radius: 25px; cursor: pointer; font-weight: 600; transition: transform 0.2s; }
        #chatbot-input button:hover { transform: scale(1.05); }
        @media (max-width: 480px) { #chatbot-window { width: calc(100vw - 40px); right: -10px; height: 400px; } }`;

    // Inject CSS
    const style = document.createElement('style');
    style.textContent = chatbotCSS;
    document.head.appendChild(style);

    // Inject HTML
    document.body.insertAdjacentHTML('beforeend', chatbotHTML);

    // Chatbot responses
    const responses = {
        pricing: "**Pricing Options:**\n\n• **Trading Bots:** $99/mo (1 bot), $79/mo (2 bots), $59/mo (3+ bots)\n• **Trading Brain:** $497 one-time\n• **Complete Bundle:** $697 one-time (Brain + 2 lifetime bots)\n\nThe Bundle is the best value - you save over $500!",
        requirements: "**System Requirements:**\n\n• Windows 10/11\n• Python 3.10+\n• 8GB RAM (16GB recommended)\n• Internet connection\n\n**API Keys Needed:**\n• Anthropic (Claude AI) - for strategy extraction\n• QuantConnect - for backtesting\n• Tradovate - for live trading",
        bundle: "**Complete Bundle ($697):**\n\n✓ Trading Brain (full AI system)\n✓ 2 Lifetime Trading Bots\n✓ All prop firm profiles\n✓ Lifetime updates\n\n⚠️ **Important:** You must activate your 2 bots within 7 days of purchase. Unused bot slots are forfeited after the activation window.",
        refund: "**Refund Policy:**\n\nDue to the digital nature of our products, all sales are final. We recommend reviewing the FAQ and requirements carefully before purchasing.\n\nIf you have technical issues, our support team will help resolve them at support@tradingbrainz.com",
        contact: "**Contact Us:**\n\n📧 Email: support@tradingbrainz.com\n\nWe typically respond within 24 hours. For faster help, check our FAQ page first!",
        default: "I'm not sure about that specific question. Here are some options:\n\n• Check our **FAQ page** for detailed answers\n• Email **support@tradingbrainz.com**\n• Ask about: pricing, requirements, bundle, or refunds"
    };

    // Global functions
    window.toggleChat = function() {
        document.getElementById('chatbot-window').classList.toggle('open');
    };

    window.askQuestion = function(topic) {
        const messagesDiv = document.getElementById('chatbot-messages');
        const userMsg = document.createElement('div');
        userMsg.className = 'user-message';
        userMsg.textContent = topic.charAt(0).toUpperCase() + topic.slice(1);
        messagesDiv.appendChild(userMsg);

        setTimeout(() => {
            const botMsg = document.createElement('div');
            botMsg.className = 'bot-message';
            botMsg.innerHTML = responses[topic].replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
            messagesDiv.appendChild(botMsg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }, 500);
    };

    window.sendMessage = function() {
        const input = document.getElementById('user-input');
        const message = input.value.trim().toLowerCase();
        if (!message) return;

        const messagesDiv = document.getElementById('chatbot-messages');
        const userMsg = document.createElement('div');
        userMsg.className = 'user-message';
        userMsg.textContent = input.value;
        messagesDiv.appendChild(userMsg);
        input.value = '';

        setTimeout(() => {
            let response = responses.default;
            if (message.includes('price') || message.includes('cost') || message.includes('how much')) response = responses.pricing;
            else if (message.includes('require') || message.includes('need') || message.includes('api')) response = responses.requirements;
            else if (message.includes('bundle') || message.includes('7 day') || message.includes('lifetime')) response = responses.bundle;
            else if (message.includes('refund') || message.includes('money back')) response = responses.refund;
            else if (message.includes('contact') || message.includes('email') || message.includes('support') || message.includes('help')) response = responses.contact;

            const botMsg = document.createElement('div');
            botMsg.className = 'bot-message';
            botMsg.innerHTML = response.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
            messagesDiv.appendChild(botMsg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }, 500);
    };

    window.handleKeyPress = function(e) {
        if (e.key === 'Enter') sendMessage();
    };
})();
