from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/magic-link")
def send_magic_link(email: str) -> dict[str, str]:
    # TODO: integrate with Supabase or Clerk. For now we return a fake token.
    return {"status": "sent", "token": "stub-token"}
