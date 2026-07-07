from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import get_current_user, get_optional_user
from api.schemas.social import ProfileOut, PublicUserOut
from apps.accounts.models import Follow, User

router = APIRouter()


async def _get_user_or_404(username: str) -> User:
    try:
        return await User.objects.aget(username=username, is_active=True)
    except User.DoesNotExist:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from None


@router.get("/{username}", response_model=ProfileOut)
async def profile(
    username: str, viewer: User | None = Depends(get_optional_user)
) -> ProfileOut:
    user = await _get_user_or_404(username)
    is_following = None
    if viewer is not None and viewer.id != user.id:
        is_following = await Follow.objects.filter(follower=viewer, followee=user).aexists()
    return ProfileOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        role=user.role,
        followers_count=await Follow.objects.filter(followee=user).acount(),
        following_count=await Follow.objects.filter(follower=user).acount(),
        is_following=is_following,
    )


@router.post("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def follow(username: str, viewer: User = Depends(get_current_user)) -> None:
    user = await _get_user_or_404(username)
    if user.id == viewer.id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cannot follow yourself")
    await Follow.objects.aget_or_create(follower=viewer, followee=user)


@router.delete("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow(username: str, viewer: User = Depends(get_current_user)) -> None:
    user = await _get_user_or_404(username)
    await Follow.objects.filter(follower=viewer, followee=user).adelete()


@router.get("/{username}/followers", response_model=list[PublicUserOut])
async def followers(
    username: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[User]:
    user = await _get_user_or_404(username)
    qs = Follow.objects.filter(followee=user).select_related("follower")[offset : offset + limit]
    return [f.follower async for f in qs]


@router.get("/{username}/following", response_model=list[PublicUserOut])
async def following(
    username: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[User]:
    user = await _get_user_or_404(username)
    qs = Follow.objects.filter(follower=user).select_related("followee")[offset : offset + limit]
    return [f.followee async for f in qs]
