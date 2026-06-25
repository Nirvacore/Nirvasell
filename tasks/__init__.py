"""Task registry. Each task module declares a TASK dict so the UI can render
it without hardcoding knowledge about each task.

Built-in tasks are imported here; user-defined tasks merge in at runtime
from custom_tasks.load_for_current_user()."""
from . import (
    listing, line_post, fb_post, tiktok_script, tiktok_live,
    email_blast, bundle, customer_qa, promotion, ad_creative, ai_review,
    review_reply,
)

BUILTIN = {t.TASK["key"]: t for t in [
    listing, line_post, fb_post, tiktok_script, tiktok_live,
    email_blast, bundle, customer_qa, promotion, ad_creative, ai_review,
    review_reply,
]}


from i18n_inline import task_label


def all_tasks() -> dict:
    """Built-in + per-user custom (custom tasks override built-ins on key collision)."""
    out = dict(BUILTIN)
    try:
        import custom_tasks as ct
        out.update(ct.load_for_current_user())
    except Exception:
        pass
    return out


# Backwards-compat: many call sites treat ALL like a plain dict. Provide
# a thin proxy that resolves dynamically each access.
class _DynamicRegistry:
    def __getitem__(self, key):
        return all_tasks()[key]

    def __iter__(self):
        return iter(all_tasks())

    def __contains__(self, key):
        return key in all_tasks()

    def __len__(self):
        return len(all_tasks())

    def items(self):
        return all_tasks().items()

    def keys(self):
        return all_tasks().keys()

    def values(self):
        return all_tasks().values()

    def get(self, key, default=None):
        return all_tasks().get(key, default)


ALL = _DynamicRegistry()


def get(key: str):
    return all_tasks()[key]


def options() -> list[tuple[str, str]]:
    return [(k, f"{m.TASK['icon']} {task_label(k, mod=m)}") for k, m in all_tasks().items()]
