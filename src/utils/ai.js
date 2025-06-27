import axios from 'axios'

const aiRequest = axios.create({
    baseURL: '/ai-api',
    timeout: 60000 // AI responses can take longer
})

// 清理响应文本，移除固定前缀
function cleanResponse(text) {
    // 移除所有 <think></think> 标签及其内容，包括可能的换行和空格
    text = text.replace(/\s*<think>[\s\S]*?<\/think>\s*/g, '');
    
    // 移除开头的空白字符
    text = text.trim();
    
    return text;
}

aiRequest.interceptors.response.use(
    response => {
        if (response.data && response.data.response) {
            // 在返回响应前清理文本
            response.data.response = cleanResponse(response.data.response);
        }
        return response.data;
    },
    error => {
        console.error("AI service error:", error);
        return Promise.reject(error);
    }
);

export function generate(userMessage, systemPrompt) {
    return aiRequest({
        url: "/generate",
        method: 'post',
        data: {
            model: "deepseek-r1:1.5b",
            prompt: systemPrompt,
            stream: false,
            temperature: 0.1
        },
        headers: {
            'Content-Type': 'application/json'
        }
    })
}

export async function generateStream(fullPrompt, onData, onDone, onError) {
    try {
        const response = await fetch('/ai-api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: "deepseek-r1:1.5b",
                prompt: fullPrompt,
                stream: true,
                temperature: 0.1
            })
        });

        if (!response.ok) {
            throw new Error(`AI service request failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        let fullText = '';
        let decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 最后一行可能不完整，留到下次
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.response) {
                        fullText += json.response;
                        onData && onData(fullText);
                    }
                } catch (e) {
                    console.error("Failed to parse stream line:", line, e);
                }
            }
        }
        
        // 当数据流结束后，处理可能残留在缓冲区中的最后一部分数据
        if (buffer.trim()) {
            try {
                const json = JSON.parse(buffer);
                if (json.response) {
                    fullText += json.response;
                    onData && onData(fullText);
                }
            } catch (e) {
                console.error("Failed to parse final stream buffer:", buffer, e);
            }
        }
        
        // 最终，确认所有数据处理完毕，正确调用 onDone 回调
        onDone && onDone();

    } catch (err) {
        onError && onError(err);
    }
}

export async function generateComment(userMessage, systemPrompt) {
  const apiKey = 'sk-ca86147be37a45a0a2185bf5e3585e6b'; 
  const endpoint = 'https://api.deepseek.com/v1/chat/completions';

  try {
    const response = await axios.post(
      endpoint,
      {
        model: 'deepseek-chat', 
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userMessage }
        ],
        temperature: 0.2,
      },
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );

    const raw = response.data?.choices?.[0]?.message?.content || '';
    return { response: raw };
  } catch (err) {
    console.error('[DeepSeek API 错误]', err?.response?.data || err.message);
    throw err;
  }
}
const bannedWords = [
    '傻逼', '垃圾', 'fuck', '操你', '滚', '你妈', 'sb', 'shit', '死全家', '狗屎'
    // 可继续扩展中英脏话、敏感词
];

function containsBannedWords(text) {
    const lowered = text.toLowerCase();
    return bannedWords.some(word => lowered.includes(word));
}

export async function moderateComment(commentText) {
    // ✅ 第一步：本地违禁词检测
    if (containsBannedWords(commentText)) {
        console.warn(`[本地拦截] 命中违禁词: "${commentText}"`);
        return { ok: false, reason: '评论包含违禁词' };
    }

    // ✅ 第二步：AI 检测（中文提示词）
const systemPrompt = `
你是一个评论审核系统，任务是判断评论是否违反社区规范。

【违规行为包括】：
1. 人身攻击、辱骂、侮辱性语言；
2. 包含侮辱性、脏话、色情、淫秽词语
3. 广告、推广、垃圾信息；
4. 欺诈、误导性内容；
5. 政治煽动、暴力威胁、反政府言论；
6. 散播谣言、恶意评分、组织攻击。
7. 涉及政治人物、国家元首、历史国家政治人物等敏感人物
8. 涉及台湾、西藏、新疆、香港、澳门独立的内容
9. 其他违法违规的言论

⚠️ 注意：
你只能用英文小写回答：
- yes：评论可能违规；
- no：评论内容正常。

❌ 严禁输出任何解释说明或标点；
❌ 严禁输出多个选项；
✅ 回复时**只能输出以下两种之一：yes 或 no**

---

现在开始审核。

评论内容如下：
"${commentText}"

请直接输出你的审核结论（只允许输出 yes 或 no）：
`;

    try {
        const result = await generateComment(commentText, systemPrompt);
        const rawResponse = (result.response || '').toLowerCase().trim();
        console.log(`[AI 审核] 输入: "${commentText}" => 回复: "${rawResponse}"`);

        const normalized = rawResponse.replace(/[^a-z]/g, '');
        return normalized === 'no'
            ? { ok: true }
            : { ok: false, reason: 'AI 检测到评论可能包含不当内容' };
    } catch (err) {
        console.error("moderateComment error:", err);
        return { ok: false, reason: 'AI 调用失败' };
    }
}




export async function generateStreamForPrice(payload, onData, onDone, onError) {
    try {
        const response = await fetch('/api/price_suggestion_stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`AI service request failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        let fullText = '';
        let decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const json = JSON.parse(line);
                    if (json.response) {
                        fullText += json.response;
                        onData && onData(fullText);
                    }
                } catch (e) {
                    // 不是JSON就直接拼接
                    fullText += line;
                    onData && onData(fullText);
                }
            }
        }
        if (buffer.trim()) {
            try {
                const json = JSON.parse(buffer);
                if (json.response) {
                    fullText += json.response;
                    onData && onData(fullText);
                }
            } catch (e) {
                fullText += buffer;
                onData && onData(fullText);
            }
        }
        onDone && onDone();
    } catch (err) {
        onError && onError(err);
    }
}