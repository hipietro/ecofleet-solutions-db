<!--
File overview
Purpose: Explain the source-comment convention and document files that cannot contain comments.
Responsibilities: Describe file relationships, configuration sections and generated/vendor boundaries.
Connections: Complements README.md and the file overviews embedded in backend, frontend, SQL and legacy C sources.
-->

# Source comments and configuration guide

## Comment convention

Application source files start with a **File overview** explaining:

- **Purpose:** why the file exists.
- **Responsibilities:** what the code in that file does.
- **Connections:** which modules call it, which modules it uses and which API/database contracts it shares.

Logical sections then explain intent near the relevant code: imports, state, effects, HTTP requests, response handling, rendering, validation, queries, transactions, reporting and cleanup. Comments are written in English. They explain groups of related operations rather than repeating every statement.

Python uses `#` comments, TypeScript/JavaScript/C/CSS use line or block comments, SQL uses `--`, and HTML/Markdown use HTML comments. JSX child sections use `{/* ... */}` so explanations do not appear in the rendered page. TypeScript configuration files support JSONC comments.

## Main application relationships

| Flow | Files involved |
| --- | --- |
| Browser startup | `frontend/index.html` → `frontend/src/main.tsx` → `frontend/src/App.tsx` |
| Page navigation | `frontend/src/routes/paths.ts` → App route definitions and page navigation callbacks |
| Backend address | `frontend/src/config/api.ts` → Login, Dashboard and Fleet HTTP requests |
| Login | Login page → backend auth router → security helpers and Cliente records |
| Protected requests | Stored bearer token → backend authentication dependency → current database account/role |
| Available vehicles | Fleet page → backend fleet router → per-vehicle PostgreSQL rate lookup |
| Personal history | Dashboard → backend rentals router → Noleggio plus nested vehicle/battery details |
| Rental completion | Rentals router → PostgreSQL billing/mileage/receipt triggers → wallet and vehicle updates in one transaction |
| Reporting | Backoffice router → completed rental data → pandas/NumPy aggregation or OpenPyXL export |
| Integration checks | Existing backend tests → disposable local database and API server → real HTTP requests |

Frontend interfaces provide compile-time descriptions, not runtime JSON validation. Pydantic defines and validates the corresponding backend contracts. Monetary `Decimal` values are serialized as strings and converted to numbers in React only for display formatting.

## Files that require strict JSON

These files cannot contain comments without breaking their consumers. Their explanations live here instead.

### `frontend/package.json`

**Purpose:** define the frontend npm package, commands and dependency declarations.

**Connections:** npm reads this file; Vite, TypeScript and ESLint run through its scripts. It is paired with `frontend/package-lock.json`.

| Section | Responsibility |
| --- | --- |
| `name`, `version`, `private` | Identify the local package and prevent accidental npm publication. |
| `type` | Select ECMAScript module semantics for JavaScript configuration files. |
| `scripts.dev` | Run the Vite development server. |
| `scripts.build` | Check TypeScript project references, then build with Vite. |
| `scripts.lint` | Run the rules in `eslint.config.js`. |
| `scripts.preview` | Serve an existing production build for local preview. |
| `dependencies` | Declare React, React DOM and React Router runtime packages. |
| `devDependencies` | Declare TypeScript, Vite, Tailwind, ESLint and related development plugins/types. |

### `frontend/package-lock.json`

**Purpose:** record the resolved npm dependency tree for reproducible installation.

**Connections:** generated and maintained by npm from `package.json`; consumed by `npm ci`.

| Section | Responsibility |
| --- | --- |
| Root package metadata | Associate the lockfile with the frontend package. |
| `lockfileVersion` | Identify the npm lockfile format. |
| `packages` | Record resolved versions, package relationships and available integrity metadata. |

Do not annotate or hand-edit this generated file. Dependency changes should update it through npm.

## Existing files with limited or inactive roles

- `frontend/src/App.css` retains starter styles and is currently not imported by the application. Its sections are documented without activating them.
- `frontend/tailwind.config.js` retains a configuration scaffold. The current Tailwind v4 path uses the Vite plugin and `src/index.css`, without an explicit `@config` reference to that file.
- `frontend/postcss.config.js` intentionally declares no plugins; it does not duplicate the Tailwind Vite integration.
- Python `__init__.py` files mark package boundaries. Their new overviews explain those relationships without initializing state or registering endpoints.
- `sql/ecofleet.sql` is the destructive academic initialization script. Its baseline hourly pricing function is replaced by the later stabilization migration; comments distinguish the two versions.
- `legacy/c/query_all.c` talks directly to PostgreSQL through libpq. It does not use the FastAPI configuration, token or routes.

## Generated, external and non-code files

Virtual environments, `node_modules`, build output and Python bytecode are generated dependencies/artifacts, not application source. The bundled libpq headers and native libraries under `legacy/c/dependencies/` are third-party files; their content is preserved. Their usage is explained by the C source overview and the adjacent README.

Images, SVG assets, the academic PDF and existing prose documentation do not receive artificial code sections. They remain documented as resources in the main README and the project-structure guide.

## Existing verification commands

From the repository root:

```bash
npm --prefix frontend run build
npm --prefix frontend run lint
ECOFLEET_RUN_DB_TESTS=1 venv/bin/python -m unittest discover -s backend/tests -v
```

The integration suite uses its own temporary database. Source-comment updates do not require applying SQL scripts to the development database.
