# AfterThought app guide

AfterThought is Arsh Talkhani’s local evidence workspace: a working browser UI over the existing Deep Research Bench Python runner, with an Einstein’s Jump research companion and a real published FlyWire metadata connection. The application uses an ivory, copper, and olive theme with locally bundled fonts.

## Start the app

Run from the repository checkout with Python 3.8 or newer:

```text
python run_app.py --preload-connectome
```

Open <http://127.0.0.1:8765>. Windows users can double-click `start-app.cmd`. The launcher preloads the dataset before serving; without the preload flag, use **Load FlyWire snapshot** in the app. No runtime dependencies, provider accounts, API keys, or build step are required.

The server binds only to the loopback interface. Keep its terminal open; stop it with Ctrl+C. Choose another port with `python run_app.py --port 8766 --preload-connectome`, then use that port in the browser.

## Presenter walkthrough

The in-app **Live demo guide** contains eight buttons that perform the real steps below. Return to that navigation item between steps.

| Step                       | Action                                   | Expected evidence                                                                                                                                                                                           |
| -------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Introduce AfterThought     | Open introduction                        | The scorer, research notebook, and metadata connector have distinct roles and explicit limits.                                                                                                              |
| Run a passing example      | Run the authored Python 3.13 answer      | 111 words, one citation, one case passed; regex, citation count, and word count each pass.                                                                                                                  |
| Show a failing answer      | Run “Python is great.” without citations | Three words; all three checks fail with inspectable details.                                                                                                                                                |
| Run the mock suite         | Run all ten public cases                 | Ten scored cases, explicitly labeled deterministic mock; the deliberately weak mock passes none overall. Export JSON or Markdown.                                                                           |
| Query FlyWire              | Find GABA neurons                        | 139,255 total records and 16,017 GABA matches in the currently fetched snapshot. Counts are calculated from source rows.                                                                                    |
| Inspect one neuron         | Find `720575940598267657`                | One record: group `ME`, predicted transmitter `GABA`, confidence `0.74`. All 18 ID digits remain intact.                                                                                                    |
| Connect data to evaluation | Run the FlyWire research demo            | A sourced editable brief reports 139,255 total, 16,017 predicted GABA, and a calculated 11.50% share; the unedited draft passes the three scorers. Alter a count or remove a citation, then evaluate again. |
| Explain the research       | Open The follow-up                       | Einstein’s Jump reports an honest null result on its two fraud-record cases and explains the positive control. Historical findings are attributed, not rerun.                                               |

These snapshot figures were measured from the official archive. The source-derived brief calculates its expected facts on the server, not from a visible 30-row sample. Its case is separate from `public-10-v1`; it does not change the ten-case suite.

## Working with answers and reports

Browse or filter the ten public cases across nine category labels. Selecting a row reveals its question, regex rules, citation minimum, length minimum, and unexecuted judge rubric. Paste an answer and HTTP(S) citation URLs, one per line, then choose **Evaluate answer**.

Reports preserve the actual runner output and distinguish manual answers, deterministic mock output, and source-derived evidence evaluations. **Evaluation runs** retains up to 30 reports in browser memory. Use the report’s JSON or Markdown export to keep evidence; reloading clears run history and answer drafts. The server does not store submitted answers.

The FlyWire brief joins the two working systems: complete source metadata supplies counts and a calculated fraction; a deterministic template supplies an editable draft; the existing `RegexScorer`, `CitationCountScorer`, and `WordCountScorer` evaluate the submitted text. No new AI model or hidden judge is involved.

## Meaning and limits

A passing structural score does not establish factual correctness, valid citations, sound reasoning, or scientific novelty. Regex checks can match repeated terms without understanding them. Citation URLs are counted, not fetched or verified. The word scorer splits on whitespace. No live research engine or LLM judge is connected, and manual submissions retain `generated_by_app: false` metadata.

Einstein’s Jump supplies a seven-phase research notebook with links to its original evidence. Its bounded historical findings do not establish a universal theorem about creativity or judges.

FlyWire results are **static metadata**, not live neural activity. A source group such as `ME` is a source grouping, not an invented cell-type name. Transmitter labels and confidence values are predictions. The app does not fetch the large synaptic graph, simulate neural activity, authenticate to CAVE, or use a fly brain to reason.

## Dataset access and licensing

