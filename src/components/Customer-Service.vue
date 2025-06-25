<template>
  <div class="customer-service">
    <div class="header" @selectstart.prevent>
      <div class="header-left">
        旅小智智能客服
      </div>
      <span class="close-btn" @click.stop="$emit('close')">×</span>
    </div>
    <div class="content">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.sender">
        <template v-if="message.sender==='ai' && message.thinking && message.text">
          <div class="ai-thinking-block">
            <div class="thinking-content" v-html="message.html"></div>
            <div class="thinking-divider"></div>
          </div>
        </template>
        <template v-else-if="message.sender==='ai' && !message.thinking">
          <img class="bubble-avatar" src="/pet01.jpg" alt="AI" />
          <div class="bubble" v-html="message.html"></div>
        </template>
        <template v-else>
          <div class="bubble">{{ message.text }}</div>
          <img v-if="message.sender==='user'" class="bubble-avatar user-avatar" src="/pet02.jpg" alt="Me" />
        </template>
      </div>
    </div>
    <div class="footer">
      <input type="text" v-model="newMessage" @keyup.enter="sendMessage" placeholder="请输入您的问题" />
      <button class="send-btn" @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<script>
import { generateStream } from '../utils/ai.js';
import { marked } from 'marked';

const SYSTEM_PROMPT = `假设你叫"旅小智"，是一个专业的旅游社智能客服。请根据下面提供的"相关旅游项目信息"，用友好、专业的口吻回答用户的问题。
你的回答必须严格按照以下 XML 格式输出，不要有任何其他多余的文字：
<thinking>
[在此处分析用户问题和相关资料，这是你的思考过程]
</thinking>
<answer>
[在此处给出直接、友好、面向用户的最终回复，不要包括任何思考过程]
</answer>

如果信息中有能回答用户问题的项目，介绍项目信息并建议购买。如果没有，请说明情况并提供其他建议。不要杜撰信息。`;

export default {
  name: "CustomerService",
  data() {
    return {
      messages: [
        { text: "您好，请问有什么可以帮助您？", sender: 'ai', html: marked.parse("您好，请问有什么可以帮助您？") }
      ],
      newMessage: "",
    };
  },
  methods: {
    async sendMessage() {
      if (this.newMessage.trim() !== '') {
        const userMessage = this.newMessage;
        this.messages.push({ text: userMessage, sender: 'user' });
        this.newMessage = '';

        // --- RAG 流程: 调用后端进行搜索 ---
        let context = "没有找到相关的旅游项目信息。";
        try {
            const ragResponse = await fetch('/api/search_courses', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userMessage })
            });
            const ragData = await ragResponse.json();
            context = ragData.context;
        } catch (error) {
            console.error("RAG检索失败:", error);
        }
        
        // 构建增强的Prompt
        const augmentedPrompt = `${SYSTEM_PROMPT}\n\n相关旅游项目信息:\n${context}\n\n用户问题: "${userMessage}"`;
        // --- RAG 流程结束 ---

        const aiMsg = { text: '', sender: 'ai', html: '', thinking: true };
        this.messages.push(aiMsg);

        generateStream(
          augmentedPrompt,
          (fullText) => { // onData: 实时更新流式内容
            aiMsg.text = fullText;
            const thinkingMatch = fullText.match(/<thinking>([\s\S]*)/);
            aiMsg.html = marked.parse(thinkingMatch ? thinkingMatch[1] : fullText); // 在流式传输时只显示思考部分
            this.$forceUpdate();
          },
          () => { // onDone: 流式结束后，分割思考和回答
            console.log("--- AI 回复已完成 ---");
            const fullText = aiMsg.text;
            
            const thinkingMatch = fullText.match(/<thinking>([\s\S]*?)<\/thinking>/);
            const answerMatch = fullText.match(/<answer>([\s\S]*?)<\/answer>/);

            let thinking = thinkingMatch ? thinkingMatch[1].trim() : '';
            let answer = answerMatch ? answerMatch[1].trim() : '';

            // Fallback: 如果标签不完整或不存在，则将所有内容视为回答
            if (!answer && !thinking) {
                answer = fullText;
            } else if (!answer && thinking) {
                // 只有思考标签，把思考当回答
                answer = thinking;
                thinking = '';
            }

            console.log("收到的完整回复: ", fullText);
            console.log("解析后的 [思考] 部分: ", thinking);
            console.log("解析后的 [回答] 部分: ", answer);

            // 更新或移除思考区块
            if (thinking) {
              aiMsg.text = thinking;
              aiMsg.html = marked.parse(thinking);
            } else {
              // 如果没有思考过程，则从消息列表中移除该区块
              const index = this.messages.findIndex(m => m === aiMsg);
              if (index > -1) {
                this.messages.splice(index, 1);
              }
            }

            // 如果有答案，则作为新消息气泡插入
            if (answer) {
              this.messages.push({
                text: answer,
                sender: 'ai',
                html: marked.parse(answer),
                thinking: false, // false 表示是回答气泡
              });
            }

            this.$forceUpdate();
          },
          (err) => { // onError
            aiMsg.text = 'AI 服务暂时不可用，请稍后再试。';
            aiMsg.html = marked.parse(aiMsg.text);
            this.$forceUpdate();
          }
        );
      }
    }
  }
};
</script>

