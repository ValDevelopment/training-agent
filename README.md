# Training Periodization Agent

An AI agent that generates personalized strength training programming, grounded in the user's own multi-year training log and periodization philosophy.

## Objective

Population-level strength training research is derived from group averages across highly individualized responses. Grounding programming decisions in an individual's own multi-year, self-observed training results provides a more directly applicable basis for that individual's own program design than general published guidance.

## Data

Approximately two years of personal training log data, most of which predates any export capability in the logging app used. Data for this project's active dataset was manually transcribed from in-app screenshots into `training_log.csv`, covering the most recent 8-to-16-week training block for each of three primary lifts.

**Squat**: April 19 to June 11, 2026 (15 sessions). Percentage-based progression against a 155kg pre-block training max, an accumulation phase through June 1, a deload (June 4, June 8), and a max-test session (June 11).

**Bench press**: June 3 to July 15, 2026 (12 sessions). A scheduled deload (July 18, July 22) and max test (July 25) were planned but had not yet occurred as of this writing. Loads were logged in pounds but physically loaded in kilogram plates; values were converted to the nearest achievable 2.5kg plate increment to preserve the actual loads used, not through a raw unit conversion.

**Deadlift**: April 5 to July 21, 2026 (12 sessions), including a deliberate six-week training break (May 9 to June 23). Structured differently from the squat and bench progressions: each session works up to a top single or triple followed by backoff sets, not an escalating fixed-percentage scheme, reflecting a philosophy of testing a near-maximal effort every session for this lift specifically.

Starting (pre-block) maxes: squat 155kg, bench 120kg, deadlift 160kg (estimated; not a directly tested max, based on a best non-maximal logged set of 140kg x5).

## Methodology

The pipeline runs in three stages:

1. **Log construction** (`scripts/build_training_log.py`): raw, manually transcribed session data is assembled into `data/raw/training_log.csv`.
2. **Pattern extraction** (`scripts/extract_programming_patterns.py`): weekly percent-of-max programming patterns are extracted from the personal log into `data/processed/weekly_programming_patterns.csv`, capturing how load and volume actually progressed session to session, rather than absolute load values. Lift-specific programming templates for squat, bench, and deadlift (`scripts/build_templates.py`) define the baseline percentage and rep structure each extracted pattern is compared against.
3. **Program generation** (`src/program_generator.py`): the extracted patterns and templates feed a generator that produces a new SBD (squat, bench, deadlift) training program, output as both a machine-readable and a human-readable CSV.

`week_num` and `day_num` are computed per lift, relative to that lift's own block start, allowing blocks of different real-world calendar lengths to be compared on a common training-week basis.

## Key Finding

The user's own weekly percent-of-max progression runs noticeably more intense (closer to failure, higher percent of 1RM) than typical published programming templates recommend. This is treated as a deliberate, core part of the training philosophy this project encodes, not as an anomaly to correct.

## Repository Structure

```
training-agent/
├── data/
│   ├── raw/
│   │   └── training_log.csv
│   ├── processed/
│   │   └── weekly_programming_patterns.csv
│   ├── templates/
│   │   ├── squat_programming_template.csv
│   │   ├── bench_programming_template.csv
│   │   ├── deadlift_programming_template.csv
│   │   └── sbd_programming_template.csv
│   └── generated/              # gitignored
│       ├── generated_sbd_program.csv
│       └── generated_sbd_program_readable.csv
├── scripts/
│   ├── build_training_log.py
│   ├── build_templates.py
│   └── extract_programming_patterns.py
├── src/
│   ├── __init__.py
│   └── program_generator.py
├── app.py
├── requirements.txt
└── README.md
```

## Usage

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limitations

- The dataset reflects one individual's response to training; extracted patterns may not generalize universally, though this is partly mitigated by focusing on percent-of-max relative patterns, not absolute loads.
- The deadlift's pre-block max is an estimate, not a directly tested value.
- The bench press block was incomplete as of the most recent update; its scheduled deload and max test had not yet occurred.
