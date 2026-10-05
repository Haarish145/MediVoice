import { SUPPORTED_LANGUAGES } from "../utils/languages";

export default function LanguageSelector({ selected, onSelect }) {
  return (
    <div>
      <p style={{ marginBottom: "0.75rem", color: "#4b5563", fontSize: "0.9rem" }}>
        Select the language you are most comfortable speaking in:
      </p>
      <div className="language-grid">
        {SUPPORTED_LANGUAGES.map((lang) => (
          <button
            key={lang.language_code}
            className={`language-btn ${selected === lang.language_code ? "selected" : ""}`}
            onClick={() => onSelect(lang.language_code)}
            aria-pressed={selected === lang.language_code}
            id={`lang-btn-${lang.language_code}`}
          >
            {lang.display_name}
          </button>
        ))}
      </div>
    </div>
  );
}
