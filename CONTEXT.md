# OcéEns

EPF's course-evaluation platform: surveys are created per program, students answer them, and the answers are exported, visualised and summarised.

## French and English

The code, issues, ADRs and documentation are in **English**. The application itself is **French**: its interface, its messages, its prompts, and the words its users say. Where the documentation names something the users see, it keeps the French word, in italics, with its English equivalent the first time:

| French (product) | English (code, docs) |
|---|---|
| *sondage* | survey |
| *synthèse* | summary (an LLM summary of free-text answers) |
| *verbatim* | free-text answer |
| *filière*, *formation* | program |
| *connexion de développement* | development login |

Interface labels quoted in the docs (« Changer d'utilisateur », *Tester*) stay in French, as they appear on screen. Code identifiers keep whatever language they already have (`sondage_loader.py`, `SurveyTemplate`): renaming them is a code change, not a documentation one.

## Language

### Authentication

**Development login** (*connexion de développement*, `AUTH_MODE=dev`):
Login without an identity provider: you pick a user's e-mail address and are logged in as that user, with no proof of identity. It exists only when `AUTH_MODE=dev` and must never be used in production.
_Avoid_: impersonation, spoofing, fake login
