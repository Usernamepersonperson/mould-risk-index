# Measured results (simulated flats, real outdoor weather)

Weather: Open-Meteo Historical Weather API (CC BY 4.0), reanalysis-based, 2025-10-15 to 2026-03-31; main city zurich. Mould class: sensitive.

## 3 behaviours x 2 building types (Zurich)

| building | behaviour | days_m_ge_1 | days_m_ge_3 | max_mould_idx | hours_rh_surf_ge_80 | days_rule80_7d | mean_rh_in | heating_kwh | alerts_watch | alerts_warn | alerts_critical | months_failing_80_rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| altbau | bad | 0 | 0 | 0.84 | 2000 | 84 | 54.95 | 3676.25 | 81 | 79 | 0 | 4 |
| altbau | typical | 0 | 0 | 0.06 | 444 | 4 | 46.00 | 4578.66 | 37 | 28 | 0 | 0 |
| altbau | good | 0 | 0 | 0.01 | 82 | 0 | 41.55 | 5269.06 | 15 | 7 | 0 | 0 |
| renovated | bad | 154 | 108 | 5.28 | 3967 | 166 | 82.74 | 565.04 | 1 | 4 | 1 | 7 |
| renovated | typical | 0 | 0 | 0.59 | 1470 | 61 | 59.05 | 1127.30 | 55 | 58 | 0 | 2 |
| renovated | good | 0 | 0 | 0.02 | 142 | 0 | 46.45 | 1699.61 | 24 | 14 | 0 | 0 |

## Cities (days with mould index >= 1)

| city | altbau_bad | altbau_good | altbau_typical | renovated_bad | renovated_good | renovated_typical |
|---|---|---|---|---|---|---|
| basel | 0.00 | 0.00 | 0.00 | 155.00 | 0.00 | 0.00 |
| bern | 0.00 | 0.00 | 0.00 | 154.00 | 0.00 | 0.00 |
| davos | 0.00 | 0.00 | 0.00 | 151.00 | 0.00 | 0.00 |
| geneva | 22.00 | 0.00 | 0.00 | 155.00 | 0.00 | 0.00 |
| lugano | 0.00 | 0.00 | 0.00 | 155.00 | 0.00 | 0.00 |
| zurich | 0.00 | 0.00 | 0.00 | 154.00 | 0.00 | 0.00 |

## Airing / setpoint sweeps (Zurich)

| building | behaviour | change | value | airing_min_per_day | days_m_ge_1 | max_mould_idx | hours_rh_surf_ge_80 | heating_kwh | mean_rh_in |
|---|---|---|---|---|---|---|---|---|---|
| altbau | bad | airing | 0.00 | 0.00 | 0 | 0.84 | 2000 | 3676.25 | 54.95 |
| altbau | bad | airing | 10.00 | 10.00 | 0 | 0.35 | 1416 | 3893.59 | 51.65 |
| altbau | bad | airing | 20.00 | 20.00 | 0 | 0.13 | 1069 | 4108.44 | 49.65 |
| altbau | bad | airing | 30.00 | 30.00 | 0 | 0.07 | 896 | 4320.58 | 48.39 |
| altbau | bad | airing | 45.00 | 45.00 | 0 | 0.05 | 749 | 4633.33 | 47.30 |
| altbau | bad | setpoint | 1.00 | 0.00 | 0 | 0.57 | 1611 | 4146.22 | 51.42 |
| altbau | bad | setpoint | 2.00 | 0.00 | 0 | 0.30 | 1207 | 4622.21 | 48.16 |
| altbau | typical | airing | 0.00 | 8.04 | 0 | 0.06 | 444 | 4578.66 | 46.00 |
| altbau | typical | airing | 10.00 | 18.04 | 0 | 0.03 | 273 | 4814.09 | 44.31 |
| altbau | typical | airing | 20.00 | 28.04 | 0 | 0.02 | 198 | 5046.49 | 43.25 |
| altbau | typical | airing | 30.00 | 38.04 | 0 | 0.02 | 172 | 5275.76 | 42.58 |
| altbau | typical | airing | 45.00 | 53.04 | 0 | 0.01 | 162 | 5613.44 | 42.02 |
| altbau | typical | setpoint | 1.00 | 8.04 | 0 | 0.04 | 254 | 5075.00 | 43.26 |
| altbau | typical | setpoint | 2.00 | 8.04 | 0 | 0.02 | 141 | 5578.79 | 40.72 |
| renovated | bad | airing | 0.00 | 0.00 | 154 | 5.28 | 3967 | 565.04 | 82.74 |
| renovated | bad | airing | 10.00 | 10.00 | 146 | 1.78 | 2855 | 809.83 | 66.18 |
| renovated | bad | airing | 20.00 | 20.00 | 0 | 0.41 | 1527 | 1053.29 | 58.00 |
| renovated | bad | airing | 30.00 | 30.00 | 0 | 0.12 | 993 | 1294.81 | 53.75 |
| renovated | bad | airing | 45.00 | 45.00 | 0 | 0.06 | 698 | 1652.95 | 50.46 |
| renovated | bad | setpoint | 1.00 | 0.00 | 155 | 5.24 | 3919 | 800.01 | 78.47 |
| renovated | bad | setpoint | 2.00 | 0.00 | 155 | 4.96 | 3782 | 1038.76 | 73.73 |
| renovated | typical | airing | 0.00 | 8.04 | 0 | 0.59 | 1470 | 1127.30 | 59.05 |
| renovated | typical | airing | 10.00 | 18.04 | 0 | 0.08 | 505 | 1393.76 | 51.45 |
| renovated | typical | airing | 20.00 | 28.04 | 0 | 0.03 | 269 | 1657.76 | 47.63 |
| renovated | typical | airing | 30.00 | 38.04 | 0 | 0.02 | 189 | 1919.34 | 45.47 |
| renovated | typical | airing | 45.00 | 53.04 | 0 | 0.01 | 153 | 2307.20 | 43.71 |
| renovated | typical | setpoint | 1.00 | 8.04 | 0 | 0.32 | 1030 | 1379.08 | 55.32 |
| renovated | typical | setpoint | 2.00 | 8.04 | 0 | 0.15 | 690 | 1633.13 | 51.83 |

