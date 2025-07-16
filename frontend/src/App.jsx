import React, { useState, useRef, useEffect } from 'react';

function App() {
  const [messages, setMessages] = useState([
    { role: 'system', content: '叮咚～ Xtool专属用户评论分析小能手已上线啦🎊！\n想知道xtool用户反馈里藏着哪些小秘密吗？ 快来召唤我吧😘！\n示例:请分析xtool的用户反馈' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newMessages = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);

    // 判断是否是淘宝评论分析相关问题
    const lowerInput = input.toLowerCase();
    const isTaobaoQuery =
      lowerInput.includes('淘宝') ||
      lowerInput.includes('xtool') ||
      lowerInput.includes('评论') ||
      lowerInput.includes('用户反馈');

    if (isTaobaoQuery) {
      setMessages(msgs => [
        ...msgs,
        { role: 'assistant', content: '正在爬取淘宝数据，请稍候...' }
      ]);
    }

    setLoading(true);
    setInput('');

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input })
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch (e) {
        setMessages(msgs => [
          ...(isTaobaoQuery ? msgs.slice(0, -1) : msgs),
          { role: 'assistant', content: '后端返回内容不是合法JSON：' + text }
        ]);
        setLoading(false);
        return;
      }
      if (data.steps && data.steps.length > 0) {
        data.steps.forEach(step => {
          setMessages(msgs => [...msgs, {
            role: 'assistant',
            content: `【思考过程】\n思考: ${step.thought}\n行动: ${step.action}\n观察: ${step.observation}\n${step.sub_answer ? `小结论: ${step.sub_answer}` : ''}`
          }]);
        });
      }
      let answer = data.answer;
      if (!answer || answer.includes('没有符合条件的评论') || answer.includes('暂无可用评论数据')) {
        answer = '暂无可用评论数据';
      }
      setMessages(msgs => [
        ...(isTaobaoQuery ? msgs.slice(0, -1) : msgs),
        {
          role: 'assistant',
          content: answer,
          charts: Array.isArray(data.charts) && data.charts.length > 0 ? data.charts : []
        }
      ]);
    } catch (e) {
      setMessages(msgs => [
        ...(isTaobaoQuery ? msgs.slice(0, -1) : msgs),
        { role: 'assistant', content: '请求失败，请检查后端服务' }
      ]);
    }
    setLoading(false);
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey && !loading) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{
      maxWidth: 600, margin: '40px auto', fontFamily: 'sans-serif',
      background: '#fff', borderRadius: 12, boxShadow: '0 4px 24px #eee', padding: 24
    }}>
      <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Xtool用户评论分析助手</h2>
      <div
        ref={chatRef}
        style={{
          border: '1px solid #eee',
          borderRadius: 8,
          padding: 16,
          minHeight: 320,
          maxHeight: 400,
          background: '#fafafa',
          overflowY: 'auto'
        }}
      >
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            margin: '8px 0'
          }}>
            <span style={{
              display: 'inline-block',
              background: msg.role === 'user' ? '#cce5ff' : (msg.role === 'assistant' ? '#e2ffe2' : '#f5f5f5'),
              color: msg.role === 'system' ? '#888' : '#222',
              borderRadius: 16,
              padding: '10px 16px',
              maxWidth: '80%',
              wordBreak: 'break-all',
              boxShadow: '0 2px 8px #eee',
              fontStyle: msg.role === 'system' ? 'italic' : 'normal',
              backgroundColor: msg.role === 'system' ? '#f0f0f0' : undefined,
              whiteSpace: 'pre-line'
            }}>
              {/* 只展示文本内容，过滤掉原始JSON */}
              {typeof msg.content === 'string' && msg.content.trim().startsWith('{')
                ? '⚠️ 后端返回了原始数据，请检查后端输出格式'
                : msg.content}
              {/* 只展示图片，不展示路径 */}
              {Array.isArray(msg.charts) && msg.charts.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  {msg.charts.map((url, i) => (
                    <img
                      key={i}
                      src={url}
                      alt="分析图表"
                      style={{
                        maxWidth: '100%',
                        maxHeight: 240, // 新增
                        margin: '12px 0',
                        display: 'block',
                        borderRadius: 8,
                        boxShadow: '0 2px 8px #eee'
                      }}
                    />
                  ))}
                </div>
              )}
            </span>
          </div>
        ))}
        {loading && (
          <div style={{ color: '#888', margin: '8px 0', textAlign: 'left' }}>
            <span className="dot-flashing"></span> 模型思考中...
          </div>
        )}
      </div>
      <div style={{ marginTop: 16, display: 'flex' }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="请输入你的问题"
          style={{
            flex: 1, padding: 12, borderRadius: 8, border: '1px solid #ccc',
            fontSize: 16, outline: 'none', resize: 'vertical', minHeight: 40, maxHeight: 100
          }}
          disabled={loading}
          autoFocus
          rows={2}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          style={{
            marginLeft: 12, padding: '0 24px', borderRadius: 8, fontSize: 16,
            background: loading ? '#ccc' : '#1677ff', color: '#fff', border: 'none', cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? '发送中...' : '发送'}
        </button>
      </div>
      {/* 加载动画样式 */}
      <style>{`
        .dot-flashing {
          position: relative;
          width: 8px;
          height: 8px;
          border-radius: 5px;
          background-color: #bbb;
          color: #bbb;
          animation: dot-flashing 1s infinite linear alternate;
          margin-right: 8px;
          display: inline-block;
        }
        @keyframes dot-flashing {
          0% { background-color: #bbb; }
          50%, 100% { background-color: #eee; }
        }
      `}</style>
    </div>
  );
}

export default App; 