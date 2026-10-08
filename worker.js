export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Securely set the Telegram webhook
    if (url.pathname === "/setup-webhook" && request.method === "GET") {
      const key = url.searchParams.get("key");

      if (!env.WEBHOOK_SETUP_SECRET || key !== env.WEBHOOK_SETUP_SECRET) {
        return new Response("Unauthorized", { status: 401 });
      }

      const webhookUrl = `${url.origin}/telegram`;

      const response = await fetch(
        `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/setWebhook`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            url: webhookUrl
          })
        }
      );

      return new Response(await response.text(), {
        headers: {
          "Content-Type": "application/json"
        }
      });
    }

    // Telegram sends updates here
    if (url.pathname === "/telegram" && request.method === "POST") {
      try {
        const update = await request.json();

        if (!update.message) {
          return new Response("OK");
        }

        const chatId = update.message.chat.id;
        const text = update.message.text || "";

        if (text === "/start" || text === "/help") {
          await sendMessage(
            env.TELEGRAM_BOT_TOKEN,
            chatId,
            "✈️ Aviator Stats Bot\n\n" +
            "/round 1.45 - record a round\n" +
            "/last - recent rounds\n" +
            "/stats - statistics\n" +
            "/bankroll 500 - set bankroll\n" +
            "/report - session report\n\n" +
            "⚠️ This bot analyzes past rounds. It cannot reliably predict the next crash."
          );
        }

        else if (text.startsWith("/round")) {
          const parts = text.trim().split(/\s+/);

          if (!parts[1]) {
            await sendMessage(
              env.TELEGRAM_BOT_TOKEN,
              chatId,
              "Use: /round 1.45"
            );
          } else {
            const value = parseFloat(parts[1].replace("x", ""));

            if (!Number.isFinite(value) || value < 1) {
              await sendMessage(
                env.TELEGRAM_BOT_TOKEN,
                chatId,
                "Enter a valid multiplier, e.g. /round 2.35"
              );
            } else {
              await sendMessage(
                env.TELEGRAM_BOT_TOKEN,
                chatId,
                `✅ Recorded ${value.toFixed(2)}x`
              );
            }
          }
        }

        else if (text === "/last") {
          await sendMessage(
            env.TELEGRAM_BOT_TOKEN,
            chatId,
            "📊 Round history storage will be connected next."
          );
        }

        else if (text === "/stats") {
          await sendMessage(
            env.TELEGRAM_BOT_TOKEN,
            chatId,
            "📈 Statistics storage will be connected next."
          );
        }

        else if (text.startsWith("/bankroll")) {
          const parts = text.trim().split(/\s+/);

          if (!parts[1] || isNaN(parseFloat(parts[1]))) {
            await sendMessage(
              env.TELEGRAM_BOT_TOKEN,
              chatId,
              "Use: /bankroll 500"
            );
          } else {
            const amount = parseFloat(parts[1]);

            if (amount < 0) {
              await sendMessage(
                env.TELEGRAM_BOT_TOKEN,
                chatId,
                "Enter a valid amount."
              );
            } else {
              await sendMessage(
                env.TELEGRAM_BOT_TOKEN,
                chatId,
                `💰 Bankroll set to ${amount.toFixed(2)}`
              );
            }
          }
        }

        else if (text === "/report") {
          await sendMessage(
            env.TELEGRAM_BOT_TOKEN,
            chatId,
            "📝 Session reporting will be connected next."
          );
        }

        return new Response("OK");
      } catch (error) {
        return new Response("OK");
      }
    }

    return new Response("Aviator Stats Bot is running.");
  }
};

async function sendMessage(token, chatId, text) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: text
    })
  });
}