The connector reads one fixed official [FAFB v783 neuron archive](https://storage.googleapis.com/flywire-data/codex/data/fafb/783/neurons.csv.gz). The first explicit load or preload retrieves approximately 1.7 MB; subsequent requests use ignored `.cache/flywire/`. A valid local cache works offline. Downloads are limited to 4 MB compressed, 40 MB decoded, and 200,000 parsed records for this fixed snapshot. One immutable parsed snapshot is shared across query threads and invalidated when the cache file changes. A corrupt cache triggers one validated refetch before atomic replacement; an invalid replacement is not published.

Raw data is not bundled or committed. **CC BY-NC 4.0** applies to the FlyWire data independently of the source code’s MIT license. Follow the [official citation guidelines](https://join.flywire.ai/guidelines) and preserve the applicable dataset attribution. The [official Codex loader](https://github.com/murthylab/codex/blob/main/codex/data/local_data_loader.py) defines the archive source. The external [Codex explorer](https://codex.flywire.ai/app/explore) requires sign-in; this app’s bounded static download does not use a Codex/CAVE token.

## Recovery during a demo

- **Port occupied:** stop the existing app instance, or restart with `--port 8766` and use the corresponding browser URL.
- **Dataset unavailable:** use **Load FlyWire snapshot** or **Refresh metadata view** to retry. Check internet access if no valid cache exists. Preload failure does not prevent local scoring from starting.
- **No matching neurons:** clear the query or choose **All transmitters** and search again. Empty matches are a valid result.
- **Scoring request refused:** check the visible error. Answers are bounded to 200,000 characters; citations must be HTTP(S) URLs, at most 100, each no longer than 2,048 characters.
- **Nothing to export:** run an evaluation first. Export before reloading because history is temporary.
- **Server unavailable:** keep the launcher terminal running. Restart the app, reload the browser, and repeat the demo action.

## HTTP surface

All endpoints are served on the same loopback origin as the UI. No answer or dataset is sent to an AI provider.

| Request                                        | Purpose                                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------------------------- |
| `GET /api/health`                              | Local server status, case count, and whether startup preload succeeded.               |
| `GET /api/cases`                               | The actual versioned public suite and scoring contracts.                              |
| `POST /api/run`                                | Evaluate selected public cases in explicit manual or mock mode.                       |
| `GET /api/connectome?q=&transmitter=&limit=30` | Search real metadata; result limit is 1–100 and neuron IDs remain strings.            |
| `GET /api/connectome/brief`                    | Calculate source facts and return the separate evidence case and deterministic draft. |
| `POST /api/connectome/evaluate`                | Score submitted brief text and citations against server-owned snapshot facts.         |

Unexpected Host/cross-origin requests are refused. POST bodies are capped at 1 MB; the server exposes no arbitrary file-write, shell-execution, or user-supplied remote-fetch endpoint.

## Checks

For the complete suite, install the development extra and run:

```text
python -m pip install -e ".[dev]"
python -m pytest -q
```

The added app checks use the standard library. Set `PYTHONPATH=src` first, then run:

```text
python -m unittest discover -s tests -p "test_web.py" -v
python -m unittest discover -s tests -p "test_connectome*.py" -v
```

In PowerShell, set the path with `$env:PYTHONPATH = "src"`; in a POSIX shell use `export PYTHONPATH=src`.

The web checks exercise the real HTTP server and existing runner/scorers, including manual passes/failures, report contents, explicit mock labels, Host/origin refusal, request bounds, static containment, and fixed errors. Metadata tests cover parsing, full-precision IDs, filtering, bounded downloads, corrupt-cache recovery, and concurrent reuse. Evidence-brief tests cover source-count consistency and meaningful failing answers through the actual scorers. Passing fixtures do not claim actual-provider, neural-simulation, or general scientific correctness.

## Visual and source credits

The Deep Research Bench core retains its [MIT license](../LICENSE) and package namespace; its [framework guide](../docs/framework.md) documents the extension APIs. Research summaries link to Arsh’s [Einstein’s Jump](https://github.com/dnarsh/einsteins-jump).

Geist (Geist Project Authors) and Newsreader (Newsreader Project Authors) are locally bundled under the SIL Open Font License: [Geist license](fonts/OFL.txt), [Newsreader license](fonts/Newsreader-OFL.txt). The neuron graphic is an original schematic, not measured connectivity. The banner and brand assets identify AfterThought; the [repository QR](assets/brand/github-qr.svg) points to <https://github.com/dnarsh/AfterThought>.
