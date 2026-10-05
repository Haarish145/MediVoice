# Language Support Matrix

MediVoice supports 12 regional languages out-of-the-box with extensible configuration:

| Language | Code | Locale | Speech Rec Code | TTS Code | Dialect Support Notes |
|----------|------|--------|-----------------|----------|-----------------------|
| Tamil | ta | ta-IN | ta-IN | ta-IN | Regional accent supported |
| Hindi | hi | hi-IN | hi-IN | hi-IN | Standard & regional conversational |
| Telugu | te | te-IN | te-IN | te-IN | Standard conversational |
| Kannada | kn | kn-IN | kn-IN | kn-IN | Standard conversational |
| Malayalam | ml | ml-IN | ml-IN | ml-IN | Standard conversational |
| Bengali | bn | bn-IN | bn-IN | bn-IN | Standard conversational |
| Marathi | mr | mr-IN | mr-IN | mr-IN | Standard conversational |
| Gujarati | gu | gu-IN | gu-IN | gu-IN | Standard conversational |
| Punjabi | pa | pa-IN | pa-IN | pa-IN | Standard conversational |
| Odia | or | or-IN | or-IN | or-IN | Standard conversational |
| Assamese | as | as-IN | as-IN | as-IN | Standard conversational |
| English | en | en-US | en-US | en-US | Standard healthcare English |

Extensibility: Additional languages can be added in `app/api/routes/languages.py` or configuration without modifying core triage engine logic.
