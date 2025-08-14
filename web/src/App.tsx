import React, { useState } from 'react';
import { match } from './api';

export default function App() {
  const [pattern, setPattern] = useState('');
  const [flags, setFlags] = useState('');
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data = await match(pattern, flags, text);
    setResult(data);
  };

  return (
    <div style={{ padding: '1rem', fontFamily: 'sans-serif' }}>
      <h1>regex-lite</h1>
      <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: '400px' }}>
        <label>
          Pattern
          <input value={pattern} onChange={e => setPattern(e.target.value)} />
        </label>
        <label>
          Flags
          <input value={flags} onChange={e => setFlags(e.target.value)} />
        </label>
        <label>
          Text
          <textarea value={text} onChange={e => setText(e.target.value)} rows={4} />
        </label>
        <button type="submit">Match</button>
      </form>
      {result && (
        <div>
          <h2>Result</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
