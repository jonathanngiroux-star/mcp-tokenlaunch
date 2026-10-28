# mcp-tokenlaunch

MCP server for **Token Launchpad Support** — token creation, vesting schedules, liquidity
provision, launch coordination, compliance checks, and launch status tracking.

## Tools

### `create_token`
Create a new token with specified parameters.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | **required** | Token name |
| `symbol` | string | **required** | Token symbol |
| `decimals` | integer | 18 | Decimal places |
| `total_supply` | string | **required** | Total supply as string (wei) |
| `chain` | string enum | `ethereum` | ethereum, polygon, arbitrum, optimism, base, solana |
| `features` | array | [] | mintable, burnable, pausable, votes, permit, flash_mint |

Returns token with generated address, creation timestamp, and status.

### `get_token_info`
Get information about a deployed token.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |

### `create_vesting_schedule`
Create a vesting schedule for token distribution.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |
| `beneficiary` | string | **required** | Beneficiary address |
| `start_time` | string | **required** | ISO-8601 start timestamp |
| `cliff_months` | integer | 0 | Cliff period in months |
| `duration_months` | integer | **required** | Total vesting duration in months |
| `total_amount` | string | **required** | Total tokens to vest (wei) |
| `release_frequency` | string enum | `monthly` | monthly, quarterly, linear |

### `get_vesting_schedule`
Get vesting schedule details and current progress.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |
| `beneficiary` | string | - | Beneficiary address; omit for all |

Returns progress percentage, cliff status, and released amount.

### `provision_liquidity`
Provision initial liquidity for a token pair on a DEX.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |
| `pair_token` | string | **required** | Pair token address (e.g., WETH, USDC) |
| `amount_token` | string | **required** | Amount of token to provide (wei) |
| `amount_pair` | string | **required** | Amount of pair token to provide (wei) |
| `dex` | string enum | `uniswap_v2` | uniswap_v2, uniswap_v3, sushiswap, pancakeswap |
| `fee_tier` | integer | 3000 | Fee tier in basis points (Uniswap V3) |

### `get_liquidity_info`
Get liquidity pool information and metrics.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |
| `pair_token` | string | - | Pair token address; omit for all pools |

### `run_compliance_check`
Run regulatory compliance checks for a token launch.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |
| `jurisdiction` | string enum | `global` | US, EU, UK, SG, JP, global |
| `checks` | array | all | sanctions, kyc_aml, securities_law, tax_reporting, consumer_protection |

Returns audit results with per-check status and overall status.

### `get_launch_status`
Get the current status of a token launch readiness.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token_address` | string | **required** | Token contract address |

Returns deploy status, vesting schedules, liquidity pools, compliance status, and launch readiness.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

State persisted in `./state/`. Override with `MCP_TOKENLAUNCH_STATE_DIR`.

## Connecting to an MCP client

```json
{
  "mcpServers": {
    "tokenlaunch": {
      "command": "python3",
      "args": ["/tmp/v3-services/mcp-tokenlaunch/main.py"]
    }
  }
}
```

## License

MIT