# OGE math finish content pack

kim_year: 2026
pack_version: 1.2.0

## context_blocks (12 total)
existing:
  - dacha_sosnovoe (plan)
  - apartment_2room (plan)
  - tires_factory (table, no plan)
  - plan_uchastka_01 (plan)
new:
  - stove_bath_01 (table)
  - tariffs_mobile_01 (table)
  - umbrellas_shop_01 (table)
  - linoleum_repair_01 (plan)
  - car_fuel_01 (table)
  - greenhouse_beds_01 (plan)
  - credit_deposit_01 (table)
  - plan_dvor_01 (plan)

## part1/part2 prototypes
source: backend/universal/specs/math_oge.json + math_oge_finish_extra.json
priority thickened: 12, 19, 22, 25 (+ sparse slots to ≥4)
part2_new_prototypes: 23c/d, 24c/d, 25b/c/d (+ wired figures on 23b/24b)

## svg_23_25
target: ≥12 (≈4 per slot)
files:
  - q23_sample_main.svg (23a)
  - q23_001_main.svg
  - q23_23b_main.svg
  - q23_23c_main.svg
  - q23_23d_main.svg
  - q24_sample_main.svg (24a)
  - q24_001_main.svg
  - q24_24b_main.svg
  - q24_24c_main.svg
  - q24_24d_main.svg
  - q25_sample_main.svg (25a)
  - q25_001_main.svg
  - q25_25b_main.svg
  - q25_25c_main.svg
  - q25_25d_main.svg
count: 15

## seed commands
```powershell
python -m backend.scripts.seed_all_subjects
python -m backend.scripts.seed_oge_math_pack --reset-contexts
python -m backend.scripts.validate_oge_part2_figures
```
