# PetroNexa Reservoir Engineering v1

## Included
- Reservoir property calculations: bulk/net rock volume, pore volume, hydrocarbon pore volume, saturation and permeability inputs.
- Darcy flow: single-phase field-unit rate calculation.
- Radial flow: steady/pseudosteady-style radial oil-rate screening with skin.
- Material balance: Havlena–Ode style calculation using supplied underground withdrawal and expansion terms.
- Productivity Index.
- Vogel IPR.

## API
- `POST /api/v1/reservoir/properties`
- `POST /api/v1/reservoir/darcy`
- `POST /api/v1/reservoir/radial-flow`
- `POST /api/v1/reservoir/material-balance`
- `POST /api/v1/reservoir/ipr/vogel`
- `POST /api/v1/reservoir/productivity-index`

All reservoir endpoints require the same Bearer JWT authentication as the existing engineering endpoints.

## Important engineering note
The material-balance endpoint intentionally accepts expansion terms explicitly rather than hiding a correlation inside the API. This makes assumptions visible and easier to audit. PVT correlations and more detailed reservoir-drive models can be added as a separate PVT/reservoir layer later.
