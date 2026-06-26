"""
Custom rules CRUD API routes.

Preserves all custom rule endpoints from original app.py
with proper HTTP status codes and validation.
"""

from fastapi import APIRouter, HTTPException
from ..models.requests import CustomRuleCreate, CustomRuleUpdate
from ..models.responses import CustomRuleResponse, CustomRulesListResponse
from ..services.rule_service import (
    load_custom_rules, add_custom_rule, toggle_custom_rule,
    delete_custom_rule, update_custom_rule,
)

router = APIRouter(prefix="/custom-rules", tags=["Custom Rules"])


@router.get(
    "",
    response_model=CustomRulesListResponse,
    summary="List all custom rules",
)
async def get_custom_rules():
    """Get all custom rules."""
    rules = load_custom_rules()
    return CustomRulesListResponse(
        status="completed",
        total=len(rules),
        rules=rules,
    )


@router.post(
    "",
    response_model=CustomRuleResponse,
    status_code=201,
    summary="Create a custom rule",
)
async def create_custom_rule(rule: CustomRuleCreate):
    """Create a new custom rule."""
    new_rule = rule.model_dump()
    add_custom_rule(new_rule)
    return CustomRuleResponse(
        status="completed",
        message="Custom rule added successfully.",
        rule=new_rule,
    )


@router.patch(
    "/{rule_index}/toggle",
    response_model=CustomRuleResponse,
    summary="Toggle rule enabled/disabled",
)
async def toggle_rule(rule_index: int):
    """Toggle the enabled status of a custom rule."""
    rules, updated_rule = toggle_custom_rule(rule_index)

    if updated_rule is None:
        raise HTTPException(status_code=404, detail="Invalid rule index.")

    return CustomRuleResponse(
        status="completed",
        message="Custom rule status updated.",
        rule=updated_rule,
    )


@router.put(
    "/{rule_index}",
    response_model=CustomRuleResponse,
    summary="Update a custom rule",
)
async def update_rule(rule_index: int, updates: CustomRuleUpdate):
    """Update an existing custom rule."""
    update_data = updates.model_dump(exclude_unset=True)
    rules, updated_rule = update_custom_rule(rule_index, update_data)

    if updated_rule is None:
        raise HTTPException(status_code=404, detail="Invalid rule index.")

    return CustomRuleResponse(
        status="completed",
        message="Custom rule updated.",
        rule=updated_rule,
    )


@router.delete(
    "/{rule_index}",
    response_model=CustomRuleResponse,
    summary="Delete a custom rule",
)
async def delete_rule(rule_index: int):
    """Delete a custom rule by index."""
    rules, deleted_rule = delete_custom_rule(rule_index)

    if deleted_rule is None:
        raise HTTPException(status_code=404, detail="Invalid rule index.")

    return CustomRuleResponse(
        status="completed",
        message="Custom rule deleted.",
        rule=deleted_rule,
    )
