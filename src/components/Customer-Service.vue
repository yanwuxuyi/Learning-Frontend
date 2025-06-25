<template>
  <div
    class="customer-service"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
    @mousedown="onMouseDown"
  >
    <div class="header" @selectstart.prevent>智能客服</div>
    <div class="content">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.sender">
        <div class="bubble">
          {{ message.text }}
        </div>
      </div>
    </div>
    <div class="footer">
      <input type="text" v-model="newMessage" @keyup.enter="sendMessage" placeholder="请输入您的问题" />
      <button @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<script>
import { generate } from '../utils/ai.js';

export default {
  name: "CustomerService",
  data() {
    return {
      position: { x: 20, y: window.innerHeight - 420 },
      dragging: false,
      dragStart: { x: 0, y: 0 },
      messages: [
        { text: "您好，请问有什么可以帮助您？" }
      ],
      newMessage: "",
    };
  },
  methods: {
    onMouseDown(event) {
      if (event.target.classList.contains('header')) {
        this.dragging = true;
        this.dragStart.x = event.clientX - this.position.x;
        this.dragStart.y = event.clientY - this.position.y;
        window.addEventListener("mousemove", this.onMouseMove);
        window.addEventListener("mouseup", this.onMouseUp);
      }
    },
    onMouseMove(event) {
      if (this.dragging) {
        this.position.x = event.clientX - this.dragStart.x;
        this.position.y = event.clientY - this.dragStart.y;
      }
    },
    onMouseUp() {
      this.dragging = false;
      window.removeEventListener("mousemove", this.onMouseMove);
      window.removeEventListener("mouseup", this.onMouseUp);
    },
    async sendMessage() {
      if(this.newMessage.trim() !== '') {
        const userMessage = this.newMessage;
        this.messages.push({ text: userMessage, sender: 'user' });
        this.newMessage = '';
        
        try {
            const res = await generate(userMessage);
            this.messages.push({ text: res.response, sender: 'ai' });
        } catch (error) {
            this.messages.push({ text: 'AI 服务暂时不可用，请稍后再试。', sender: 'ai' });
        }
      }
    }
  },
  beforeUnmount() {
    window.removeEventListener("mousemove", this.onMouseMove);
    window.removeEventListener("mouseup", this.onMouseUp);
  },
};
</script>

<style scoped>
.customer-service {
  position: fixed;
  width: 300px;
  height: 400px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  cursor: move;
  z-index: 1000;
}
.header {
  padding: 10px;
  background-color: #f0f0f0;
  border-bottom: 1px solid #ccc;
  font-weight: bold;
  user-select: none;
}
.content {
    flex-grow: 1;
    padding: 10px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}
.message {
    margin-bottom: 10px;
    display: flex;
}
.bubble {
    padding: 8px 12px;
    border-radius: 10px;
    max-width: 80%;
}

.user {
    justify-content: flex-end;
}
.user .bubble {
    background-color: #dcf8c6;
}

.ai {
    justify-content: flex-start;
}
.ai .bubble {
    background-color: #f0f0f0;
}

.footer {
    display: flex;
    padding: 10px;
    border-top: 1px solid #ccc;
}
.footer input {
    flex-grow: 1;
    margin-right: 10px;
}
</style> 