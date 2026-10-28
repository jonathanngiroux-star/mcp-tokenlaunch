#!/usr/bin/env python3
"""Tool definitions for mcp-tokenlaunch - Token Launchpad Support."""

from mcp.types import Tool

TOOLS: list = [
    Tool(
        name="create_token",
        description="Create a new token with specified parameters (ERC-20, SPL, etc.).",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Token name."},
                "symbol": {"type": "string", "description": "Token symbol."},
                "decimals": {"type": "integer", "default": 18, "description": "Decimal places."},
                "total_supply": {"type": "string", "description": "Total supply as string (wei)."},
                "chain": {"type": "string", "enum": ["ethereum", "polygon", "arbitrum", "optimism", "base", "solana"], "default": "ethereum"},
                "features": {"type": "array", "items": {"type": "string", "enum": ["mintable", "burnable", "pausable", "votes", "permit", "flash_mint"]}, "default": [], "description": "ERC-20 extensions."},
            },
            "required": ["name", "symbol", "total_supply"],
        },
    ),
    Tool(
        name="get_token_info",
        description="Get information about a deployed token.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
            },
            "required": ["token_address"],
        },
    ),
    Tool(
        name="create_vesting_schedule",
        description="Create a vesting schedule for token distribution.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
                "beneficiary": {"type": "string", "description": "Beneficiary address."},
                "start_time": {"type": "string", "description": "ISO-8601 start timestamp."},
                "cliff_months": {"type": "integer", "default": 0, "description": "Cliff period in months."},
                "duration_months": {"type": "integer", "description": "Total vesting duration in months."},
                "total_amount": {"type": "string", "description": "Total tokens to vest (wei)."},
                "release_frequency": {"type": "string", "enum": ["monthly", "quarterly", "linear"], "default": "monthly"},
            },
            "required": ["token_address", "beneficiary", "start_time", "duration_months", "total_amount"],
        },
    ),
    Tool(
        name="get_vesting_schedule",
        description="Get vesting schedule details and current progress.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
                "beneficiary": {"type": "string", "description": "Beneficiary address; omit for all."},
            },
            "required": ["token_address"],
        },
    ),
    Tool(
        name="provision_liquidity",
        description="Provision initial liquidity for a token pair on a DEX.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
                "pair_token": {"type": "string", "description": "Pair token address (e.g., WETH, USDC)."},
                "amount_token": {"type": "string", "description": "Amount of token to provide (wei)."},
                "amount_pair": {"type": "string", "description": "Amount of pair token to provide (wei)."},
                "dex": {"type": "string", "enum": ["uniswap_v2", "uniswap_v3", "sushiswap", "pancakeswap"], "default": "uniswap_v2"},
                "fee_tier": {"type": "integer", "default": 3000, "description": "Fee tier in basis points (Uniswap V3)."},
            },
            "required": ["token_address", "pair_token", "amount_token", "amount_pair"],
        },
    ),
    Tool(
        name="get_liquidity_info",
        description="Get liquidity pool information and metrics.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
                "pair_token": {"type": "string", "description": "Pair token address; omit for all pools."},
            },
            "required": ["token_address"],
        },
    ),
    Tool(
        name="run_compliance_check",
        description="Run regulatory compliance checks for a token launch.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
                "jurisdiction": {"type": "string", "enum": ["US", "EU", "UK", "SG", "JP", "global"], "default": "global"},
                "checks": {"type": "array", "items": {"type": "string", "enum": ["sanctions", "kyc_aml", "securities_law", "tax_reporting", "consumer_protection"]}, "default": ["sanctions", "kyc_aml", "securities_law", "tax_reporting", "consumer_protection"]},
            },
            "required": ["token_address"],
        },
    ),
    Tool(
        name="get_launch_status",
        description="Get the current status of a token launch.",
        inputSchema={
            "type": "object",
            "properties": {
                "token_address": {"type": "string", "description": "Token contract address."},
            },
            "required": ["token_address"],
        },
    ),
]