<style scoped>
.customer-service {
  position: relative;
  width: 420px;
  height: 520px;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 8px 32px 0 rgba(60, 60, 60, 0.18);
  display: flex;
  flex-direction: column;
  z-index: 1200;
  overflow: hidden;
  border: none;
  font-family: 'Segoe UI', 'PingFang SC', 'Hiragino Sans', Arial, sans-serif;
}
.header {
  padding: 16px 20px 14px 20px;
  background: linear-gradient(90deg, #ffe082 0%, #ffd54f 100%);
  color: #fff;
  font-weight: bold;
  font-size: 18px;
  user-select: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  letter-spacing: 1px;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.08);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid #fffde7;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.10);
  object-fit: cover;
}
.close-btn {
  font-size: 22px;
  color: #fff;
  cursor: pointer;
  margin-left: 10px;
  transition: color 0.2s;
  font-weight: normal;
}
.close-btn:hover {
  color: #ffd54f;
}
.content {
  flex-grow: 1;
  padding: 18px 16px 8px 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: #fffde7;
}
.message {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-end;
}
.bubble {
  padding: 12px 18px;
  border-radius: 18px;
  max-width: 70%;
  font-size: 15px;
  line-height: 1.7;
  box-shadow: 0 2px 12px rgba(255, 193, 7, 0.10);
  word-break: break-all;
  position: relative;
  background: #fff;
  color: #b28704;
  border: 1.5px solid #ffe082;
  transition: box-shadow 0.2s;
}
.user {
  justify-content: flex-end;
}
.user .bubble {
  background: linear-gradient(90deg, #fffde7 0%, #ffe082 100%);
  color: #b28704;
  border-bottom-right-radius: 6px;
  border: 1.5px solid #ffe082;
  margin-right: 8px;
}
.user .bubble-avatar {
  margin-left: 8px;
}
.ai {
  justify-content: flex-start;
}
.ai .bubble {
  background: #fff;
  color: #b28704;
  border-bottom-left-radius: 6px;
  border: 1.5px solid #fffde7;
  margin-left: 8px;
}
.bubble-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #fff;
  border: 1.5px solid #ffe082;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.10);
  object-fit: cover;
}
.user-avatar {
  border: 1.5px solid #ffd54f;
}
.footer {
  display: flex;
  padding: 14px 16px;
  border-top: 1.5px solid #ffe082;
  background: #fffde7;
}
.footer input {
  flex-grow: 1;
  margin-right: 10px;
  border-radius: 8px;
  border: 1.5px solid #ffe082;
  padding: 10px 14px;
  font-size: 15px;
  outline: none;
  transition: border 0.2s, box-shadow 0.2s;
  background: #fff;
  color: #b28704;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.04);
}
.footer input:focus {
  border: 2px solid #ffd54f;
  box-shadow: 0 0 0 2px #ffe08244;
}
.send-btn {
  background: linear-gradient(90deg, #ffe082 0%, #ffd54f 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 22px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s, transform 0.1s;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.10);
}
.send-btn:hover {
  background: linear-gradient(90deg, #ffd54f 0%, #ffe082 100%);
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 4px 16px rgba(255, 193, 7, 0.18);
}
.ai-thinking-block {
  width: 100%;
  margin-bottom: 8px;
  color: #bdbdbd;
  font-size: 14px;
  background: none;
  border: none;
  box-shadow: none;
  padding: 0 0 0 48px;
  position: relative;
}
.thinking-content {
  color: #bdbdbd;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-all;
}
.thinking-divider {
  border-bottom: 1px dashed #e0e0e0;
  margin: 8px 0 0 0;
  height: 1px;
  width: 90%;
}
</style> 