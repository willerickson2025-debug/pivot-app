from __future__ import annotations
import asyncio
import logging
from typing import Optional
import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter, before_sleep_log, RetryError
from backend.config import get_settings
from backend.engine.cache import cget, cset, make_key
from backend.models.player import PlayerProfile, TeamProfile
from backend.ai.prompts import SYSTEM, analyze_prompt, compare_prompt, trade_prompt, team_prompt, chat_system

logger = logging.getLogger(__name__)
_sem: Optional[asyncio.Semaphore] = None


def _get_sem() -> asyncio.Semaphore:
    global _sem
    if _sem is None:
        _sem = asyncio.Semaphore(get_settings().max_concurrent_llm_calls)
    return _sem


async def _call(system: str, user: str, cache_key: str, ttl: Optional[int] = None, force: bool = False) -> str:
    s = get_settings()

    if not force:
        cached = cget(cache_key)
        if cached is not None:
            logger.info("LLM cache HIT %s", cache_key)
            return cached

    @retry(
        retry=retry_if_exception_type((
            anthropic.RateLimitError,
            anthropic.InternalServerError,
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
        )),
        stop=stop_after_attempt(s.retry_max_attempts),
        wait=wait_exponential_jitter(initial=s.retry_min_wait_seconds, max=s.retry_max_wait_seconds, jitter=2.0),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _attempt():
        async with _get_sem():
            client = anthropic.AsyncAnthropic(api_key=s.anthropic_api_key)
            return await client.messages.create(
                model=s.claude_model,
                max_tokens=s.claude_max_tokens,
                temperature=s.claude_temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )

    try:
        msg = await _attempt()
    except RetryError:
        return "[ERROR] Claude API unavailable after retries. Try again shortly."
    except anthropic.AuthenticationError:
        return "[ERROR] Invalid API key."
    except Exception as e:
        logger.error("Claude error: %s", e, exc_info=True)
        return f"[ERROR] {e}"

    result = msg.content[0].text if msg.content else ""
    logger.info("Tokens — in:%d out:%d key:%s", msg.usage.input_tokens, msg.usage.output_tokens, cache_key)

    if result and not result.startswith("[ERROR]"):
        cset(cache_key, result, ttl=ttl)

    return result


# ── Public async functions ─────────────────────────────────────────────────

async def ai_analyze(p: PlayerProfile, question: str | None = None, force: bool = False) -> str:
    key = make_key("llm:analyze", pid=p.identity.player_id, season=p.season, q=question or "")
    return await _call(SYSTEM, analyze_prompt(p, question), key, force=force)


async def ai_compare(a: PlayerProfile, b: PlayerProfile, context: str = "", force: bool = False) -> str:
    key = make_key("llm:compare", ids=sorted([a.identity.player_id, b.identity.player_id]), season=a.season, ctx=context)
    return await _call(SYSTEM, compare_prompt(a, b, context), key, force=force)


async def ai_trade(out: list[PlayerProfile], inc: list[PlayerProfile], context: str = "", force: bool = False) -> str:
    key = make_key("llm:trade",
        out=sorted([p.identity.player_id for p in out]),
        inc=sorted([p.identity.player_id for p in inc]),
        ctx=context
    )
    return await _call(SYSTEM, trade_prompt(out, inc, context), key, force=force)


async def ai_team(team: TeamProfile, question: str | None = None, force: bool = False) -> str:
    key = make_key("llm:team", abbr=team.abbreviation, season=team.season, q=question or "")
    return await _call(SYSTEM, team_prompt(team, question), key, force=force)


async def ai_chat(p: PlayerProfile, history: list[dict], message: str) -> tuple[str, list[dict]]:
    s = get_settings()
    updated = history + [{"role": "user", "content": message}]
    try:
        client = anthropic.AsyncAnthropic(api_key=s.anthropic_api_key)
        msg = await client.messages.create(
            model=s.claude_model,
            max_tokens=s.claude_max_tokens,
            temperature=s.claude_temperature,
            system=chat_system(p),
            messages=updated,
        )
        reply = msg.content[0].text if msg.content else "[No response]"
        updated.append({"role": "assistant", "content": reply})
        return reply, updated
    except Exception as e:
        logger.error("Chat error: %s", e)
        return f"[ERROR] {e}", history


async def ai_roster_package(team: TeamProfile, force: bool = False) -> dict[str, str]:
    from backend.ai.prompts import roster_card_prompt

    async def _one(p: PlayerProfile) -> tuple[str, str]:
        key = make_key("llm:rostercard", pid=p.identity.player_id, season=p.season)
        cached = cget(key)
        if cached and not force:
            return p.identity.name, cached
        s = get_settings()
        client = anthropic.AsyncAnthropic(api_key=s.anthropic_api_key)
        msg = await client.messages.create(
            model=s.claude_model,
            max_tokens=400,
            temperature=0.2,
            system=SYSTEM,
            messages=[{"role": "user", "content": roster_card_prompt(p)}],
        )
        result = msg.content[0].text if msg.content else ""
        cset(key, result, ttl=s.cache_ttl_seconds)
        return p.identity.name, result

    results = await asyncio.gather(*[_one(p) for p in team.roster], return_exceptions=True)
    return {name: report for item in results if not isinstance(item, Exception) for name, report in [item]}