// import React, { useState } from "react";
// import { match } from "./api";

// export default function App() {
//     const [pattern, setPattern] = useState("");
//     const [flags, setFlags] = useState("");
//     const [text, setText] = useState("");
//     const [result, setResult] = useState<any>(null);

//     const onSubmit = async (e: React.FormEvent) => {
//         e.preventDefault();
//         const data = await match(pattern, flags, text);
//         setResult(data);
//     };

//     return (
//         <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
//             <h1>regex-lite</h1>
//             <form
//                 onSubmit={onSubmit}
//                 style={{
//                     display: "flex",
//                     flexDirection: "column",
//                     gap: "0.5rem",
//                     maxWidth: "400px",
//                 }}
//             >
//                 <label>
//                     Pattern
//                     <input
//                         value={pattern}
//                         onChange={(e) => setPattern(e.target.value)}
//                     />
//                 </label>
//                 <label>
//                     Flags
//                     <input
//                         value={flags}
//                         onChange={(e) => setFlags(e.target.value)}
//                     />
//                 </label>
//                 <label>
//                     Text
//                     <textarea
//                         value={text}
//                         onChange={(e) => setText(e.target.value)}
//                         rows={4}
//                     />
//                 </label>
//                 <button type="submit">Match</button>
//             </form>
//             {result && (
//                 <div>
//                     <h2>Result</h2>
//                     <pre>{JSON.stringify(result, null, 2)}</pre>
//                 </div>
//             )}
//         </div>
//     );
// }


import React, { useState } from "react";
import "./App.css";

const App: React.FC = () => {
  const [pattern, setPattern] = useState("");
  const [flags, setFlags] = useState("");
  const [text, setText] = useState("");
  const [matches, setMatches] = useState<any[]>([]);
  const [error, setError] = useState("");

  const useMock = import.meta.env.VITE_USE_MOCK === "true";
  const apiBase = "http://localhost:8000";
  const apiPrefix = useMock ? "/mock" : "";

  const handleSubmit = async () => {
    setError("");
    setMatches([]);

    const body = { pattern, flags, text };

    try {
      const response = await fetch(`${apiBase}${apiPrefix}/regex/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) throw new Error("Server error");

      const data = await response.json();
      setMatches(data.matches || []);
    } catch (err: any) {
      setError("Something went wrong: " + err.message);
    }
  };

  return (
    <div className="container">
      <h1>Regex-Lite Playground</h1>

      <label>
        Pattern:
        <input
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
        />
      </label>

      <label>
        Flags (i, m, s, g):
        <input
          value={flags}
          onChange={(e) => setFlags(e.target.value)}
        />
      </label>

      <label>
        Input Text:
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </label>

      <button onClick={handleSubmit}>Run Match</button>

      {error && <p className="error">{error}</p>}

      {matches.length > 0 && (
        <div className="results">
          <h2>Matches</h2>
          {matches.map((match, idx) => (
            <div key={idx}>
              <p>
                Match {idx + 1}: [{match.span[0]}, {match.span[1]}] → "
                {text.slice(match.span[0], match.span[1])}"
              </p>
              <ul>
                {match.groups.map((group: [number, number] | null, i: number) =>
                  group ? (
                    <li key={i}>
                      Group {i + 1}: [{group[0]}, {group[1]}] → "
                      {text.slice(group[0], group[1])}"
                    </li>
                  ) : (
                    <li key={i}>Group {i + 1}: null</li>
                  )
                )}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default App;