## Closed loop with the advice engine (Zurich)

| building | behaviour | policy | compliance | n_advice | days_m_ge_1 | max_mould_idx | hours_rh_surf_ge_80 | heating_kwh | mean_rh_in | airing_min_per_day |
|---|---|---|---|---|---|---|---|---|---|---|
| altbau | bad | none | 0.00 | 0 | 0 | 0.84 | 2000 | 3676.25 | 54.95 | 0.00 |
| altbau | bad | corner | 0.30 | 533 | 0 | 0.10 | 1082 | 4252.33 | 49.32 | 7.86 |
| altbau | bad | corner | 0.70 | 369 | 0 | 0.03 | 772 | 4477.60 | 47.42 | 12.19 |
| altbau | bad | room | 0.30 | 315 | 0 | 0.15 | 1386 | 4082.64 | 50.71 | 4.57 |
| altbau | bad | room | 0.70 | 203 | 0 | 0.04 | 1120 | 4199.83 | 49.56 | 6.52 |
| altbau | typical | none | 0.00 | 0 | 0 | 0.06 | 444 | 4578.66 | 46.00 | 8.04 |
| altbau | typical | corner | 0.30 | 201 | 0 | 0.00 | 166 | 4861.85 | 43.94 | 10.99 |
| altbau | typical | corner | 0.70 | 141 | 0 | 0.01 | 107 | 4929.83 | 43.41 | 12.46 |
| altbau | typical | room | 0.30 | 156 | 0 | 0.01 | 223 | 4731.18 | 44.71 | 10.04 |
| altbau | typical | room | 0.70 | 101 | 0 | 0.01 | 143 | 4806.21 | 44.16 | 11.08 |
| renovated | bad | none | 0.00 | 0 | 154 | 5.28 | 3967 | 565.04 | 82.74 | 0.00 |
| renovated | bad | corner | 0.30 | 828 | 0 | 0.85 | 2163 | 1186.25 | 60.60 | 12.14 |
| renovated | bad | corner | 0.70 | 518 | 0 | 0.17 | 1237 | 1314.08 | 56.01 | 16.81 |
| renovated | bad | room | 0.30 | 874 | 35 | 1.09 | 2195 | 1153.51 | 61.34 | 12.10 |
| renovated | bad | room | 0.70 | 514 | 0 | 0.08 | 1249 | 1316.36 | 56.00 | 17.00 |
| renovated | typical | none | 0.00 | 0 | 0 | 0.59 | 1470 | 1127.30 | 59.05 | 8.04 |
| renovated | typical | corner | 0.30 | 327 | 0 | 0.01 | 298 | 1438.46 | 51.99 | 13.04 |
| renovated | typical | corner | 0.70 | 216 | 0 | 0.00 | 124 | 1493.39 | 50.81 | 14.94 |
| renovated | typical | room | 0.30 | 482 | 0 | 0.03 | 234 | 1506.20 | 50.83 | 14.37 |
| renovated | typical | room | 0.70 | 289 | 0 | 0.00 | 104 | 1627.47 | 48.73 | 17.85 |

## Sensor placement and false alarms (mean over 6 flats x 3 noise seeds)

| setup | hour_precision | hour_recall | false_alarm_per_flat_month | missed_per_flat_month | mean_abs_err_rh_surf | coverage_pct |
|---|---|---|---|---|---|---|
| corner | 0.89 | 0.93 | 0.02 | 0.06 | 3.10 | 98.35 |
| room_generic | 0.90 | 0.74 | 0.14 | 0.47 | 4.26 | 98.35 |
| room_known | 0.88 | 0.92 | 0.03 | 0.12 | 2.49 | 98.35 |
