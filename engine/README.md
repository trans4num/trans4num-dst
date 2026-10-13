# Trans4Num

This is our optimizer for the first Trans4Num workshop.

## Data
The source data used in this project can be found in S3.

A download script is included in the repo and can be used with the following command:

```bash
export TRANS4NUM_SOURCE_DATA_URI=s3://YOUR_SOURCE_BUCKET/YOUR_PREFIX
./scripts/download_data.sh
```

`TRANS4NUM_SOURCE_DATA_URI` must point to the S3 prefix containing the source
files. The bucket name is intentionally supplied by the environment rather
than stored in the repository.

The S3-backed engine store also requires the runtime bucket to be configured:

```bash
export TRANS4NUM_STORAGE_BUCKET=YOUR_RUNTIME_BUCKET
```

Use `--store-type local` for local engine runs that use the local file store
instead. The repository root includes a Compose configuration that runs this
mode in Docker and shares its files with the backend.

## Optimization preparation

The engine assumes a fresh AWS Lambda execution environment for each job. Source
fields are read for each job. Crop-transition coefficients are reused by full
crop sequence, soil, and metric within that job, avoiding repeated calculations
across fields and constraints. This bounded coefficient cache is cleared at job
entry, so benchmarks and behavior do not depend on earlier invocations.

Model preparation removes dominated rotation options only after comparing the
objective and every enabled regional/farmer constraint, using the exact same
integer-scaled coefficients as CP-SAT. The existing rotation is always retained.
Unrecognized constraint implementations opt out of pruning, and an enabled
constraint without an implementation raises an error instead of being ignored.

Prepared map geometry is persisted in S3 (or the local file store) and reused
across simulations, including fresh containers. Its cache key includes the
geometry source version and selected field IDs, so a changed source or field set
regenerates it. Custom stores can opt out through the default `IStore` methods.

## Regional allocation fast path

Economy and nitrogen-load objectives with zero or one plain regional additive
constraint can use a continuous allocation relaxation with a whole-field repair.
The result has one actual rotation per field, is checked against the same
integer-scaled constraints as CP-SAT, and includes a regional lower bound.

Grouped farmer constraints, multiple regional constraints, and custom constraint
implementations use CP-SAT. Eligibility is based
on the prepared constraint objects, not a list of UI constraint names. New
constraint types therefore default to the general solver. If the repaired
allocation misses the requested gap, it becomes a feasible solver hint and
fallback candidate rather than being accepted as a sufficiently accurate result.

## Regional economy per nitrogen load

`maximizeEconomyNLoad` maximizes **total regional economy / total regional
N-load**. It no longer minimizes a sum of individual field ratios. Internally,
the equivalent minimization is **total N-load / total economy**, which remains
finite when nitrogen load is zero and economy is positive.

Dinkelbach iterations solve the additive objective `N - lambda * E`, where
`lambda` is the best feasible regional `N/E` found so far. Crop metrics and
integer-scaled hard constraints are prepared once; each iteration changes only
the objective. Eligible iterations use regional allocation, and more complex
constraints use CP-SAT. The CP-SAT variable/constraint matrix is built once and
reused with updated objectives and checked hints within the same invocation.
Ratio pruning compares economy and nitrogen load separately, together with
every active constraint, so an option with a worse field ratio can still be
chosen when it improves the region's totals.

The objective requires nonnegative field nitrogen loads and positive regional
economy. Individual field economy can be zero or negative. When positivity is
not already guaranteed by the options, a conservatively integer-scaled constraint
requires at least `1e-6` DKK of regional economy. Zero regional nitrogen load is
an optimal inverse ratio of zero, avoiding an infinite JSON objective.

Each additive lower bound is translated into a regional ratio lower bound using
the prepared bounds on total economy. The reported ratio gap is
`(best_ratio - lower_bound) / best_ratio`, or zero for zero nitrogen load. Inner
linear gaps are never presented as regional-ratio gaps. Metadata identifies the
objective as `regional_nload_per_economy` in `kg N / DKK` and records the number
of fractional iterations. Existing simulation files are not recalculated.

All iterations share one search-time budget; reaching a budget or iteration
limit returns the best feasible regional ratio with its actual gap. The default
iteration limit is 64, configurable with `maxFractionalIterations` in request
settings or `TRANS4NUM_OPTIMIZER_MAX_FRACTIONAL_ITERATIONS`. Source data and
coefficients retain cold-invocation semantics: only the current job's selections
are used for iteration hints.

## Solver budgets and result quality

The defaults are a 120-second CP-SAT search budget, a normalized relative gap of
0.05 (5%), eight search workers, and an enabled allocation fast path. Set these
environment variables when starting Compose/the root CLI:

| Variable | Default |
| --- | --- |
| `TRANS4NUM_OPTIMIZER_MAX_TIME_SECONDS` | `120` |
| `TRANS4NUM_OPTIMIZER_RELATIVE_GAP` | `0.05` |
| `TRANS4NUM_OPTIMIZER_WORKERS` | `8` (use `0` for automatic) |
| `TRANS4NUM_OPTIMIZER_FAST_PATH` | `true` |
| `TRANS4NUM_OPTIMIZER_DEBUG` | `false` |
| `TRANS4NUM_OPTIMIZER_MAX_FRACTIONAL_ITERATIONS` | `64` |

