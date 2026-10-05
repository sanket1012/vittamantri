import { useEffect, useRef, useState } from 'react';
import SendIcon from '@mui/icons-material/Send';
import { Box, Card, CircularProgress, IconButton, TextField, Typography } from '@mui/material';
import toast from 'react-hot-toast';
import { askInsightAgent } from '../api/client.js';

const SUGGESTIONS = [
  'How much have I spent this month?',
  "What's my biggest spending category?",
  'How much did I spend on food?',
  'Am I saving money this month?',
];

function MessageBubble({ role, content }) {
  const isUser = role === 'user';
  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <Box
        sx={{
          maxWidth: '75%',
          bgcolor: isUser ? '#111827' : '#F0EBE2',
          color: isUser ? '#FFFFFF' : '#20242C',
          borderRadius: '14px',
          borderBottomRightRadius: isUser ? '4px' : '14px',
          borderBottomLeftRadius: isUser ? '14px' : '4px',
          px: 2,
          py: 1.25,
          fontSize: '0.9375rem',
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
        }}
      >
        {content}
      </Box>
    </Box>
  );
}

export default function InsightChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  const send = async (question) => {
    const text = (question ?? input).trim();
    if (!text || sending) return;
    setInput('');
    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setSending(true);
    try {
      const answer = await askInsightAgent(text, history);
      setMessages((prev) => [...prev, { role: 'assistant', content: answer }]);
    } catch (err) {
      toast.error(err.response?.data?.error || 'Could not reach the assistant.');
      setMessages((prev) => [...prev, { role: 'assistant', content: "Sorry, I couldn't answer that right now. Please try again shortly." }]);
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    send();
  };

  return (
    <Card sx={{ height: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #E3DDD4', display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box component="span" sx={{ color: '#6E72AE', fontSize: 16, lineHeight: 1 }}>✦</Box>
        <Box>
          <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#20242C' }}>Ask Samvitta</Typography>
          <Typography sx={{ fontSize: '0.875rem', color: '#77736D' }}>Questions about this month's household finances</Typography>
        </Box>
      </Box>

      <Box ref={scrollRef} sx={{ flex: 1, overflowY: 'auto', p: 3, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {messages.length === 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mt: 'auto', mb: 2 }}>
            <Typography sx={{ fontSize: '0.8125rem', color: '#77736D', mb: 0.5 }}>Try asking:</Typography>
            {SUGGESTIONS.map((s) => (
              <Box
                key={s}
                component="button"
                type="button"
                onClick={() => send(s)}
                sx={{
                  textAlign: 'left',
                  border: '1px solid #E3DDD4',
                  borderRadius: '10px',
                  px: 2,
                  py: 1.25,
                  bgcolor: '#FFFFFF',
                  color: '#20242C',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  '&:hover': { borderColor: '#C7A66A', bgcolor: '#FBF8F2' },
                }}
              >
                {s}
              </Box>
            ))}
          </Box>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} />
        ))}
        {sending && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
            <Box sx={{ bgcolor: '#F0EBE2', borderRadius: '14px', px: 2, py: 1.25 }}>
              <CircularProgress size={16} sx={{ color: '#77736D' }} />
            </Box>
          </Box>
        )}
      </Box>

      <Box component="form" onSubmit={handleSubmit} sx={{ p: 2, borderTop: '1px solid #E3DDD4', display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Ask about this month's spending…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
        />
        <IconButton type="submit" disabled={sending || !input.trim()} sx={{ bgcolor: '#111827', color: '#FFFFFF', '&:hover': { bgcolor: '#20242C' }, '&.Mui-disabled': { bgcolor: '#E3DDD4', color: '#AAA' } }}>
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>
    </Card>
  );
}
