# YojanaMitra

**Your eligibility. Your opportunities. One search.**

Indian scholarships and benefits are published across national and state portals. YojanaMitra uses live You.com research to surface official scheme pages, show published conditions and compare clear rules with your profile.

## YojanaMitra React homepage

Use Node.js 22.12+ or 24+ and Python 3.11+. Set `YOU_API_KEY` in the project's `.env` file using the setup below. From the project directory in PowerShell:

```powershell
npm.cmd ci
npm.cmd run build
.\.venv\Scripts\python.exe yojanamitra_server.py
```

Open [YojanaMitra](http://127.0.0.1:8502). The Python server serves the React build and reuses the existing You.com Search API client. For frontend development, keep the Python server running, execute `npm.cmd run dev` in a second terminal and open the Vite URL printed there.

Use the homepage search or a category card to discover schemes. Open a result to see its official source, prepare an application checklist, or save it with a progress label. The device profile, language and saved list use browser storage. Voice input uses browser speech recognition when supported. Hindi and Marathi translate the homepage and navigation. Published scheme evidence appears in the source language. The assistant shows excerpts and links retrieved through You.com.

The original Streamlit app remains available using the commands below.

## Quick start

Install Python 3.11 or newer. Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Create an API key in the [You.com Platform](https://you.com/platform). Open the local `.env` file and put the key after the equals sign:

```dotenv
YOU_API_KEY=your_actual_api_key
```

Start Streamlit and open [the local app](http://localhost:8501).

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

With the environment already activated, the equivalent commands are `pip install -r requirements.txt` and `streamlit run app.py`.

## Demo

1. Click **Try Sample Student Profile** to populate a 23-year-old undergraduate student in Maharashtra with ₹2,00,000 family income and OBC category.
2. Click **Find My Schemes**. The first submission sends real You.com Search API requests and requires working API credentials and internet access.
3. Try the **Possibly Eligible** or **State Government** filter. Open **Why am I matched with this scheme?** and follow the official details link.

## How it works

- Python and Streamlit handle the UI and session state. Requests calls You.com and python-dotenv loads the local key.
- The app sends two or three targeted requests to the documented You.com Search API and reads web results and extracted highlights. It keeps up to eight distinct results with recognized official HTTPS domains. [You.com Search API reference](https://you.com/docs/api-reference/search/v1-search)
- The matcher extracts labeled evidence and checks explicit rules for age, state, occupation, education, category and income. Unclear or missing rules are flagged. The card displays an application button only if a retrieved official result identifies a scheme-specific application form or online application. Other cards link to official details.
- Results are cached in memory for three minutes per session. Filters use the current session results. Search queries use state, interest and an education level or occupation. Age, income, category and gender stay in the current app session.

## Limitations and next steps

Search coverage depends on the pages You.com returns and what those pages publish in extractable text. Amounts, required documents and deadlines can be missing or refer to earlier application cycles. Confirm the relevant cycle and rules on the official page. The rule matcher supports explicit English wording and sends complex conditions, including marks and exceptions, to manual verification. Discovery can be improved with more state portal patterns, better handling of multilingual guidelines and extraction of complete official eligibility sections.

YojanaMitra is an information discovery assistant, not an official government portal. Eligibility and deadlines must be confirmed on the relevant government website.

## Local tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use representative mocked API responses. To verify an authenticated live request, configure a real key and submit the sample profile in Streamlit.


## Scheme catalogue

YojanaMitra stores scheme records in .yojanamitra.sqlite3. The schemes table retains stable IDs, government level, state, department, official URLs, verification dates and a JSON record for benefits, eligibility evidence, documents and application steps. The categories table connects schemes to browsing categories and benefit types. The refreshes table tracks category cache age.

A category request runs focused You.com searches when its cache is empty or older than six hours. Existing records remain available if a refresh fails. Opening a scheme retrieves deeper information from myScheme or its official department sources and enriches the stored record. Results depend on indexed official sources and observable published evidence.

| Endpoint | Use |
| --- | --- |
| GET /api/schemes | Browse with category, state, scope, benefit, page and limit filters |
| GET /api/schemes/search | Search with q plus the same filters |
| GET /api/schemes/{id} | Read a catalogue record |
| POST /api/eligibility/match | Compare a profile with published conditions for a category or scheme |
| POST /api/research | Retrieve detailed official content and support the existing assistant |

Set YOU_API_KEY in the existing .env file, run npm.cmd run build, then run .venv/Scripts/python.exe yojanamitra_server.py. The preparation review supports Save as PDF through the browser print dialog. Eligibility answers and application drafts are not written to the database.
