from fastapi import APIRouter, Depends, Path
from app.schemas.common import ResponseBase
from app.middleware.auth import get_current_user
from app.services.bond_service import BondService

router = APIRouter(prefix="/bond", tags=["羁绊碎片"])


@router.get("/{role_key}")
def get_bond(
    role_key: str = Path(..., max_length=64, description="角色标识 linxi / gacha_xxx"),
    user_id: int = Depends(get_current_user),
):
    """获取指定角色的羁绊进度（4 个章节状态）"""
    data = BondService.get_bond_status(user_id, role_key)
    return ResponseBase.success(data=data)
