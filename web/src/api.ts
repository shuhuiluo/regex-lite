import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export async function match(pattern: string, flags: string, text: string) {
  const res = await axios.post(`${API_BASE}/regex/match`, { pattern, flags, text });
  return res.data;
}
