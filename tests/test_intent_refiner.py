"""Testes do IntentRefinerAgent."""

from src.agents.intent_refiner import intent_refiner
from src.telemetry import read_events


def _estado(**extra):
    return {"run_id": "no-test", "arm": "B", "task_id": "t", **extra}


def test_intent_refiner_ready(ctx_minimo, sample_intent):
    """Deve retornar intent estruturada quando a solicitação é clara."""
    _, respostas = ctx_minimo
    respostas.append(sample_intent)

    result = intent_refiner(_estado(raw_request="Criar CRUD de Cliente"))

    assert result["is_ready"] is True
    assert result["intent"]["goal"] == "Implementar CRUD de Cliente."
    assert result["clarifications_needed"] == []


def test_intent_refiner_not_ready(ctx_minimo, sample_intent_not_ready):
    """Deve indicar clarificações quando há ambiguidade."""
    _, respostas = ctx_minimo
    respostas.append(sample_intent_not_ready)

    result = intent_refiner(_estado(raw_request="Criar algo"))

    assert result["is_ready"] is False
    assert len(result["clarifications_needed"]) == 2


def test_intent_refiner_increments_iteration(ctx_minimo, sample_intent):
    """Deve incrementar iteration_count após clarificações."""
    _, respostas = ctx_minimo
    respostas.append(sample_intent)

    result = intent_refiner(_estado(
        raw_request="Criar CRUD",
        clarification_responses=[{"question": "Q?", "answer": "A."}],
        iteration_count=1,
    ))

    assert result["iteration_count"] == 2


def test_no_aparece_na_telemetria(ctx_minimo, sample_intent):
    """
    O braço B tem quatro nós além do developer chamando LLM. Se não
    aparecessem na telemetria, o custo dele sairia subestimado.
    """
    ctx, respostas = ctx_minimo
    respostas.append(sample_intent)

    intent_refiner(_estado(raw_request="Criar CRUD"))

    tipos = [e["event_type"] for e in read_events(ctx.telemetry.path)]
    assert tipos == ["node_enter", "node_exit"]
    papeis = {e["agent_role"] for e in read_events(ctx.telemetry.path)}
    assert papeis == {"intent_refiner"}
