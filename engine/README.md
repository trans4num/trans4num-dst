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

# Objectives:
Mixed (nloadperecon): Minimize (nload/econ)
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
