import React, { useState } from "react";
import "./app.css";
import { Match, match as runMatch } from "./api";

const App: React.FC = () => {
  const [pattern, setPattern] = useState("");
  const [flags, setFlags] = useState("");
  const [text, setText] = useState("");
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    setMatches([]);

    try {
      const response = await runMatch({ pattern, flags, text });
      setMatches(response.matches ?? []);
    } catch (err: unknown) {
      let message = "Something went wrong while contacting the server.";

      if (err instanceof Error) {
        message = err.message;
      } else if (typeof err === "string") {
        message = err;
      }

      setError(message);
    }
  };

  return (
    <div className="container">
      <h1>Regex-Lite Playground</h1>

      <label>
        Pattern:
        <input value={pattern} onChange={(e) => setPattern(e.target.value)} />
      </label>

      <label>
        Flags (i, m, s, g):
        <input value={flags} onChange={(e) => setFlags(e.target.value)} />
      </label>

      <label>
        Input Text:
        <textarea value={text} onChange={(e) => setText(e.target.value)} />
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
                {match.groups.map((group, i) =>
                  group ? (
                    <li key={i}>
                      Group {i + 1}: [{group[0]}, {group[1]}] → "
                      {text.slice(group[0], group[1])}"
                    </li>
                  ) : (
                    <li key={i}>Group {i + 1}: null</li>
                  ),
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