For example, `TRANS4NUM_OPTIMIZER_MAX_TIME_SECONDS=30
TRANS4NUM_OPTIMIZER_RELATIVE_GAP=0.01 ./trans4num --region REGION_UUID` requests
a 30-second solver budget and a 1% gap. The budget covers CP-SAT search, including
presolve, rather than input loading/model building/output generation. A time
limit may return a feasible result with a larger gap, or no result if neither
the solver nor a checked starting selection found one.

API clients can override the defaults per simulation using `optimizationSettings`:

```json
{
  "name": "Preview",
  "regionId": "REGION_UUID",
  "model": "<the normal model object>",
  "optimizationSettings": {
    "maxTimeSeconds": 30,
    "relativeGap": 0.01,
    "workers": 8,
    "useFastPath": true
  }
}
```

An explicit settings object uses its own defaults for omitted fields; otherwise
the environment is used. Set the gap to zero to request exact search, or disable
the fast path to compare CP-SAT directly. Native gap stopping observes both
incumbent and bound improvements. Starting selections are constructed from the
current job's allocation or source baseline and checked against all current
constraints before use as hints or timeout fallbacks.
For supported additive constraints, greedy improvement of a feasible seed checks
every regional/farmer limit after each field move. This heuristic is only a
starting solution; it never supplies its own optimality bound. Solver hints and
fallbacks therefore work on cold invocations without a previous simulation.

The local backend serializes requests to its single Lambda emulator and consumes
each invocation response before starting the next one. Cloud Lambda execution
is unaffected by this local queue behavior.

Completed and solver-failed simulations expose `optimization` metadata: method,
optimal/feasible/missing status, objective, lower bound, normalized relative gap,
termination reason, requested budget, and phase timings. Objectives use the
engine's minimization convention (economy is negative). The normalized gap is
`max(0, objective - bound) / max(1, abs(objective))`, which is also defined for
negative and zero objectives. The configuration dialog displays quality and
timings for new results; older simulations can omit these fields.
The regional-ratio objective uses its ratio-specific gap definition above.

Engine regression tests use Python's standard `unittest` runner. With the local
Docker image built, run from the repository root:

```bash
docker run --rm --entrypoint /opt/conda-env/bin/python \
  -v "$PWD:/workspace:ro" -w /workspace/engine \
  -e PYTHONPATH=/workspace/engine/src:/workspace/common \
  open-source-engine -m unittest discover -s tests -v
```

# Objectives:
Mixed (nloadperecon): Minimize total regional N-load / total regional economy
Economy (economy): Maximize economy -> Constraints for hvad nload må blive
Emision (nload): Minimize (nload) -> Constraints for hvad økonomi må blive

# Constraints
* nload_change_percent: Eksempelvis -10 betyder at nload skal reduceres med mindst 10
* economy_change_percent: Eksempelvis -10 betyder at vi maksimalt må reducere økonomien med 10
* max_change_of_field_pct: Eksempelvis 15 betyder at vi må ændre 15% af markerne
* max_change_of_area_pct: Eksempelvis 15 betyder at vi må ændre 15% af arealet
* max_revenue_per_org_change_pct: Eksempelvis -5 betyder at vi reducerer økonomien med 5 % på den mest ramte farm
* max_distance_to_biora: Eksempelvis 30 betyder at vi kun må ligge græs ud hvis marken er inden for 30km af biogas.
* max_nature_value_for_changed_field: Eksempelvis 40 betyder at vi ikke må ændre på en mark med mere end 40% højnatur.


# Summary
* economy: The total economy of the entire site.
* nload: The total nload of the entire site.
* nature: The mean percentage of fields with nature value over 5
* consistency: The percentage of area not touched
* fieldConsistency: The percentage of fields not touched
* farmEconomy: The percentage of economy left fort the most affected farm.
* nloadPerEcon: How much do we leach for every economy we gain. The lower the better.


# Todo:

## Data available
* We could use ID15, to run som constraints or optimizations within each of the smaller catchments.
* delop_id can be used to split into the two real regions, instead of a single region for the limfjord catchment.
* Nature value: Should this be internal or external parameter.
* I use road distance to biogas. Should we make this influence the price of grass? (Internal parameter or external parameter).


## Crop rotations
* I have interpreted pulses as legumes.
* How am I encoding the crop rotations from the existing crops?
* Are we only allowed to go from some of the before to some of the after?
* Are we only allowed to have the from rotations before?
* I have decided to average over the length, to handle very varying length of rotations.
* Right now I ignore the cost of going from one rotation to another. Should that be taken into account?
* Our check on where we introduce grass is a bit weird now, which rotations should be placed based on this? Maybe it makes snese to make an internal depency where it modifies economy of grass.
* Something is wrong, we have a suggested rotation with transitions which should not be possible? Arable: cereal spring with cover crop -> rape seed
* Something is wrong, we have a suggested rotation with transitions which should not be possible? Cattle: maize -> grass/clover fertilized to norm
* Something is wrong, we have a suggested rotation with transitions which should not be possible? Dairy Organic: potato -> grass/clover fertilized to norm

## Tool
* Update frontend with new names (would be cool if it was dynamic and not hardcoded)
* We should consider if there should be more focus on evaluating the output, and less variability in creating scenarios? Maybe we should make most of the choices internal parameters of the model.
